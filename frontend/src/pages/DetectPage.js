import React, { useState, useEffect } from "react";
import { predict, checkHealth } from "../api";
import "./DetectPage.css";

function ResultCard({ result }) {
  const isScam = result.label === 1;
  const scamW = result.scam_prob;
  const legitW = result.legit_prob;

  return (
    <div className={`result-card ${isScam ? "result-scam" : "result-legit"}`}>
      {result.is_mock && (
        <div className="mock-banner">
          Mock Mode — predictions are simulated
        </div>
      )}
      {result.is_duplicate && (
        <div className="duplicate-banner">
          Cached result — this post was scanned before. No duplicate saved to
          database.
        </div>
      )}
      <div className="result-header">
        <div className={`result-icon ${isScam ? "icon-scam" : "icon-legit"}`}>
          {isScam ? "!" : "✓"}
        </div>
        <div>
          <div className="result-verdict">
            {isScam ? "Scam Detected" : "Looks Legitimate"}
          </div>
          <div className="result-platform">
            {result.platform === "facebook" ? "Facebook" : "X (Twitter)"}
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

export default function DetectPage() {
  const [text, setText] = useState("");
  const [platform, setPlatform] = useState("facebook");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(null);

  useEffect(() => {
    checkHealth().then((ok) => setOnline(ok));
  }, []);

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
        platform: platform 
      });
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
    setPlatform("facebook");
    setResult(null);
    setError("");
  };

  const fillScamSample = () => {
    setText(
      "GRABE! Kumita ako ng 50000 pesos sa loob ng 7 araw! DM mo ko para malaman kung paano! 💰🔥 bit.ly/abc123",
    );
  };

  const fillLegitSample = () => {
    setText(
      "Kumain kami ni Maria sa Jollibee kanina. Masarap pa rin ang Chickenjoy! Highly recommend 😄",
    );
  };

  return (
    <div className="detect-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Scam Detector</h1>
          <p className="page-sub">
            Enter a post caption to get a scam verdict — Text-Only mBERT
          </p>
        </div>
        {online === false && (
          <div className="offline-banner">
            <span className="dot" /> API is offline — start the FastAPI server first
          </div>
        )}
      </div>

      <div className="detect-grid">
        {/* LEFT — Input */}
        <div className="input-panel">
          {/* Platform */}
          <div className="platform-selector">
            <button
              className={`plat-btn ${platform === "facebook" ? "plat-active" : ""}`}
              onClick={() => setPlatform("facebook")}
            >
              Facebook
            </button>
            <button
              className={`plat-btn ${platform === "twitter" ? "plat-active" : ""}`}
              onClick={() => setPlatform("twitter")}
            >
              X (Twitter)
            </button>
          </div>

          {/* Post Text */}
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
                platform === "facebook"
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
                Scam sample
              </button>
              <button
                className="example-btn legit-ex"
                onClick={fillLegitSample}
              >
                Legit sample
              </button>
            </div>
          </div>

          {error && <div className="error-msg">{error}</div>}

          <div className="action-row">
            <button
              className="analyze-btn"
              onClick={handleSubmit}
              disabled={loading || !text.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner" /> Analysing...
                </>
              ) : (
                <>Analyse Post</>
              )}
            </button>
            <button className="reset-btn" onClick={handleReset}>
              Reset
            </button>
          </div>
        </div>

        {/* RIGHT — Result */}
        <div className="result-panel">
          {!result && !loading && (
            <div className="result-placeholder">
              <div className="placeholder-icon">P</div>
              <p className="placeholder-title">Ready to analyse</p>
              <p className="placeholder-sub">
                Enter a post caption and click <strong>Analyse Post</strong>.
              </p>
              <div className="placeholder-tips">
                <div className="tip">
                  Supports Tagalog, English, and Taglish
                </div>
                <div className="tip">Powered by mBERT Text-Only</div>
                <div className="tip">No metadata required</div>
              </div>
            </div>
          )}

          {loading && (
            <div className="result-placeholder">
              <div className="big-spinner" />
              <p className="placeholder-title">Analysing post...</p>
              <p className="placeholder-sub">
                Running mBERT text-only encoder
              </p>
            </div>
          )}

          {result && !loading && (
            <div style={{ animation: "fadeInUp 0.35s ease" }}>
              <ResultCard result={result} />
              <div className="summary-card" style={{ marginTop: 16 }}>
                <div className="summary-title">Input Summary</div>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="s-label">Platform</span>
                    <span className="s-value">
                      {platform === "facebook" ? "Facebook" : "X (Twitter)"}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="s-label">Text Length</span>
                    <span className="s-value">{text.length} characters</span>
                  </div>
                </div>
                <div className="summary-text">
                  <span className="s-label">Analysed text:</span>
                  <p className="s-text-preview">
                    "{text.substring(0, 120)}
                    {text.length > 120 ? "…" : ""}"
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}