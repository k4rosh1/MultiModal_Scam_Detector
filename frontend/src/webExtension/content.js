console.log('========================================');
console.log('🔵 Protego Content Script LOADED!');
console.log('📍 URL:', window.location.href);
console.log('========================================');

let scannedPosts = new WeakMap();
let observer = null;
let autoDetectEnabled = true;
let isScanning = false;
let currentPlatform = 'web';
let currentMetadata = {
  platform: 'web'
};
let isExtensionContextValid = true;

// Check if extension context is still valid
function checkExtensionContext() {
  try {
    if (!chrome.runtime?.id) {
      isExtensionContextValid = false;
      return false;
    }
    return true;
  } catch (e) {
    isExtensionContextValid = false;
    return false;
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (!checkExtensionContext()) {
    console.log('⚠️ Extension context invalid, ignoring message');
    sendResponse({ status: 'error', message: 'Extension context invalid' });
    return true;
  }

  console.log('📨 Content script received:', request.action);

  if (request.action === 'ping') {
    sendResponse({ status: 'ready', metadata: currentMetadata });
    return true;
  }

  if (request.action === 'scanPage') {
    console.log('📄 Manual scan requested');
    if (isScanning) {
      sendResponse({ status: 'already_scanning' });
      return true;
    }
    scanAllPostsAsync();
    sendResponse({ status: 'started' });
    return true;
  }

  if (request.action === 'getProfileInfo') {
    console.log('📊 Getting profile info...');
    extractUserMetadata().then(metadata => {
      console.log('📊 Sending metadata:', metadata);
      sendResponse({ profileInfo: metadata });
    });
    return true;
  }

  if (request.action === 'clearHighlights') {
    clearHighlights();
    scannedPosts = new WeakMap();
    sendResponse({ status: 'cleared' });
    return true;
  }

  if (request.type === 'AUTO_DETECT_CHANGED') {
    autoDetectEnabled = request.enabled;
    if (!autoDetectEnabled && observer) {
      observer.disconnect();
      observer = null;
    } else if (autoDetectEnabled && !observer) {
      startObserver();
      setTimeout(() => scanAllPostsAsync(), 500);
    }
    sendResponse({ success: true });
    return true;
  }
});

function detectPlatform() {
  try {
    const url = window.location.href.toLowerCase();
    if (url.includes('facebook.com') || url.includes('fb.com')) return 'facebook';
    if (url.includes('twitter.com') || url.includes('x.com')) return 'twitter';
    return 'web';
  } catch (e) {
    return 'web';
  }
}

async function extractUserMetadata() {
  const platform = detectPlatform();
  const metadata = {
    platform: platform
  };
  
  console.log(`🔍 Extracting metadata for ${platform}...`);
  
  currentMetadata = metadata;
  console.log('📊 Final metadata:', metadata);
  return metadata;
}

function getFacebookPosts() {
  const posts = [];
  try {
    // Try multiple selectors for Facebook posts
    const selectors = [
      '[data-testid="post_message"]',
      '[role="article"]',
      '[data-testid="feed_story"]',
      '[data-testid="post_content"]',
      '.userContent',
      '.postContent',
      '.story_body_container'
    ];
    
    let postElements = [];
    for (const selector of selectors) {
      const els = document.querySelectorAll(selector);
      if (els.length > 0) {
        postElements = [...postElements, ...els];
      }
    }
    
    // Remove duplicates
    postElements = [...new Set(postElements)];
    
    console.log(`📝 Found ${postElements.length} potential Facebook posts`);
    
    let count = 0;
    for (const el of postElements) {
      if (count >= 15) break;
      if (scannedPosts.has(el)) continue;
      if (el.closest('[role="comment"]')) continue;
      if (el.closest('[aria-label="Chats"]')) continue;
      
      // Check if it's a sponsored/ad post
      const isAd = el.querySelector('[aria-label="Sponsored"]') || 
                   el.innerText?.includes('Sponsored') ||
                   el.innerText?.includes('Ad');
      if (isAd) continue;
      
      let text = extractPostText(el);
      if (text && text.length > 10) {
        console.log(`📝 Facebook post found: "${text.substring(0, 50)}..."`);
        posts.push({ element: el, text: text });
        count++;
      }
    }
  } catch (e) {
    console.error('Error getting Facebook posts:', e);
  }
  return posts;
}

function getTwitterPosts() {
  const posts = [];
  try {
    const selectors = [
      '[data-testid="tweetText"]',
      '[data-testid="tweet"]',
      'article[data-testid="tweet"]',
      'div[data-testid="cellInnerDiv"]'
    ];
    
    let tweetElements = [];
    for (const selector of selectors) {
      const els = document.querySelectorAll(selector);
      if (els.length > 0) {
        tweetElements = [...tweetElements, ...els];
      }
    }
    
    tweetElements = [...new Set(tweetElements)];
    
    console.log(`📝 Found ${tweetElements.length} potential tweets`);
    
    let count = 0;
    for (const el of tweetElements) {
      if (count >= 15) break;
      if (scannedPosts.has(el)) continue;
      
      const isAd = el.innerText?.includes('Ad') || el.innerText?.includes('Promoted');
      if (isAd) continue;
      
      let text = extractPostText(el);
      if (text && text.length > 10) {
        console.log(`📝 Twitter post found: "${text.substring(0, 50)}..."`);
        posts.push({ element: el, text: text });
        count++;
      }
    }
  } catch (e) {
    console.error('Error getting Twitter posts:', e);
  }
  return posts;
}

function extractPostText(element) {
  try {
    let text = element.textContent?.trim() || '';
    
    if (!text || text.length < 5) return '';
    
    // Check if it's mostly just a URL
    const urlMatch = text.match(/https?:\/\/[^\s]+/g);
    if (urlMatch) {
      const urlLength = urlMatch.join(' ').length;
      const textWithoutUrls = text.replace(/https?:\/\/[^\s]+/g, '').trim();
      if (urlLength / text.length > 0.7 && textWithoutUrls.length < 20) {
        return textWithoutUrls || text;
      }
    }
    
    return text;
  } catch (e) {
    return '';
  }
}

async function scanAllPostsAsync() {
  if (!checkExtensionContext()) {
    console.log('⚠️ Extension context invalid, stopping scan');
    isScanning = false;
    return;
  }

  if (isScanning) {
    console.log('Already scanning, skipping');
    return;
  }
  
  isScanning = true;
  
  try {
    const platform = detectPlatform();
    if (platform === 'web') {
      console.log('Not a supported platform');
      isScanning = false;
      return;
    }
    
    console.log(`🔍 Scanning ${platform} for posts...`);
    
    await extractUserMetadata();
    
    let posts = [];
    if (platform === 'facebook') {
      posts = getFacebookPosts();
    } else if (platform === 'twitter') {
      posts = getTwitterPosts();
    }
    
    const newPosts = posts.filter(p => !scannedPosts.has(p.element));
    
    if (newPosts.length === 0) {
      console.log('No new posts found');
      try {
        await chrome.runtime.sendMessage({ action: 'scanComplete', count: 0 });
      } catch (e) {
        console.log('Could not send message, extension may be reloaded');
      }
      isScanning = false;
      return;
    }
    
    console.log(`📊 Found ${newPosts.length} new posts to analyze`);
    try {
      await chrome.runtime.sendMessage({ action: 'scanProgress', total: newPosts.length, current: 0 });
    } catch (e) {
      console.log('Could not send message, extension may be reloaded');
    }
    
    let completed = 0;
    for (const post of newPosts) {
      if (!checkExtensionContext()) {
        console.log('⚠️ Extension context invalid, stopping scan');
        break;
      }
      
      await analyzePost(post.text, post.element);
      completed++;
      
      if (completed % 3 === 0 || completed === newPosts.length) {
        try {
          await chrome.runtime.sendMessage({ action: 'scanProgress', total: newPosts.length, current: completed });
        } catch (e) {
          console.log('Could not send message, extension may be reloaded');
        }
        console.log(`📊 Progress: ${completed}/${newPosts.length} posts analyzed`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    console.log(`✅ Scan complete: ${completed} posts analyzed`);
    try {
      await chrome.runtime.sendMessage({ action: 'scanComplete', count: completed });
    } catch (e) {
      console.log('Could not send message, extension may be reloaded');
    }
    
  } catch (error) {
    console.error('Scan error:', error);
  } finally {
    isScanning = false;
  }
}

async function analyzePost(text, element) {
  if (!autoDetectEnabled) return;
  
  if (!checkExtensionContext()) {
    console.log('⚠️ Extension context invalid, skipping analysis');
    return;
  }
  
  const platform = detectPlatform();
  
  console.log(`🔍 Analyzing post: "${text.substring(0, 50)}..."`);
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'detectText',
      text: text,
      url: window.location.href,
      platform: platform,
      type: 'post'
    });
    
    if (response && !response.error) {
      scannedPosts.set(element, response);
      console.log(`✅ Result: ${response.verdict} (${response.confidence})`);
      
      if (response.verdict === 'SCAM') {
        console.log('🚨 SCAM DETECTED! Highlighting post...');
        highlightPost(element, response, text);
      } else {
        console.log('✅ Post is legitimate, not highlighting');
      }
    } else {
      console.log('⚠️ No response or error from API:', response);
    }
  } catch (error) {
    console.error('Error analyzing post:', error);
  }
}

function highlightPost(element, result, text) {
  console.log('🎨 Highlighting scam post...');
  
  try {
    // Apply outline
    element.style.outline = '3px solid #f05252';
    element.style.outlineOffset = '2px';
    element.style.backgroundColor = 'rgba(240, 82, 82, 0.08)';
    element.style.borderRadius = '4px';
    
    console.log('✅ Applied outline and background styles');
    
    // Check if badge already exists
    if (element.querySelector('.protego-badge')) {
      console.log('⚠️ Badge already exists, skipping');
      return;
    }
    
    // Create badge
    const badge = document.createElement('span');
    badge.className = 'protego-badge';
    badge.textContent = '⚠️ SCAM';
    badge.style.cssText = `
      display: inline-block !important;
      background: #f05252 !important;
      color: white !important;
      font-size: 11px !important;
      padding: 3px 10px !important;
      border-radius: 4px !important;
      margin-left: 8px !important;
      cursor: pointer !important;
      font-weight: bold !important;
      z-index: 9999 !important;
      position: relative !important;
    `;
    badge.onclick = (e) => {
      e.stopPropagation();
      alert(`⚠️ SCAM DETECTED!\n\nConfidence: ${result.confidence}\n\nText: ${text.substring(0, 200)}`);
    };
    
    // Try to prepend to the element
    try {
      element.prepend(badge);
      console.log('✅ Badge added to element');
    } catch (e) {
      // If prepend fails, try to add it differently
      console.log('⚠️ Prepend failed, trying alternative method');
      const wrapper = document.createElement('div');
      wrapper.style.display = 'inline';
      wrapper.appendChild(badge);
      element.parentNode?.insertBefore(wrapper, element);
      console.log('✅ Badge added using alternative method');
    }
    
    // Also add a subtle indicator to the element itself
    element.setAttribute('data-protego-scam', 'true');
    
    console.log('✅ Highlight complete!');
    
  } catch (error) {
    console.error('Error highlighting post:', error);
  }
}

function clearHighlights() {
  console.log('🧹 Clearing all highlights...');
  
  try {
    // Remove badges
    const badges = document.querySelectorAll('.protego-badge');
    console.log(`Found ${badges.length} badges to remove`);
    badges.forEach(b => {
      try { b.remove(); } catch(e) {}
    });
    
    // Remove styling from elements
    const elements = document.querySelectorAll('[style*="outline"]');
    console.log(`Found ${elements.length} elements with outline to clear`);
    elements.forEach(el => {
      try {
        el.style.outline = '';
        el.style.outlineOffset = '';
        el.style.backgroundColor = '';
        el.style.borderRadius = '';
        el.removeAttribute('data-protego-scam');
      } catch(e) {}
    });
    
    console.log('✅ Highlights cleared');
  } catch (e) {
    console.error('Error clearing highlights:', e);
  }
}

function startObserver() {
  if (observer) return;
  try {
    observer = new MutationObserver(() => {
      if (!autoDetectEnabled) return;
      clearTimeout(window._scanTimer);
      window._scanTimer = setTimeout(() => {
        if (autoDetectEnabled) {
          scanAllPostsAsync();
        }
      }, 1500);
    });
    observer.observe(document.body, { childList: true, subtree: true });
    console.log('👁 Observer started');
  } catch (e) {
    console.error('Error starting observer:', e);
  }
}

async function init() {
  try {
    const stored = await chrome.storage.local.get(['autoDetectEnabled']);
    autoDetectEnabled = stored.autoDetectEnabled !== false;
    currentPlatform = detectPlatform();
    
    console.log(`Platform: ${currentPlatform} | Auto-detect: ${autoDetectEnabled}`);
    
    await extractUserMetadata();
    
    if (autoDetectEnabled && currentPlatform !== 'web') {
      console.log('🚀 Starting initial scan in 3 seconds...');
      setTimeout(() => scanAllPostsAsync(), 3000);
      startObserver();
    }
  } catch (e) {
    console.error('Error initializing content script:', e);
  }
}

init();