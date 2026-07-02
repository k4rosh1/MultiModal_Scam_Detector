import jsQR from "jsqr";

// ── QR IMAGE DECODING ──────────────────────────────────────────────────────
// Reads an uploaded image file, draws it to an off-screen canvas, and runs
// jsQR against the raw pixel data to find/decode a QR code.
//
// Returns the decoded string, or null if no QR code could be found in the
// image (i.e. the uploaded file is not a QR code / doesn't contain one).
export function decodeQRFromImage(file) {
  return new Promise((resolve, reject) => {
    if (!file || !file.type || !file.type.startsWith("image/")) {
      reject(new Error("Uploaded file is not an image."));
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, imageData.width, imageData.height, {
          inversionAttempts: "attemptBoth",
        });

        URL.revokeObjectURL(objectUrl);
        resolve(code ? code.data : null);
      } catch (err) {
        URL.revokeObjectURL(objectUrl);
        reject(err);
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Could not load the uploaded file as an image."));
    };

    img.src = objectUrl;
  });
}

// ── QR CONTENT CLASSIFICATION ──────────────────────────────────────────────
// Once a QR code is decoded, its payload can be almost anything (a link,
// Wi-Fi credentials, a contact card, plain text, etc). We accept anything
// that's plausibly a "post/caption" — a link to ANY site, or a block of
// plain text — regardless of which platform (if any) it came from. A QR
// code has no idea what app it was scanned inside of, so we don't gate
// acceptance on the destination domain; we only reject payload *shapes*
// that clearly aren't post/caption content at all (Wi-Fi, contact cards,
// calendar invites, tel/mailto/etc).
//
// The Facebook/X "platform" selector elsewhere in the UI is just a manual
// hint about where the user encountered the content — same as it already
// was for the plain-text tab. We opportunistically auto-fill it when the
// QR happens to link straight to facebook.com/x.com, purely as a UX nicety,
// but it is never required for the content to be accepted.

const FB_HOSTS = [
  "facebook.com",
  "m.facebook.com",
  "fb.watch",
  "fb.com",
  "mbasic.facebook.com",
];
const X_HOSTS = ["twitter.com", "x.com", "mobile.twitter.com"];

// Payload formats that are never a "post/caption" no matter the source app.
const NON_POST_PATTERNS = [
  /^WIFI:/i,
  /^BEGIN:VCARD/i,
  /^MECARD:/i,
  /^BEGIN:VEVENT/i,
  /^BEGIN:VCALENDAR/i,
  /^tel:/i,
  /^smsto:/i,
  /^sms:/i,
  /^mailto:/i,
  /^geo:/i,
  /^bitcoin:/i,
  /^matmsg:/i,
  /^upi:\/\//i,
];

function matchesHost(hostname, list) {
  const host = hostname.replace(/^www\./i, "").toLowerCase();
  return list.some((h) => host === h || host.endsWith(`.${h}`));
}

// Best-effort platform hint from a URL's hostname — used only to
// pre-select the Facebook/X toggle, never to gate acceptance.
function detectPlatformHint(hostname) {
  if (matchesHost(hostname, FB_HOSTS)) return "facebook";
  if (matchesHost(hostname, X_HOSTS)) return "twitter";
  return null;
}

/**
 * Classify decoded QR text.
 * Returns one of:
 *  { valid: true,  platform: "facebook" | "twitter" | null, contentType: "link" | "text", text, hostname? }
 *  { valid: false, reason: string }
 */
export function classifyQRContent(raw) {
  const content = (raw || "").trim();

  if (!content) {
    return { valid: false, reason: "The QR code appears to be empty." };
  }

  if (NON_POST_PATTERNS.some((p) => p.test(content))) {
    return {
      valid: false,
      reason:
        "This QR code contains Wi-Fi/contact/calendar/payment data — not a post or caption.",
    };
  }

  // Try to parse as a URL first.
  let url = null;
  try {
    url = new URL(content);
  } catch {
    url = null;
  }

  if (url) {
    if (!/^https?:$/.test(url.protocol)) {
      return {
        valid: false,
        reason: `This QR code contains a "${url.protocol}" link, which isn't a post or caption.`,
      };
    }
    // Any http(s) link is accepted — it's plausibly a link to a post,
    // regardless of which site hosts it or which app the QR was found in.
    return {
      valid: true,
      platform: detectPlatformHint(url.hostname),
      contentType: "link",
      text: content,
      hostname: url.hostname,
    };
  }

  // Not a URL — treat as raw caption/post text.
  if (content.length < 3) {
    return {
      valid: false,
      reason: "QR content is too short to be a post or caption.",
    };
  }

  return { valid: true, platform: null, contentType: "text", text: content };
}

/**
 * Best-effort, informational-only enrichment: if the accepted content is a
 * link, try to resolve it past any shortener/dynamic-QR wrapper (me-qr.com,
 * bit.ly, tinyurl...) so the user can see the real destination and, if it
 * happens to be Facebook/X, get the platform toggle auto-selected. This
 * NEVER rejects content — resolution failing just means we display the
 * original link as-is.
 */
export function enrichResolvedLink(resolvedUrl) {
  let url;
  try {
    url = new URL(resolvedUrl);
  } catch {
    return null;
  }
  return {
    text: resolvedUrl,
    hostname: url.hostname,
    platform: detectPlatformHint(url.hostname),
  };
}
