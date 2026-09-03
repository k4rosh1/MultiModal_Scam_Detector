import React, { useState, useEffect } from "react";
import { getDetections, getArchives, getArchiveDownloadUrl } from "../api";
import "./HistoryPage.css";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "scam", label: " Scam" },
  { key: "legit", label: " Legit" },
  { key: "uncertain", label: " Uncertain" },
  { key: "facebook", label: " Facebook" },
  { key: "twitter", label: " X (Twitter)" },
];

// Helper to get extension history
async function getExtensionHistory() {
  if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.id) {
    return [];
  }

  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: "getHistory" }, (response) => {
      if (response && response.history) {
        const formatted = response.history.map((item) => ({
          id: item.id,
          text: item.text || "",
          label: item.verdict === "SCAM" ? 1 : 0,
          verdict: item.verdict,
          confidence: item.confidence,
          scam_prob: item.scam_prob,
          legit_prob: item.legit_prob,
          platform: item.platform,
          timestamp: item.timestamp,
          is_mock: item.is_mock || false,
        }));
        resolve(formatted);
      } else {
        resolve([]);
      }
    });
  });
}

export default function HistoryPage() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedItem, setSelectedItem] = useState(null); // NEW: Tracks clicked row

  const [archives, setArchives] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      // Get both backend and extension data
      const [backendData, extensionData, archivesData] = await Promise.all([
        getDetections(200).catch(() => []),
        getExtensionHistory().catch(() => []),
        getArchives().catch(() => []),
      ]);

      // Merge and sort by ID (newest first)
      const allData = [...backendData, ...extensionData];
      allData.sort((a, b) => (b.id || 0) - (a.id || 0));

      setRows(allData);
      setArchives(archivesData);
      setError("");
    } catch (err) {
      console.error("Failed to load history:", err);
      setError("Cannot reach API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  

  const filtered = rows.filter((r) => {
    const matchFilter =
      filter === "all"
        ? true
        : filter === "scam"
          ? r.label === 1
          : filter === "legit"
            ? r.label === 0
            : filter === "uncertain"
              ? r.label === 2
              : filter === "facebook"
                ? r.platform === "facebook"
                : filter === "twitter"
                  ? r.platform === "twitter"
                  : true;
    const matchSearch =
      search.trim() === "" ||
      (r.text || "").toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const downloadCSV = () => {
    if (!rows || rows.length === 0) {
      alert("No data to archive.");
      return;
    }
    const headers = ["ID", "Verdict", "Platform", "Confidence", "Scam Prob", "Legit Prob", "Timestamp", "Text"];
    const csvRows = rows.map(r => {
      const safeText = (r.text || "").replace(/"/g, '""');
      return [
        r.id,
        r.verdict,
        r.platform,
        `${parseFloat(r.confidence || 0).toFixed(1)}%`,
        `${parseFloat(r.scam_prob || 0).toFixed(1)}%`,
        `${parseFloat(r.legit_prob || 0).toFixed(1)}%`,
        r.timestamp ? new Date(r.timestamp).toISOString() : "",
        `"${safeText}"`
      ].join(",");
    });
    
    const blob = new Blob([[headers.join(","), ...csvRows].join("\n")], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `protego_scans_archive_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="history-page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '48px', height: '48px', background: 'var(--accent-dim)', color: 'var(--accent)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div>
            <h1 className="page-title" style={{ margin: '0 0 4px 0' }}>Detection History</h1>
            <p className="page-sub" style={{ margin: 0 }}>
              All past detections — cloud capacity is strictly capped at 1,000 to save space.
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn" style={{background: 'var(--accent)', color: '#fff'}} onClick={downloadCSV}>
            💾 Download Archive (CSV)
          </button>
          <button className="btn btn-ghost" onClick={load}>
            ↻ Refresh
          </button>
        </div>
      </div>

      <div className="controls-row">
        <div className="filter-tabs">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`filter-tab ${filter === f.key ? "filter-active" : ""}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          className="search-input"
          type="text"
          placeholder="Search post text..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="results-count">
        Showing <strong>{filtered.length}</strong> of {rows.length} detections
      </div>

      {loading ? (
        <div className="table-loading">
          <div className="big-spinner-h" />
          <span>Loading...</span>
        </div>
      ) : error ? (
        <div className="table-error card"> {error}</div>
      ) : filtered.length === 0 ? (
        <div className="table-empty card">
          <div style={{ fontSize: 40, marginBottom: 12 }}></div>
          <p>No detections found.</p>
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>
            Use the Detect page for manual scans, or the extension on
            Facebook/Twitter.
          </p>
        </div>
      ) : (
        <div className="table-wrap card">
          <table className="det-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Verdict</th>
                <th>Platform</th>
                <th>Post Text</th>
                <th>Confidence</th>
                <th>Scam %</th>
                <th>Legit %</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const isScam = r.label === 1;
                const isUncertain = r.label === 2;
                const conf = parseFloat(r.confidence) || 0;
                const ts = r.timestamp
                  ? new Date(r.timestamp).toLocaleString()
                  : "—";
                const rowClass = isUncertain ? "row-uncertain" : isScam ? "row-scam" : "row-legit";
                const tagClass = isUncertain ? "tag-uncertain" : isScam ? "tag-scam" : "tag-legit";
                const tagText = isUncertain ? " Uncertain" : isScam ? " Scam" : " Legit";
                return (
                  <tr
                    key={r.id}
                    className={`clickable-row ${rowClass}`}
                    onClick={() => setSelectedItem(r)}
                  >
                    <td className="mono-cell">#{r.id}</td>
                    <td>
                      <span
                        className={`tag ${tagClass}`}
                      >
                        {tagText}
                      </span>
                    </td>
                    <td>
                      <span className="plat-cell">
                        {r.platform === "facebook"
                          ? " FB"
                          : r.platform === "twitter"
                            ? " X"
                            : r.platform === "qr"
                              ? " QR"
                              : " ?"}
                      </span>
                    </td>
                    <td className="text-cell" title={r.text || ""}>
                      {(r.text || "").substring(0, 70)}
                      {r.text?.length > 70 ? "…" : ""}
                    </td>
                    <td>
                      <div className="mini-bar-wrap">
                        <div className="mini-bar">
                          <div
                            className={`mini-fill ${isUncertain ? "fill-uncertain" : isScam ? "fill-scam" : "fill-legit"}`}
                            style={{ width: `${conf}%` }}
                          />
                        </div>
                        <span className="mono-cell">{conf.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td
                      className="mono-cell"
                      style={{ color: "var(--danger)" }}
                    >
                      {r.scam_prob
                        ? parseFloat(r.scam_prob).toFixed(1) + "%"
                        : "—"}
                    </td>
                    <td className="mono-cell" style={{ color: "var(--safe)" }}>
                      {r.legit_prob
                        ? parseFloat(r.legit_prob).toFixed(1) + "%"
                        : "—"}
                    </td>
                    <td className="ts-cell">{ts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── DETAIL MODAL ── */}
      {selectedItem && (
        <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
          <div
            className="modal-content card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2 className="modal-title">Scan Details #{selectedItem.id}</h2>
              <button
                className="modal-close"
                onClick={() => setSelectedItem(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div
                className="modal-verdict-banner"
                style={{
                  backgroundColor:
                    selectedItem.label === 2
                      ? "rgba(245, 158, 11, 0.1)"
                      : selectedItem.label === 1
                        ? "rgba(240, 82, 82, 0.1)"
                        : "rgba(34, 197, 94, 0.1)",
                  borderColor:
                    selectedItem.label === 2 ? "#f59e0b" : selectedItem.label === 1 ? "var(--danger)" : "var(--safe)",
                }}
              >
                <span style={{ fontSize: 24 }}>
                  {selectedItem.label === 2 ? "⚠️" : selectedItem.label === 1 ? "🚨" : "✅"}
                </span>
                <div>
                  <div
                    style={{
                      fontWeight: "bold",
                      color:
                        selectedItem.label === 2
                          ? "#f59e0b"
                          : selectedItem.label === 1
                            ? "var(--danger)"
                            : "var(--safe)",
                    }}
                  >
                    {selectedItem.verdict}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
                    {selectedItem.platform.toUpperCase()} •{" "}
                    {selectedItem.timestamp
                      ? new Date(selectedItem.timestamp).toLocaleString()
                      : "Unknown Date"}
                  </div>
                </div>
              </div>

              <div className="modal-grid">
                <div className="modal-stat">
                  <span className="modal-stat-label">Model Confidence</span>
                  <span className="modal-stat-value">
                    {parseFloat(selectedItem.confidence || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="modal-stat">
                  <span className="modal-stat-label">Scam Probability</span>
                  <span
                    className="modal-stat-value"
                    style={{ color: "var(--danger)" }}
                  >
                    {parseFloat(selectedItem.scam_prob || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="modal-stat">
                  <span className="modal-stat-label">Legit Probability</span>
                  <span
                    className="modal-stat-value"
                    style={{ color: "var(--safe)" }}
                  >
                    {parseFloat(selectedItem.legit_prob || 0).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="modal-text-section">
                <span className="modal-text-label">Scanned Text / Content</span>
                <div className="modal-text-box">
                  {selectedItem.text || "No text content available."}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── AUTO ARCHIVES SECTION ── */}
      <div style={{ marginTop: '3rem', marginBottom: '2rem' }}>
        <h2 className="page-title" style={{ fontSize: 18, marginBottom: 16 }}>Previous Scans (Auto-Archives)</h2>
        
        {archives.length === 0 ? (
          <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📦</div>
            <p style={{ margin: 0 }}>No auto-archives yet.</p>
            <p style={{ fontSize: 12, marginTop: 4 }}>
              When your active history reaches 1,000 scans, the oldest 500 will automatically be compressed and saved here to free up cloud space!
            </p>
          </div>
        ) : (
          <div className="table-wrap card">
            <table className="det-table">
              <thead>
                <tr>
                  <th>Created Date</th>
                  <th>Total Scans</th>
                  <th>Expires On</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {archives.map(a => (
                  <tr key={a.id}>
                    <td className="ts-cell">{new Date(a.created_at + 'Z').toLocaleString()}</td>
                    <td className="mono-cell">{a.scan_count}</td>
                    <td className="ts-cell" style={{ color: 'var(--text-muted)' }}>{new Date(a.expires_at + 'Z').toLocaleString()}</td>
                    <td>
                      <a href={getArchiveDownloadUrl(a.id)} className="btn" style={{ padding: '4px 12px', fontSize: 12, background: 'var(--accent)', color: '#fff', textDecoration: 'none' }}>
                        Download CSV
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
