const BASE = "http://localhost:8000";

export async function predict(payload) {
  const res = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
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

// Follows redirects for a shortener/dynamic-QR link (me-qr.com, bit.ly, etc.)
// server-side and returns the final destination URL. Needed because browsers
// block JS from reading cross-origin redirect targets (CORS).
export async function resolveUrl(url) {
  const res = await fetch(
    `${BASE}/resolve-url?url=${encodeURIComponent(url)}`,
    {
      signal: AbortSignal.timeout(8000),
    },
  );
  if (!res.ok) {
    throw new Error(`Resolve request failed (${res.status})`);
  }
  return res.json(); // { ok, resolved_url?, error?, original_url }
}
