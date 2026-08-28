const BASE = "https://protego.duckdns.org";

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

export async function predict(payload) {
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
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error("Stats fetch failed");
  return res.json();
}

export async function getDetections(limit = 100, platform = null) {
  const url = platform
    ? `${BASE}/detections?limit=${limit}&platform=${platform}`
    : `${BASE}/detections?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Detections fetch failed");
  return res.json();
}

export async function clearDetections() {
  const res = await fetch(`${BASE}/detections/clear`, { method: "DELETE" });
  if (!res.ok) throw new Error("Clear failed");
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
