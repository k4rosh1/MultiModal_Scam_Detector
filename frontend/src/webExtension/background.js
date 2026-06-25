const API_URL = 'http://localhost:8000';

const DEFAULT_SETTINGS = {
  autoDetectEnabled: true,
  highlightScams: true,
  showNotifications: true,
  scanSocialMedia: true,
  scanQR: true,
  confidenceThreshold: 50
};

let autoDetectEnabled = true;

async function saveToHistory(detectionResult) {
  try {
    const result = await chrome.storage.local.get(['detectionHistory']);
    let history = result.detectionHistory || [];
    
    history.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      text: detectionResult.text || 'No text',
      verdict: detectionResult.verdict,
      confidence: detectionResult.confidence,
      scam_prob: detectionResult.scam_prob,
      legit_prob: detectionResult.legit_prob,
      platform: detectionResult.platform,
      url: detectionResult.url || '',
      type: detectionResult.type || 'post'
    });
    
    if (history.length > 100) {
      history = history.slice(0, 100);
    }
    
    await chrome.storage.local.set({ detectionHistory: history });
    console.log('✅ Saved to history:', detectionResult.verdict, detectionResult.platform);
    return true;
  } catch (error) {
    console.error('Error saving to history:', error);
    return false;
  }
}

async function getHistory() {
  try {
    const result = await chrome.storage.local.get(['detectionHistory']);
    return result.detectionHistory || [];
  } catch (error) {
    return [];
  }
}

async function clearHistory() {
  try {
    await chrome.storage.local.set({ detectionHistory: [] });
    return true;
  } catch (error) {
    return false;
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  console.log('ScamShield Extension Installed');
  
  const settings = await chrome.storage.local.get(DEFAULT_SETTINGS);
  if (Object.keys(settings).length === 0 || settings.autoDetectEnabled === undefined) {
    await chrome.storage.local.set(DEFAULT_SETTINGS);
    autoDetectEnabled = DEFAULT_SETTINGS.autoDetectEnabled;
  } else {
    autoDetectEnabled = settings.autoDetectEnabled !== false;
  }
  
  const history = await chrome.storage.local.get(['detectionHistory']);
  if (!history.detectionHistory) {
    await chrome.storage.local.set({ detectionHistory: [] });
  }
  
  console.log('Background service worker initialized, auto-detect:', autoDetectEnabled);
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received:', request.action);
  
  if (request.type === 'AUTO_DETECT_TOGGLED') {
    autoDetectEnabled = request.enabled;
    chrome.storage.local.set({ autoDetectEnabled: autoDetectEnabled });
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'getHistory') {
    getHistory().then(history => sendResponse({ history: history }));
    return true;
  }
  
  if (request.action === 'clearHistory') {
    clearHistory().then(success => sendResponse({ success: success }));
    return true;
  }
  
  if (request.action === 'detectText') {
    console.log('📡 Detecting text, length:', request.text?.length);
    
    if (request.manual !== true && !autoDetectEnabled) {
      sendResponse({ verdict: 'SKIPPED', message: 'Auto-detection is disabled' });
      return true;
    }
    
    const platform = request.platform || 'web';
    
    detectScam(request.text, request.url, platform, request.type || 'post')
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message, verdict: 'ERROR' }));
    return true;
  }
  
  // NEW: QR Code detection handler
  if (request.action === 'detectQR') {
    console.log('📱 Detecting QR code data:', request.qrData);
    
    analyzeQRData(request.qrData, request.url, request.platform)
      .then(result => {
        // Save to history
        saveToHistory({
          text: request.qrData || 'QR Code',
          verdict: result.verdict,
          confidence: result.confidence,
          scam_prob: result.scam_prob || 0,
          legit_prob: result.legit_prob || 0,
          platform: 'qr',
          url: request.url || 'unknown',
          type: 'qr'
        });
        sendResponse(result);
      })
      .catch(error => {
        console.error('QR detection error:', error);
        sendResponse({ 
          verdict: 'ERROR', 
          confidence: 0, 
          error: error.message,
          type: 'qr'
        });
      });
    return true;
  }
  
  // NEW: QR scan complete handler
  if (request.action === 'qrScanComplete') {
    console.log('QR Scan Complete:', request);
    updateBadgeWithQRStatus(request);
    sendResponse({ status: 'ok' });
    return true;
  }
  
  if (request.action === 'getStats') {
    getStats().then(stats => sendResponse(stats));
    return true;
  }
  
  if (request.action === 'getSettings') {
    getSettings().then(settings => sendResponse(settings));
    return true;
  }
  
  if (request.action === 'updateSettings') {
    updateSettings(request.settings).then(() => sendResponse({ success: true }));
    return true;
  }
});

// NEW: QR Code Analysis Function
async function analyzeQRData(qrData, pageUrl, platform = 'web') {
  try {
    console.log('🔍 Analyzing QR data:', qrData);
    
    // If QR data is empty or null
    if (!qrData) {
      return {
        verdict: 'UNKNOWN',
        confidence: 0,
        details: 'Empty QR code data',
        type: 'qr'
      };
    }
    
    // Check if QR data contains URLs
    const urlRegex = /https?:\/\/[^\s]+/g;
    const urls = qrData.match(urlRegex);
    
    // Analyze URLs found in QR
    if (urls && urls.length > 0) {
      console.log(`📊 Found ${urls.length} URLs in QR code`);
      
      for (const url of urls) {
        // First, check URL against known scam patterns
        const quickCheck = quickQRUrlCheck(url);
        if (quickCheck.verdict === 'SCAM') {
          return {
            verdict: 'SCAM',
            confidence: 0.85,
            details: `QR code contains suspicious URL: ${url}`,
            url: url,
            scam_prob: 0.85,
            legit_prob: 0.15,
            type: 'qr'
          };
        }
        
        // If URL passes quick check, do deeper analysis
        if (qrData.length > 10) {
          try {
            const response = await detectScam(qrData, url, 'qr', 'qr');
            if (response.verdict === 'SCAM') {
              return {
                verdict: 'SCAM',
                confidence: response.confidence || 0.8,
                details: `QR code links to suspicious content: ${url}`,
                url: url,
                scam_prob: response.scam_prob || 0.8,
                legit_prob: response.legit_prob || 0.2,
                type: 'qr'
              };
            }
          } catch (error) {
            console.error('Error analyzing QR URL with API:', error);
          }
        }
      }
    }
    
    // Check for suspicious patterns in QR data
    const suspiciousPatterns = {
      'login': 0.3,
      'verify': 0.4,
      'update': 0.3,
      'confirm': 0.3,
      'secure': 0.2,
      'account': 0.3,
      'bank': 0.5,
      'paypal': 0.5,
      'apple': 0.3,
      'microsoft': 0.3,
      'google': 0.2,
      'facebook': 0.3,
      'instagram': 0.3,
      'bitcoin': 0.6,
      'crypto': 0.5,
      'wallet': 0.4,
      'investment': 0.5,
      'urgent': 0.6,
      'immediate': 0.5,
      'suspend': 0.5,
      'deactivate': 0.5,
      'limited': 0.4,
      'offer': 0.3,
      'free': 0.2,
      'prize': 0.4,
      'winner': 0.4,
      'congratulation': 0.5
    };
    
    let maxScore = 0;
    const lowerData = qrData.toLowerCase();
    
    for (const [pattern, score] of Object.entries(suspiciousPatterns)) {
      if (lowerData.includes(pattern)) {
        maxScore = Math.max(maxScore, score);
        console.log(`⚠️ Found suspicious pattern: "${pattern}" (score: ${score})`);
      }
    }
    
    // Check for URL shorteners
    const shorteners = ['bit.ly', 'tinyurl', 'goo.gl', 'shorturl', 'ow.ly', 'is.gd', 'buff.ly'];
    if (qrData.includes('http')) {
      for (const shortener of shorteners) {
        if (lowerData.includes(shortener)) {
          maxScore = Math.max(maxScore, 0.5);
          console.log(`⚠️ Found URL shortener: ${shortener}`);
        }
      }
    }
    
    // Check for unusual characters or encoding
    const unusualChars = (qrData.match(/[^a-zA-Z0-9\-_.~:/?#\[\]@!$&'()*+,;=]/g) || []).length;
    if (unusualChars > 5) {
      maxScore = Math.max(maxScore, 0.3);
      console.log(`⚠️ Found ${unusualChars} unusual characters`);
    }
    
    // Determine verdict based on score
    let verdict, confidence, details;
    
    if (maxScore >= 0.5) {
      verdict = 'SCAM';
      confidence = maxScore;
      details = `QR code contains suspicious content (${Math.round(maxScore * 100)}% confidence)`;
    } else if (maxScore >= 0.3) {
      verdict = 'SUSPICIOUS';
      confidence = maxScore;
      details = `QR code has some suspicious indicators (${Math.round(maxScore * 100)}% confidence)`;
    } else {
      verdict = 'SAFE';
      confidence = 0.9 - maxScore;
      details = 'QR code appears safe';
    }
    
    // If we have URLs and no scams detected, mark as safe
    if (urls && urls.length > 0 && verdict !== 'SCAM') {
      verdict = 'SAFE';
      confidence = 0.7;
      details = `QR code contains ${urls.length} URL(s) - no scam detected`;
    }
    
    return {
      verdict: verdict,
      confidence: confidence,
      details: details,
      type: 'qr',
      scam_prob: verdict === 'SCAM' ? confidence : 1 - confidence,
      legit_prob: verdict === 'SAFE' ? confidence : 1 - confidence,
      data: qrData.substring(0, 200)
    };
    
  } catch (error) {
    console.error('Error analyzing QR data:', error);
    return {
      verdict: 'ERROR',
      confidence: 0,
      details: 'Error analyzing QR code',
      type: 'qr',
      error: error.message
    };
  }
}

// NEW: Quick QR URL Check
function quickQRUrlCheck(url) {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    
    // Check for suspicious domains
    const suspiciousDomains = [
      'login-secure', 'verify-account', 'security-update', 
      'bank-verify', 'paypal-secure', 'apple-id', 'microsoft-verify',
      'login-security', 'account-verify', 'secure-login'
    ];
    
    for (const domain of suspiciousDomains) {
      if (hostname.includes(domain)) {
        return { verdict: 'SCAM', confidence: 0.8, reason: 'Suspicious domain pattern' };
      }
    }
    
    // Check for IP address instead of domain
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname)) {
      return { verdict: 'SCAM', confidence: 0.7, reason: 'IP address used instead of domain' };
    }
    
    // Check for excessive subdomains
    const subdomains = hostname.split('.').length;
    if (subdomains > 4) {
      return { verdict: 'SUSPICIOUS', confidence: 0.5, reason: 'Excessive subdomains' };
    }
    
    return { verdict: 'SAFE', confidence: 0.9 };
    
  } catch (error) {
    return { verdict: 'UNKNOWN', confidence: 0.5, reason: 'Invalid URL' };
  }
}

// NEW: Update badge with QR status
function updateBadgeWithQRStatus(data) {
  try {
    if (data && data.success === false) {
      chrome.action.setBadgeText({ text: '!QR' });
      chrome.action.setBadgeBackgroundColor({ color: '#ff9800' });
      return;
    }
    
    // Check if we have any scam QR detections in history
    getHistory().then(history => {
      const recentScams = history.filter(item => 
        item.type === 'qr' && 
        item.verdict === 'SCAM' &&
        (Date.now() - new Date(item.timestamp).getTime()) < 3600000 // Last hour
      );
      
      if (recentScams.length > 0) {
        chrome.action.setBadgeText({ text: '⚠QR' });
        chrome.action.setBadgeBackgroundColor({ color: '#ff0000' });
      } else {
        // Check if we have any QR detections at all
        const qrDetections = history.filter(item => item.type === 'qr');
        if (qrDetections.length > 0) {
          chrome.action.setBadgeText({ text: 'QR' });
          chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
        } else {
          chrome.action.setBadgeText({ text: '' });
        }
      }
    }).catch(() => {
      // If error, just show QR
      chrome.action.setBadgeText({ text: 'QR' });
      chrome.action.setBadgeBackgroundColor({ color: '#2196F3' });
    });
  } catch (error) {
    console.error('Error updating badge:', error);
  }
}

async function detectScam(text, url, platform = 'web', type = 'post') {
  if (!autoDetectEnabled && type !== 'manual') {
    return { verdict: 'SKIPPED', confidence: 0 };
  }
  
  if (!text || text.length === 0) {
    return { verdict: 'ERROR', confidence: 0, error: 'empty_text' };
  }
  
  try {
    console.log(`📤 Calling API for ${platform}...`);
    const response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text.substring(0, 1000),
        platform: platform,
        account_age: 365,
        posting_frequency: 1,
        url: url || null
      })
    });
    
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    
    const data = await response.json();
    console.log(`🎯 API Result: ${data.verdict} (${data.confidence})`);
    
    await saveToHistory({
      text: text,
      verdict: data.verdict,
      confidence: data.confidence,
      scam_prob: data.scam_prob,
      legit_prob: data.legit_prob,
      platform: platform,
      url: url || 'unknown',
      type: type
    });
    
    return data;
  } catch (error) {
    console.error('Detection error:', error);
    return { error: error.message, verdict: 'ERROR', confidence: 0 };
  }
}

async function getStats() {
  try {
    const response = await fetch(`${API_URL}/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
  } catch (error) {
    return { total_detections: 0, scam_count: 0, scam_rate: '0%', mock_mode: true };
  }
}

async function getSettings() {
  const settings = await chrome.storage.local.get(DEFAULT_SETTINGS);
  return {
    autoDetectEnabled: settings.autoDetectEnabled !== false,
    highlightScams: settings.highlightScams !== false,
    showNotifications: settings.showNotifications !== false,
    scanSocialMedia: settings.scanSocialMedia !== false,
    scanQR: settings.scanQR !== false,
    confidenceThreshold: settings.confidenceThreshold || 50
  };
}

async function updateSettings(newSettings) {
  const currentSettings = await chrome.storage.local.get(DEFAULT_SETTINGS);
  const updatedSettings = { ...currentSettings, ...newSettings };
  await chrome.storage.local.set(updatedSettings);
  
  if (newSettings.autoDetectEnabled !== undefined) {
    autoDetectEnabled = newSettings.autoDetectEnabled;
  }
}

console.log('ScamShield background service worker started');