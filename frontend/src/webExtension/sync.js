// ── Protego Session Sync ─────────────────────────────────────────────────────
// This content script runs on the Protego web portal (Vercel / localhost).
// It grabs the extension's session_id from chrome.storage.local and injects it
// into the web page's localStorage, so the portal automatically uses the same
// session as the extension. Zero login, zero clicks required.
//
// Runs at document_start (before React loads) to win the race against
// React's getSessionId() which reads localStorage synchronously.

(function () {
  // Signal to React that the extension is present and syncing
  window.localStorage.setItem("protego_extension_syncing", "true");

  chrome.storage.local.get("session_id", (data) => {
    if (data.session_id) {
      window.localStorage.setItem("protego_session_id", data.session_id);
      console.log("[Protego Extension] Session synced:", data.session_id);
    }
    // Clear the syncing flag so React knows it can safely read now
    window.localStorage.removeItem("protego_extension_syncing");
  });
})();
