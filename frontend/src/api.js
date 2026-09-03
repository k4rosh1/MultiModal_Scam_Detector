const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

// FastAPI returns `detail` as a plain string for simple errors (e.g. HTTPException),
// but as an ARRAY of {loc, msg, type} objects for Pydantic validator errors (e.g. the
// "text exceeds maximum length" check). Stringifying that array directly produces
// "[object Object]" instead of a readable message — this extracts the real text either way.
function extractErrorMessage(errBody, fallback) {
  if (!errBody) return fallback;
  const detail = errBody.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return (
      detail
        .map((d) => (d && typeof d === "object" ? d.msg : String(d)))
        .filter(Boolean)
        .join("; ") || fallback
    );
  }
  return fallback;
}

// ── Session ID (per-device privacy) ──────────────────────────────────────────
// Priority: URL param > extension-synced localStorage > existing localStorage > generate new
//
// The extension's sync.js content script sets a "protego_extension_syncing" flag
// in localStorage at document_start, then asynchronously reads chrome.storage
// and writes the extension's session_id. We need to wait for that to finish
// before generating our own (which would create a mismatch).

let _cachedSessionId = null;

export function getSessionId() {
  if (_cachedSessionId) return _cachedSessionId;

  // Check URL param first (highest priority)
  const urlParams = new URLSearchParams(window.location.search);
  const urlSession = urlParams.get('session_id');
  if (urlSession) {
    localStorage.setItem('protego_session_id', urlSession);
    _cachedSessionId = urlSession;
    return urlSession;
  }

  // Read whatever is in localStorage (extension may have already synced)
  let session = localStorage.getItem('protego_session_id');
  if (!session) {
    session = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15);
    localStorage.setItem('protego_session_id', session);
  }
  _cachedSessionId = session;
  return session;
}

// If the extension syncs AFTER React has already booted, listen for the
// storage change and update the cached value so subsequent API calls use it.
window.addEventListener('storage', (e) => {
  if (e.key === 'protego_session_id' && e.newValue) {
    _cachedSessionId = e.newValue;
  }
});

// Also poll once briefly at startup in case extension sync is in progress
(function waitForExtensionSync() {
  if (!localStorage.getItem('protego_extension_syncing')) return;
  let attempts = 0;
  const interval = setInterval(() => {
    attempts++;
    if (!localStorage.getItem('protego_extension_syncing') || attempts > 10) {
      clearInterval(interval);
      const synced = localStorage.getItem('protego_session_id');
      if (synced) _cachedSessionId = synced;
    }
  }, 50);
})();

export async function predict(payload) {
  payload.session_id = getSessionId();
  const res = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(err, `API error ${res.status}`));
  }
  return res.json();
}

export async function getStats() {
  const sessionId = getSessionId();
  const res = await fetch(`${BASE}/stats?session_id=${sessionId}`);
  if (!res.ok) throw new Error("Stats fetch failed");
  return res.json();
}

export async function getDetections(limit = 100, platform = null, offset = 0) {
  const sessionId = getSessionId();
  let url = platform
    ? `${BASE}/detections?limit=${limit}&offset=${offset}&platform=${platform}&session_id=${sessionId}`
    : `${BASE}/detections?limit=${limit}&offset=${offset}&session_id=${sessionId}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Detections fetch failed");
  return res.json();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function scanQR(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", getSessionId());
  const res = await fetch(`${BASE}/scan-qr`, {
    method: "POST",
    body: formData,
    // No Content-Type header — browser sets it automatically with boundary for multipart
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(err, `QR scan error ${res.status}`));
  }
  return res.json();
}

export async function getModelMetrics(modelType = "multimodal") {
  const res = await fetch(`${BASE}/metrics?model_type=${modelType}`);
  if (!res.ok) throw new Error("Metrics fetch failed");
  return res.json();
}

export async function getArchives() {
  const sessionId = getSessionId();
  if (!sessionId) return [];
  const res = await fetch(`${BASE}/archives?session_id=${sessionId}`);
  if (!res.ok) return [];
  return res.json();
}

export function getArchiveDownloadUrl(archiveId) {
  const sessionId = getSessionId();
  return `${BASE}/archives/${archiveId}/download?session_id=${sessionId}`;
}
