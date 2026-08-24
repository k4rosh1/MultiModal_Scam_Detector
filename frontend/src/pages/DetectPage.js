import React, { useState, useEffect, useRef } from "react";
import { predict, checkHealth, scanQR } from "../api";
import "./DetectPage.css";

const DEFAULT_META = {
  platform: "facebook",
  account_age: 365,
  posting_frequency: 1.0,
};

function dateToDays(dateStr) {
  if (!dateStr) return 0;
  const joined = new Date(dateStr);
  const today = new Date();
  const diff = Math.floor((today - joined) / (1000 * 60 * 60 * 24));
  return diff < 0 ? 0 : diff;
}

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

// ── Content type label ────────────────────────────────────────────────────────
function QRContentTypeBadge({ type }) {
  const map = {
    plain_text: { label: "Plain Text", color: "var(--accent)" },
    url: { label: "URL / Link", color: "var(--warn)" },
    social_media_url: { label: "Social Media Link", color: "#185FA5" },
    media_file: { label: "Media File", color: "var(--danger)" },
    payment_qr: { label: "Payment / E-Wallet", color: "var(--danger)" },
  };
  const info = map[type] || { label: type, color: "var(--text-muted)" };
  return (
    <span
      className="qr-type-badge"
      style={{ borderColor: info.color, color: info.color }}
    >
      {info.label}
    </span>
  );
}

// ── Result card ───────────────────────────────────────────────────────────────
function ResultCard({ result }) {
  const isScam = result.label === 1;
  const scamW = result.scam_prob;
  const legitW = result.legit_prob;

  return (
    <div className={`result-card ${isScam ? "result-scam" : "result-legit"}`}>
      {result.is_mock && (
        <div className="mock-banner">
          🟡 Mock Mode — predictions are simulated
        </div>
      )}
      {result.is_duplicate && (
        <div className="duplicate-banner">
          ⚡ Cached result — this was scanned before. No duplicate saved to
          database.
        </div>
      )}
      <div className="result-header">
        <div className={`result-icon ${isScam ? "icon-scam" : "icon-legit"}`}>
          {isScam ? "🚨" : "✅"}
        </div>
        <div>
          <div className="result-verdict">
            {isScam ? "Scam Detected" : "Looks Legitimate"}
          </div>
          <div className="result-platform">
            {result.platform === "facebook"
              ? "Facebook"
              : result.platform === "twitter"
                ? "X (Twitter)"
                : result.platform === "qr"
                  ? "QR Code"
                  : result.platform}
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
                style={{ width: scamW }}
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
                style={{ width: legitW }}
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
        <span className="conf-value">{result.confidence}</span>
      </div>
    </div>
  );
}

// ── QR Upload tab ─────────────────────────────────────────────────────────────
function QRUploadTab({ onResult, onError, onLoading }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [qrInfo, setQrInfo] = useState(null); // decoded QR info before scan
  const [rejected, setRejected] = useState(null); // rejection message
  const fileRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    const allowed = [
      "image/png",
      "image/jpeg",
      "image/jpg",
      "image/webp",
      "image/bmp",
      "image/gif",
    ];
    if (!allowed.includes(f.type)) {
      onError(
        "Invalid file type. Please upload a PNG, JPG, WEBP, or BMP image.",
      );
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setQrInfo(null);
    setRejected(null);
    onResult(null);
    onError("");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleScan = async () => {
    if (!file) {
      onError("Please upload a QR code image first.");
      return;
    }
    onError("");
    onLoading(true);
    setQrInfo(null);
    setRejected(null);
    onResult(null);
    try {
      const res = await scanQR(file);

      // Right here! We catch the rejection and fire off an alert
      if (res.rejected) {
        setRejected(res.note);
        alert("Scan Rejected!\n\n" + res.note);
        onLoading(false);
        return;
      }

      setQrInfo({
        raw: res.qr_content,
        type: res.content_type,
        note: res.note,
        url: res.url,
        scanned: res.scan_text,
      });
      onResult(res);
    } catch (err) {
      onError(
        err.message ||
          "QR scan failed. Make sure the image contains a clear QR code.",
      );
    } finally {
      onLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setQrInfo(null);
    setRejected(null);
    onResult(null);
    onError("");
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="qr-tab">
      {/* Drop zone */}
      <div
        className={`qr-dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        {preview ? (
          <img src={preview} alt="QR preview" className="qr-preview-img" />
        ) : (
          <>
            <div className="qr-drop-icon"></div>
            <p className="qr-drop-title">Upload QR Code Image</p>
            <p className="qr-drop-sub">Drag & drop or click to browse</p>
            <p className="qr-drop-hint">PNG, JPG, WEBP, BMP supported</p>
          </>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp,image/bmp,image/gif"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {file && (
        <div className="qr-file-info">
          <span className="qr-file-name">📎 {file.name}</span>
          <button className="qr-clear-btn" onClick={handleReset}>
            ✕ Clear
          </button>
        </div>
      )}

      {/* Rejection message */}
      {rejected && (
        <div className="qr-rejected">
          <div className="qr-rejected-icon"></div>
          <p className="qr-rejected-title">Cannot Scan This Content</p>
          <p className="qr-rejected-msg">{rejected}</p>
        </div>
      )}

      {/* Decoded QR info — shown after scan */}
      {qrInfo && (
        <div className="qr-info-card">
          <div className="qr-info-row">
            <span className="qr-info-label">Content type</span>
            <QRContentTypeBadge type={qrInfo.type} />
          </div>
          {qrInfo.url && (
            <div className="qr-info-row">
              <span className="qr-info-label">URL</span>
              <span className="qr-info-value qr-url">{qrInfo.url}</span>
            </div>
          )}
          <div className="qr-info-row">
            <span className="qr-info-label">Raw QR content</span>
            <span className="qr-info-value">{qrInfo.raw}</span>
          </div>
          <div className="qr-info-row">
            <span className="qr-info-label">Scanned text</span>
            <span className="qr-info-value">{qrInfo.scanned}</span>
          </div>
          <div className="qr-info-note">{qrInfo.note}</div>
        </div>
      )}

      <div className="action-row" style={{ marginTop: 8 }}>
        <button
          className="btn btn-primary analyze-btn"
          onClick={handleScan}
          disabled={!file}
        >
          Scan QR Code
        </button>
        {file && (
          <button className="btn btn-ghost" onClick={handleReset}>
            Reset
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main DetectPage ───────────────────────────────────────────────────────────
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
  // platform mode: 'facebook' | 'twitter' | 'qr'
  const [mode, setMode] = useState("facebook");

  useEffect(() => {
    checkHealth().then((ok) => setOnline(ok));
  }, []);

  const handleDateChange = (e) => {
    const dateStr = e.target.value;
    setJoinedDate(dateStr);
    setMeta((prev) => ({ ...prev, account_age: dateToDays(dateStr) }));
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
      const res = await predict({
        text: text.trim(),
        platform: mode,
        account_age: meta.account_age,
        posting_frequency: meta.posting_frequency,
      });
      setResult(res);
    } catch (err) {
      setError(
        err.message ||
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
    setError("");
    setTab("text");
  };

  const fillScamSample = () => {
    setText(
      "GRABE! Kumita ako ng 50000 pesos sa loob ng 7 araw! DM mo ko para malaman kung paano! bit.ly/abc123",
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

  const today = new Date().toISOString().split("T")[0];
  const isQR = mode === "qr";

  return (
    <div className="detect-page">
      <div className="page-header">
        <div className="header-left">
          <div className="header-icon-circle">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <path d="M9 12l2 2 4-4"></path>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Scam Detector</h1>
            <p className="page-sub">
              Enter a post caption, provide account metadata, or upload a QR code
            </p>
          </div>
        </div>
        {online === false && (
          <div className="offline-banner">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            API is offline — start the FastAPI server first
          </div>
        )}
      </div>

      <div className="detect-grid">
        {/* LEFT — Input */}
        <div className="input-panel">
          {/* Platform / Mode selector */}
          <div className="platform-selector">
            <button
              className={`plat-btn ${mode === "facebook" ? "plat-active" : ""}`}
              onClick={() => {
                setMode("facebook");
                setMeta((p) => ({ ...p, platform: "facebook" }));
                setResult(null);
                setError("");
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3.61l.39-4H14V7a1 1 0 0 1 1-1h3z"></path></svg>
              Facebook
            </button>
            <button
              className={`plat-btn ${mode === "twitter" ? "plat-active" : ""}`}
              onClick={() => {
                setMode("twitter");
                setMeta((p) => ({ ...p, platform: "twitter" }));
                setResult(null);
                setError("");
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="4" x2="20" y2="20"></line><line x1="20" y1="4" x2="4" y2="20"></line></svg>
              X (Twitter)
            </button>
            <button
              className={`plat-btn ${mode === "qr" ? "plat-active" : ""}`}
              onClick={() => {
                setMode("qr");
                setResult(null);
                setError("");
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><rect x="7" y="7" width="3" height="3"></rect><rect x="14" y="7" width="3" height="3"></rect><rect x="7" y="14" width="3" height="3"></rect><rect x="14" y="14" width="3" height="3"></rect></svg>
              QR Code
            </button>
          </div>

          {/* ── QR MODE ── */}
          {isQR ? (
            <>
              <div className="qr-mode-notice">
                Platform selection and account metadata are not required for QR
                code scanning. Upload a QR code image and the system will
                extract and analyze its content automatically.
              </div>
              {error && <div className="error-msg">{error}</div>}
              <QRUploadTab
                onResult={setResult}
                onError={setError}
                onLoading={setLoading}
              />
            </>
          ) : (
            <>
              {/* ── NORMAL MODE — Tabs ── */}
              <div className="tab-bar">
                <button
                  className={`tab-btn ${tab === "text" ? "tab-active" : ""}`}
                  onClick={() => setTab("text")}
                >
                  Post Caption
                </button>
                <button
                  className={`tab-btn ${tab === "meta" ? "tab-active" : ""}`}
                  onClick={() => setTab("meta")}
                >
                  Account Metadata
                </button>
              </div>

              {/* Text tab */}
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
                      mode === "facebook"
                        ? "Paste a Facebook post here..."
                        : "Paste a tweet here..."
                    }
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={8}
                    maxLength={2000}
                  />
                  <div className="char-count">{text.length} / 2,000 characters</div>
                  
                  <div className="info-box">
                    <div className="info-box-header">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                      Supports Tagalog, English, and Taglish
                    </div>
                    <div className="info-box-body">
                      Our model understands mixed languages for more accurate detection.
                    </div>
                  </div>
                </div>
              )}

              {/* Metadata tab */}
              {tab === "meta" && (
                <div className="tab-content meta-form">
                  <div className="meta-section-title">Account Info</div>
                  <div className="date-field-row">
                    <span className="date-field-label">
                      Account Joined Date
                    </span>
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
                  <div className="days-display">
                    <span className="days-label">Account age in days</span>
                    <div className="days-value-wrap">
                      <span className="days-formula">
                        Today − Joined Date =
                      </span>
                      <span className="days-value">
                        {meta.account_age} days
                      </span>
                    </div>
                  </div>
                  <div className="meta-section-title" style={{ marginTop: 20 }}>
                    Activity
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

              {error && <div className="error-msg">{error}</div>}

              <div className="action-row">
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
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                      Analyse Post
                    </>
                  )}
                </button>
                <button className="btn btn-ghost reset-btn" onClick={handleReset}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.59-9.21L21.5 8"></path></svg>
                  Reset
                </button>
              </div>
            </>
          )}
        </div>

        {/* RIGHT — Result */}
        <div className="result-panel">
          {!result && !loading && (
            <div className="result-placeholder">
              <img src="/logo.png" alt="Protego" className="placeholder-logo" />
              <h2 className="placeholder-title">Ready to analyze</h2>
              <p className="placeholder-sub">
                {isQR
                  ? "Upload a QR code image and click Scan QR Code."
                  : "Enter a post caption and click Analyse Post."}
              </p>
              <div className="placeholder-bullets">
                {isQR ? (
                  <>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Supports text, URLs, and social media links</div>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Fast and secure scanning</div>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Automatic redirection parsing</div>
                  </>
                ) : (
                  <>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Pick the account's join date for accuracy</div>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Supports Tagalog, English, and Taglish</div>
                    <div className="bullet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Powered by mBERT + Early Fusion + Metadata</div>
                  </>
                )}
              </div>
            </div>
          )}

          {loading && (
            <div className="result-placeholder">
              <div className="big-spinner" />
              <p className="placeholder-title">
                {isQR ? "Scanning QR code..." : "Analysing post..."}
              </p>
              <p className="placeholder-sub">
                {isQR
                  ? "Decoding QR → extracting content → running detection"
                  : "Running mBERT encoder + metadata fusion"}
              </p>
            </div>
          )}

          {result && !loading && (
            <div style={{ animation: "fadeInUp 0.35s ease" }}>
              <ResultCard result={result} />
              {!isQR && (
                <div className="summary-card card" style={{ marginTop: 16 }}>
                  <div className="summary-title">Input Summary</div>
                  <div className="summary-grid">
                    {[
                      {
                        label: "Platform",
                        value: mode === "facebook" ? "Facebook" : "X",
                      },
                      { label: "Joined Date", value: joinedDate },
                      { label: "Acct Age", value: `${meta.account_age} days` },
                      { label: "Posts/Day", value: meta.posting_frequency },
                    ].map(({ label, value }) => (
                      <div className="summary-item" key={label}>
                        <span className="s-label">{label}</span>
                        <span className="s-value">{value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="summary-text">
                    <span className="s-label">Analysed text:</span>
                    <p className="s-text-preview">
                      "{text.substring(0, 120)}
                      {text.length > 120 ? "…" : ""}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
