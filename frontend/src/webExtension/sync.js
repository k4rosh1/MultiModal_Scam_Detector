// ── Protego Session Sync ─────────────────────────────────────────────────────
// This content script runs on the Protego web portal (Vercel).
// It grabs the extension's session_id from chrome.storage.local and injects it
// into the web page's localStorage, so the portal automatically uses the same
// session as the extension. Zero login, zero clicks required.

(function () {
  chrome.storage.local.get("session_id", (data) => {
    if (data.session_id) {
      // Inject the extension's session_id into the web portal's localStorage
      window.localStorage.setItem("protego_session_id", data.session_id);
      console.log("[Protego Extension] Session synced:", data.session_id);
    }
  });
})();
