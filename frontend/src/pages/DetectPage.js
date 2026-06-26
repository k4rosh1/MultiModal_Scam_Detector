import React, { useState, useEffect, useRef } from "react";
import { predict, checkHealth } from "../api";
import "./DetectPage.css";

const DEFAULT_META = {
  platform: "facebook",
  account_age: 365,
  posting_frequency: 1.0,
};

// Converts a date string to number of days from that date until today
function dateToDays(dateStr) {
  if (!dateStr) return 0;
  const joined = new Date(dateStr);
  const today = new Date();
  const diff = Math.floor((today - joined) / (1000 * 60 * 60 * 24));
  return diff < 0 ? 0 : diff;
}

// Converts number of days back to a date string for the date picker display
function daysToDate(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}

function NumberField({ label, name, value, onChange, hint, min, max, step }) {
  return (
    <div className="field-row">
      <div className="field-label-wrap">
        <label className="field-label">{label}</label>
        {hint && <span className="field-hint">{hint}</span>}
      </div>
      <input
        type="number"
        name={name}
        value={value}
        onChange={onChange}
        min={min}
        max={max}
        step={step || 1}
        className="field-input"
      />
    </div>
  );
}

function ResultCard({ result }) {
  const isScam = result.label === 1;
  const scamW = result.scam_prob || "0%";
  const legitW = result.legit_prob || "0%";

  return (
    <div className={`result-card ${isScam ? "result-scam" : "result-legit"}`}>
      {result.is_mock && (
        <div className="mock-banner">
          🟡 Mock Mode — predictions are simulated
        </div>
      )}
      {result.is_duplicate && (
        <div className="duplicate-banner">
          ⚡ Cached result — this post was scanned before. No duplicate saved to database.
        </div>
      )}
      {result.error && (
        <div className="error-banner">
          ❌ {result.error}
        </div>
      )}
      <div className="result-header">
        <div className={`result-icon ${isScam ? "icon-scam" : "icon-legit"}`}>
          {isScam ? "🚨" : "✅"}
        </div>
        <div>
          <div className="result-verdict">
            {result.verdict || (isScam ? "Scam Detected" : "Looks Legitimate")}
          </div>
          <div className="result-platform">
            {result.type === "qr" ? "📱 QR Code" : 
             result.platform === "facebook" ? "📘 Facebook" : "🐦 X (Twitter)"}
          </div>
        </div>
        <span className={`tag ${isScam ? "tag-scam" : "tag-legit"}`}>
          {isScam ? "SCAM" : "LEGIT"}
        </span>
      </div>

      <div className="result-bars">
        <div className="prob-row">
          <span className="prob-label">Scam probability</span>
          <div className="prob-bar-wrap">
            <div className="prob-bar">
              <div
                className="prob-fill prob-fill-scam"
                style={{ width: typeof scamW === 'string' ? scamW.replace('%', '') : scamW }}
              />
            </div>
            <span className="prob-value" style={{ color: "var(--danger)" }}>
              {scamW}
            </span>
          </div>
        </div>
        <div className="prob-row">
          <span className="prob-label">Legit probability</span>
          <div className="prob-bar-wrap">
            <div className="prob-bar">
              <div
                className="prob-fill prob-fill-legit"
                style={{ width: typeof legitW === 'string' ? legitW.replace('%', '') : legitW }}
              />
            </div>
            <span className="prob-value" style={{ color: "var(--safe)" }}>
              {legitW}
            </span>
          </div>
        </div>
      </div>

      <div className="result-conf">
        <span className="conf-label">Model confidence</span>
        <span className="conf-value">{result.confidence || "0%"}</span>
      </div>
      
      {result.type === "qr" && result.qr_data && (
        <div className="qr-result-details">
          <div className="qr-detail-header">📱 QR Code Details</div>
          <div className="qr-detail-row">
            <span className="qr-detail-label">Decoded Data:</span>
            <span className="qr-detail-value">{result.qr_data}</span>
          </div>
          {result.qr_urls && result.qr_urls.length > 0 && (
            <div className="qr-detail-row">
              <span className="qr-detail-label">URLs Found:</span>
              <span className="qr-detail-value">
                {result.qr_urls.map((url, i) => (
                  <div key={i} className="qr-url-item">{url}</div>
                ))}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DetectPage() {
  const [text, setText] = useState("");
  const [meta, setMeta] = useState(DEFAULT_META);
  const [joinedDate, setJoinedDate] = useState(
    daysToDate(DEFAULT_META.account_age),
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(null);
  const [tab, setTab] = useState("text");
  
  // QR Code states - removed unused qrImage
  const [qrPreview, setQrPreview] = useState(null);
  const [qrData, setQrData] = useState("");
  const [isQrLoading, setIsQrLoading] = useState(false);
  const [qrResult, setQrResult] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkHealth().then((ok) => setOnline(ok));
  }, []);

  // When user picks a date → auto-calculate days and update meta
  const handleDateChange = (e) => {
    const dateStr = e.target.value;
    setJoinedDate(dateStr);
    const days = dateToDays(dateStr);
    setMeta((prev) => ({ ...prev, account_age: days }));
  };

  const handleMeta = (e) => {
    const { name, value } = e.target;
    setMeta((prev) => ({ ...prev, [name]: parseFloat(value) ?? value }));
  };

  const handleSubmit = async () => {
    if (!text.trim()) {
      setError("Please enter a post caption.");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const res = await predict({ text: text.trim(), ...meta });
      setResult(res);
    } catch {
      setError(
        "Cannot reach API. Make sure the server is running at http://localhost:8000",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setText("");
    setMeta(DEFAULT_META);
    setJoinedDate(daysToDate(DEFAULT_META.account_age));
    setResult(null);
    setQrResult(null);
    setError("");
    setTab("text");
    setQrPreview(null);
    setQrData("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // QR Code handlers
  const handleQrUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file (PNG, JPG, JPEG, etc.)");
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError("Image file is too large. Please upload an image under 5MB.");
      return;
    }

    setQrPreview(URL.createObjectURL(file));
    setError("");
    setQrResult(null);
    setResult(null);
    
    // Auto-detect QR code
    await detectQRCode(file);
  };

  const detectQRCode = async (file) => {
    setIsQrLoading(true);
    setError("");
    setQrData("");
    
    try {
      // Convert image to base64
      const base64 = await imageToBase64(file);
      
      // Send to API for QR detection
      const response = await fetch("http://localhost:8000/detect-qr", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          image: base64,
          platform: meta.platform,
          account_age: meta.account_age,
          posting_frequency: meta.posting_frequency
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `QR detection failed: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("QR Detection Response:", data);
      
      // Check if there was an error in the response
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Set QR data
      const decodedData = data.qr_data || "No data decoded";
      setQrData(decodedData);
      
      // Set QR result
      setQrResult({
        label: data.verdict === "SCAM" ? 1 : 0,
        verdict: data.verdict || "UNKNOWN",
        scam_prob: data.scam_prob || "0%",
        legit_prob: data.legit_prob || "0%",
        confidence: data.confidence || "0%",
        platform: meta.platform,
        type: "qr",
        qr_data: decodedData,
        qr_urls: data.qr_urls || [],
        is_mock: data.is_mock || false,
        is_duplicate: data.is_duplicate || false,
        error: data.error || null
      });
      
    } catch (error) {
      console.error("QR detection error:", error);
      setError(`QR detection failed: ${error.message}`);
      setQrData("Error decoding QR code");
      setQrResult({
        label: 0,
        verdict: "ERROR",
        scam_prob: "0%",
        legit_prob: "0%",
        confidence: "0%",
        platform: meta.platform,
        type: "qr",
        qr_data: "Error decoding QR code",
        qr_urls: [],
        error: error.message
      });
    } finally {
      setIsQrLoading(false);
    }
  };

  const imageToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Get the base64 string without the data URL prefix
        const base64 = reader.result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      handleQrUpload({ target: { files: [file] } });
    }
  };

  const fillScamSample = () => {
    setText(
      "GRABE! Kumita ako ng 50000 pesos sa loob ng 7 araw! DM mo ko para malaman kung paano! 💰🔥 bit.ly/abc123",
    );
    const age = 30;
    setMeta((prev) => ({ ...prev, account_age: age, posting_frequency: 15.0 }));
    setJoinedDate(daysToDate(age));
    setTab("meta");
    setTimeout(() => setTab("text"), 1500);
  };

  const fillLegitSample = () => {
    setText(
      "Kumain kami ni Maria sa Jollibee kanina. Masarap pa rin ang Chickenjoy! Highly recommend 😄",
    );
    const age = 800;
    setMeta((prev) => ({ ...prev, account_age: age, posting_frequency: 1.2 }));
    setJoinedDate(daysToDate(age));
    setTab("meta");
    setTimeout(() => setTab("text"), 1500);
  };

  // Today's date as max for the date picker (can't join in the future)
  const today = new Date().toISOString().split("T")[0];

  // Determine which result to show
  const displayResult = tab === "qr" ? qrResult : result;

  return (
    <div className="detect-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Scam Detector</h1>
          <p className="page-sub">
            Enter a post caption or upload a QR code to get a scam verdict.
          </p>
        </div>
        {online === false && (
          <div className="offline-banner">
            ⚠️ API is offline — start the FastAPI server first
          </div>
        )}
      </div>

      <div className="detect-grid">
        {/* LEFT — Input */}
        <div className="input-panel">
          {/* Platform */}
          <div className="platform-selector">
            <button
              className={`plat-btn ${meta.platform === "facebook" ? "plat-active" : ""}`}
              onClick={() => setMeta((p) => ({ ...p, platform: "facebook" }))}
            >
              📘 Facebook
            </button>
            <button
              className={`plat-btn ${meta.platform === "twitter" ? "plat-active" : ""}`}
              onClick={() => setMeta((p) => ({ ...p, platform: "twitter" }))}
            >
              🐦 X (Twitter)
            </button>
          </div>

          {/* Tabs */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${tab === "text" ? "tab-active" : ""}`}
              onClick={() => setTab("text")}
            >
              ✏️ Post Caption
            </button>
            <button
              className={`tab-btn ${tab === "meta" ? "tab-active" : ""}`}
              onClick={() => setTab("meta")}
            >
              👤 Account Metadata
            </button>
            <button
              className={`tab-btn ${tab === "qr" ? "tab-active" : ""}`}
              onClick={() => setTab("qr")}
            >
              📱 QR Code
            </button>
          </div>

          {/* Tab: Post text */}
          {tab === "text" && (
            <div className="tab-content">
              <label
                className="field-label"
                style={{ marginBottom: 8, display: "block" }}
              >
                Post / Caption Text
                <span className="field-hint"> — Taglish supported</span>
              </label>
              <textarea
                className="post-textarea"
                placeholder={
                  meta.platform === "facebook"
                    ? "Paste a Facebook post here..."
                    : "Paste a tweet here..."
                }
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
              />
              <div className="char-count">{text.length} characters</div>
              <div className="examples-wrap">
                <span className="examples-label">Try an example:</span>
                <button
                  className="example-btn scam-ex"
                  onClick={fillScamSample}
                >
                  🚨 Scam sample
                </button>
                <button
                  className="example-btn legit-ex"
                  onClick={fillLegitSample}
                >
                  ✅ Legit sample
                </button>
              </div>
            </div>
          )}

          {/* Tab: Metadata */}
          {tab === "meta" && (
            <div className="tab-content meta-form">
              <div className="meta-section-title">📅 Account Info</div>

              {/* Date picker — user picks join date, days calculated automatically */}
              <div className="date-field-row">
                <span className="date-field-label">Account Joined Date</span>
                <span className="date-field-hint">
                  Pick the date the account was created
                </span>
                <input
                  type="date"
                  className="date-input"
                  value={joinedDate}
                  max={today}
                  onChange={handleDateChange}
                />
              </div>

              {/* Auto-calculated result — shown below the date picker */}
              <div className="days-display">
                <span className="days-label">Account age in days</span>
                <div className="days-value-wrap">
                  <span className="days-formula">Today − Joined Date =</span>
                  <span className="days-value">{meta.account_age} days</span>
                </div>
              </div>

              <div className="meta-section-title" style={{ marginTop: 20 }}>
                📊 Activity
              </div>
              <NumberField
                label="Posts per Day"
                name="posting_frequency"
                value={meta.posting_frequency}
                onChange={handleMeta}
                hint="Average posting frequency"
                min={0}
                max={100}
                step={0.1}
              />
            </div>
          )}

          {/* Tab: QR Code Upload */}
          {tab === "qr" && (
            <div className="tab-content qr-upload-tab">
              <label className="field-label" style={{ marginBottom: 8, display: "block" }}>
                Upload QR Code Image
                <span className="field-hint"> — PNG, JPG, or JPEG supported</span>
              </label>
              
              <div 
                className={`qr-drop-zone ${qrPreview ? "has-image" : ""}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                {qrPreview ? (
                  <div className="qr-preview-container">
                    <img src={qrPreview} alt="QR Code" className="qr-preview" />
                    <div className="qr-preview-actions">
                      <button 
                        className="btn btn-ghost btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setQrPreview(null);
                          setQrData("");
                          setQrResult(null);
                          if (fileInputRef.current) fileInputRef.current.value = "";
                        }}
                      >
                        Remove
                      </button>
                      {isQrLoading && <span className="qr-loading-text">Decoding...</span>}
                    </div>
                  </div>
                ) : (
                  <div className="qr-drop-placeholder">
                    <div className="qr-drop-icon">📱</div>
                    <div className="qr-drop-text">
                      <strong>Click to upload</strong> or drag & drop
                    </div>
                    <div className="qr-drop-subtext">PNG, JPG, JPEG up to 5MB</div>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleQrUpload}
                  style={{ display: "none" }}
                />
              </div>
              
              {qrData && (
                <div className="qr-decoded-data">
                  <div className="qr-data-label">📝 Decoded Data:</div>
                  <div className="qr-data-value">{qrData}</div>
                </div>
              )}
            </div>
          )}

          {error && <div className="error-msg">⚠️ {error}</div>}

          <div className="action-row">
            {tab !== "qr" ? (
              <>
                <button
                  className="btn btn-primary analyze-btn"
                  onClick={handleSubmit}
                  disabled={loading || !text.trim()}
                >
                  {loading ? (
                    <>
                      <span className="spinner" /> Analysing...
                    </>
                  ) : (
                    <>🔍 Analyse Post</>
                  )}
                </button>
                <button className="btn btn-ghost" onClick={handleReset}>
                  Reset
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn btn-primary analyze-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isQrLoading}
                >
                  {isQrLoading ? (
                    <>
                      <span className="spinner" /> Decoding...
                    </>
                  ) : (
                    <>📱 Upload QR Code</>
                  )}
                </button>
                <button className="btn btn-ghost" onClick={handleReset}>
                  Reset
                </button>
              </>
            )}
          </div>
        </div>

        {/* RIGHT — Result */}
        <div className="result-panel">
          {!displayResult && !loading && !isQrLoading && (
            <div className="result-placeholder">
              <div className="placeholder-icon">🛡️</div>
              <p className="placeholder-title">Ready to analyse</p>
              <p className="placeholder-sub">
                {tab === "qr" ? "Upload a QR code image to scan for scams." : "Enter a post caption and click <strong>Analyse Post</strong>."}
              </p>
              <div className="placeholder-tips">
                {tab === "qr" ? (
                  <>
                    <div className="tip">📱 Supports PNG, JPG, JPEG images</div>
                    <div className="tip">🔍 Extracts URLs from QR codes</div>
                    <div className="tip">⚡ Scans QR content for scam patterns</div>
                  </>
                ) : (
                  <>
                    <div className="tip">💡 Pick the account's join date for accuracy</div>
                    <div className="tip">🌐 Supports Tagalog, English, and Taglish</div>
                    <div className="tip">⚡ Powered by mBERT + Early Fusion</div>
                  </>
                )}
              </div>
            </div>
          )}

          {(loading || isQrLoading) && (
            <div className="result-placeholder">
              <div className="big-spinner" />
              <p className="placeholder-title">
                {isQrLoading ? "Decoding QR Code..." : "Analysing post..."}
              </p>
              <p className="placeholder-sub">
                {isQrLoading ? "Extracting data and scanning for scams" : "Running mBERT encoder + metadata fusion"}
              </p>
            </div>
          )}

          {displayResult && !loading && !isQrLoading && (
            <div style={{ animation: "fadeInUp 0.35s ease" }}>
              <ResultCard result={displayResult} />
              <div className="summary-card card" style={{ marginTop: 16 }}>
                <div className="summary-title">📋 Input Summary</div>
                <div className="summary-grid">
                  {[
                    {
                      label: "Platform",
                      value:
                        meta.platform === "facebook" ? "📘 Facebook" : "🐦 X",
                    },
                    { label: "Joined Date", value: joinedDate },
                    { label: "Acct Age", value: `${meta.account_age} days` },
                    { label: "Posts/Day", value: meta.posting_frequency },
                    ...(displayResult.type === "qr" ? [{ label: "Type", value: "📱 QR Code" }] : [])
                  ].map(({ label, value }) => (
                    <div className="summary-item" key={label}>
                      <span className="s-label">{label}</span>
                      <span className="s-value">{value}</span>
                    </div>
                  ))}
                </div>
                {displayResult.type !== "qr" && (
                  <div className="summary-text">
                    <span className="s-label">Analysed text:</span>
                    <p className="s-text-preview">
                      "{text.substring(0, 120)}
                      {text.length > 120 ? "…" : ""}"
                    </p>
                  </div>
                )}
                {displayResult.type === "qr" && displayResult.qr_data && (
                  <div className="summary-text">
                    <span className="s-label">QR Decoded Data:</span>
                    <p className="s-text-preview">
                      "{displayResult.qr_data.substring(0, 120)}
                      {displayResult.qr_data.length > 120 ? "…" : ""}"
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}