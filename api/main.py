# =============================================================================
# ScamShield — FastAPI Server  (v3 — Optimized + Encrypted)
# =============================================================================
# MOCK_MODE = True  → simulated predictions (while model is training on Colab)
# MOCK_MODE = False → loads real trained model from scam_model/
#
# Run:
#   cd C:\scam_project\api
#   uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# First-time setup — generate encryption key:
#   python -c "from cryptography.fernet import Fernet
import re
import io
import cv2
import numpy as np_cv  # alias to avoid conflict with existing numpy as np
import requests as http_requests
from PIL import Image
from urllib.parse import urlparse
from fastapi import UploadFile, File, HTTPException
#   Copy the output into a file called  api/.env  as:
#   DB_ENCRYPTION_KEY=<paste key here>
# =============================================================================

import os
import hashlib
import sqlite3
import datetime
import threading
import numpy as np
import torch
import torch.nn as nn
from contextlib import contextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cryptography.fernet import Fernet
import re
import io
import cv2
import numpy as np_cv  # alias to avoid conflict with existing numpy as np
import requests as http_requests
from PIL import Image
from urllib.parse import urlparse
from fastapi import UploadFile, File, HTTPException

# ── CONFIG ────────────────────────────────────────────────────────────────────
MOCK_MODE  = False
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "scam_model")
DB_PATH    = os.path.join(os.path.dirname(__file__), "detections.db")
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LEN    = 128
METADATA_COLS = ["account_age", "posting_frequency"]

# ── ENCRYPTION SETUP ──────────────────────────────────────────────────────────
# Load key from .env file or environment variable
def _load_key() -> bytes:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DB_ENCRYPTION_KEY="):
                    return line.split("=", 1)[1].strip().encode()
    # Fall back to environment variable
    key = os.environ.get("DB_ENCRYPTION_KEY")
    if key:
        return key.encode()
    # Auto-generate and save if no key exists (first run)
    new_key = Fernet.generate_key()
    with open(env_path, "w") as f:
        f.write(f"DB_ENCRYPTION_KEY={new_key.decode()}\n")
    print("🔑 Encryption key auto-generated and saved to api/.env")
    print("   Keep this file safe — losing it means losing access to stored data.")
    return new_key

_fernet = Fernet(_load_key())

def encrypt(value: str) -> str:
    """Encrypt a string value before storing in the database."""
    if not value:
        return ""
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    """Decrypt a string value after reading from the database."""
    if not value:
        return ""
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        # Already plain text (migration: old unencrypted rows)
        return value

# ── DATABASE ──────────────────────────────────────────────────────────────────
# Connection pool using thread-local storage — one connection per thread,
# reused across requests instead of opening/closing on every call.
_local = threading.local()

@contextmanager
def get_db():
    """Thread-local SQLite connection with WAL mode and foreign keys enabled."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        # WAL mode: readers don't block writers, better concurrent performance
        _local.conn.execute("PRAGMA journal_mode=WAL")
        # Improve write performance
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA cache_size=1000")
    try:
        yield _local.conn
    except Exception:
        _local.conn.rollback()
        raise

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp         TEXT,
                platform          TEXT,
                text              TEXT,
                label             INTEGER,
                verdict           TEXT,
                confidence        REAL,
                scam_prob         REAL,
                legit_prob        REAL,
                account_age       INTEGER,
                posting_frequency REAL,
                is_mock           INTEGER DEFAULT 0,
                text_hash         TEXT,
                duplicate_count   INTEGER DEFAULT 0
            )
        """)
        # Create index for faster stats queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_label
            ON detections(label)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_platform
            ON detections(platform)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON detections(timestamp)
        """)
        # Index for fast duplicate lookup on text_hash
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_text_hash
            ON detections(text_hash)
        """)
        # Migration: add missing columns from older databases
        existing = {row[1] for row in conn.execute("PRAGMA table_info(detections)").fetchall()}
        if "account_age" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN account_age INTEGER DEFAULT 0")
        if "posting_frequency" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN posting_frequency REAL DEFAULT 0")
        if "text_hash" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN text_hash TEXT")
        if "duplicate_count" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN duplicate_count INTEGER DEFAULT 0")
        conn.commit()
    print("✅ Database initialized with WAL mode and indexes")

init_db()

def _make_hash(text: str, platform: str, account_age: float, posting_frequency: float) -> str:
    """Create a SHA-256 hash of the input combination for duplicate detection."""
    raw = f"{text.strip().lower()}|{platform}|{round(account_age)}|{round(posting_frequency, 1)}"
    return hashlib.sha256(raw.encode()).hexdigest()

def find_duplicate(text: str, platform: str, account_age: float, posting_frequency: float):
    """Check if this exact input combination was already detected before.
    Returns the existing row dict if found, None otherwise."""
    h = _make_hash(text, platform, account_age, posting_frequency)
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM detections WHERE text_hash=? ORDER BY id DESC LIMIT 1", (h,)
        ).fetchone()
        if row:
            # Increment duplicate_count so we track how many times it was re-scanned
            conn.execute(
                "UPDATE detections SET duplicate_count = duplicate_count + 1 WHERE id=?",
                (row["id"],)
            )
            conn.commit()
            result = decrypt_row(dict(row))
            result["is_duplicate"] = True
            return result
    return None

def save_detection(data: dict, is_mock: bool = False):
    """Save detection with encrypted text, platform, and verdict fields."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO detections
            (timestamp, platform, text, label, verdict, confidence,
             scam_prob, legit_prob, account_age, posting_frequency, is_mock, text_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            encrypt(data.get("platform", "unknown")),   # encrypted
            encrypt((data.get("text", ""))[:500]),       # encrypted
            data.get("label",     -1),
            encrypt(data.get("verdict", "")),            # encrypted
            data.get("confidence", 0),
            data.get("scam_prob",  0),
            data.get("legit_prob", 0),
            data.get("account_age",       0),
            data.get("posting_frequency", 0),
            1 if is_mock else 0,
            _make_hash(
                data.get("text", ""),
                data.get("platform", "unknown"),
                data.get("account_age", 0),
                data.get("posting_frequency", 0),
            ),
        ))
        conn.commit()

def decrypt_row(row: dict) -> dict:
    """Decrypt encrypted fields in a row dict before returning to frontend."""
    row["text"]     = decrypt(row.get("text",     ""))
    row["platform"] = decrypt(row.get("platform", ""))
    row["verdict"]  = decrypt(row.get("verdict",  ""))
    return row

# ── MODEL ARCHITECTURE ────────────────────────────────────────────────────────
class EarlyFusionScamDetector(nn.Module):
    """
    Multi-modal Early Fusion model.
    768-dim mBERT [CLS] + 2 metadata = 770-dim → single FC layer → 2 classes
    """
    def __init__(self, bert_model_name):
        super().__init__()
        from transformers import AutoModel
        self.bert       = AutoModel.from_pretrained(bert_model_name)
        self.classifier = nn.Linear(768 + 2, 2)

    def forward(self, input_ids, attention_mask, metadata):
        bert_out      = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = bert_out.last_hidden_state[:, 0, :]
        fused         = torch.cat([cls_embedding, metadata], dim=1)
        return self.classifier(fused)

# ── LOAD REAL MODEL ───────────────────────────────────────────────────────────
tokenizer = None
scaler    = None
model     = None

if not MOCK_MODE:
    try:
        import joblib
        from transformers import AutoTokenizer
        print(f"Loading model from {MODEL_DIR}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        scaler    = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        model     = EarlyFusionScamDetector(bert_model_name="bert-base-multilingual-cased")
        model.load_state_dict(
            torch.load(os.path.join(MODEL_DIR, "model.pt"), map_location=DEVICE),
            strict=False
        )
        model.to(DEVICE)
        model.eval()
        print(f"✅ Real model loaded on {DEVICE}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Falling back to MOCK_MODE")
        MOCK_MODE = True
else:
    print("🟡 MOCK_MODE is ON — returning simulated predictions")

# ── RATE LIMITER ──────────────────────────────────────────────────────────────
# Limits: /predict → 30 requests/minute per IP (prevents spam/abuse)
#         /stats   → 60 requests/minute per IP
#         /detections → 60 requests/minute per IP
limiter = Limiter(key_func=get_remote_address)

# ── FASTAPI APP ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScamShield API",
    description="Taglish scam detection — mBERT + Early Fusion (770-dim)",
    version="3.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load allowed origins from .env
# Local dev:   ALLOWED_ORIGINS=http://localhost:3000
# Production:  ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
def _load_allowed_origins() -> list:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ALLOWED_ORIGINS="):
                    raw = line.split("=", 1)[1].strip()
                    return [o.strip() for o in raw.split(",") if o.strip()]
    env_val = os.environ.get("ALLOWED_ORIGINS", "")
    if env_val:
        return [o.strip() for o in env_val.split(",") if o.strip()]
    # Fallback to localhost only
    return ["http://localhost:3000"]

ALLOWED_ORIGINS = _load_allowed_origins()
print(f"🌐 CORS allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# ── REQUEST SCHEMA ────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    text:              str
    platform:          Optional[str]   = "facebook"
    account_age:       Optional[float] = 365.0
    posting_frequency: Optional[float] = 1.0

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("text cannot be empty")
        if len(v) > 2000:
            raise ValueError("text exceeds maximum length of 2000 characters")
        return v.strip()

    @validator("account_age")
    def age_must_be_positive(cls, v):
        if v is None: return 365.0
        return max(0.0, float(v))

    @validator("posting_frequency")
    def freq_must_be_positive(cls, v):
        if v is None: return 1.0
        return max(0.0, float(v))

# ── MOCK PREDICTION ───────────────────────────────────────────────────────────
def mock_predict(req: PredictRequest) -> dict:
    text  = req.text.lower()
    score = 0
    scam_keywords = [
        "kumita", "pesos", "₱", "gcash", "dm mo", "libre", "free",
        "promo", "raffle", "invest", "click", "bit.ly", "tinyurl",
        "congratulations", "nanalo", "limited", "urgent", "verify"
    ]
    for kw in scam_keywords:
        if kw in text:
            score += 15
    if req.account_age       < 90:  score += 20
    if req.posting_frequency > 10:  score += 25
    score      = max(0, min(100, score))
    label      = 1 if score >= 50 else 0
    scam_prob  = float(score)
    legit_prob = 100.0 - scam_prob
    confidence = scam_prob if label == 1 else legit_prob
    return {
        "label":      label,
        "verdict":    "SCAM" if label == 1 else "LEGITIMATE",
        "confidence": f"{confidence:.1f}%",
        "scam_prob":  f"{scam_prob:.1f}%",
        "legit_prob": f"{legit_prob:.1f}%",
        "platform":   req.platform,
        "is_mock":    True,
    }

# ── REAL PREDICTION ───────────────────────────────────────────────────────────
def real_predict(req: PredictRequest) -> dict:
    enc = tokenizer(
        req.text, max_length=MAX_LEN, padding='max_length',
        truncation=True, return_tensors='pt'
    )
    input_ids      = enc['input_ids'].to(DEVICE)
    attention_mask = enc['attention_mask'].to(DEVICE)
    meta_raw    = np.array([[req.account_age, req.posting_frequency]], dtype=np.float32)
    meta_scaled = scaler.transform(meta_raw)
    metadata    = torch.tensor(meta_scaled, dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        logits = model(input_ids, attention_mask, metadata)
        probs  = torch.softmax(logits, dim=1)[0]
        label  = logits.argmax(dim=1).item()
    confidence = probs[label].item() * 100
    scam_prob  = probs[1].item() * 100
    legit_prob = probs[0].item() * 100
    return {
        "label":      label,
        "verdict":    "SCAM" if label == 1 else "LEGITIMATE",
        "confidence": f"{confidence:.1f}%",
        "scam_prob":  f"{scam_prob:.1f}%",
        "legit_prob": f"{legit_prob:.1f}%",
        "platform":   req.platform,
        "is_mock":    False,
    }

# ── QR CODE SCANNER ──────────────────────────────────────────────────────────

# File types considered as pure media (cannot be scanned for scam text)
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico',  # images
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v',  # videos
    '.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a',                   # audio
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',         # documents (non-text)
}

# Social media URL patterns
SOCIAL_PATTERNS = {
    'facebook': [r'facebook\.com', r'fb\.com', r'fb\.watch', r'm\.facebook\.com'],
    'twitter':  [r'twitter\.com', r'x\.com', r't\.co'],
    'instagram':[r'instagram\.com', r'instagr\.am'],
    'tiktok':   [r'tiktok\.com', r'vm\.tiktok\.com'],
    'youtube':  [r'youtube\.com', r'youtu\.be'],
}

def _upscale_if_small(img, min_dim: int = 400):
    """Upscale small images — OpenCV's/zbar's QR detectors are much more
    reliable on QR codes that are at least a few hundred pixels across.
    Many QR codes from free online generators are exported tiny (~150px)."""
    h, w = img.shape[:2]
    scale = max(1.0, min_dim / min(h, w))
    if scale > 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    return img


def _decode_with_pyzbar(img) -> str:
    """Try decoding with pyzbar (libzbar) — significantly more robust than
    OpenCV's built-in QRCodeDetector, especially for small/low-contrast/
    tightly-cropped QR codes from third-party generators."""
    try:
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        return ""

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Attempt 1: raw grayscale
    results = zbar_decode(gray)
    if results:
        return results[0].data.decode("utf-8", errors="ignore").strip()

    # Attempt 2: contrast-enhanced
    enhanced = cv2.equalizeHist(gray)
    results = zbar_decode(enhanced)
    if results:
        return results[0].data.decode("utf-8", errors="ignore").strip()

    # Attempt 3: binary threshold (helps with low-contrast / off-white backgrounds)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results = zbar_decode(thresh)
    if results:
        return results[0].data.decode("utf-8", errors="ignore").strip()

    return ""


def _decode_with_opencv(img) -> str:
    """Fallback decoder using OpenCV's built-in QRCodeDetector."""
    detector = cv2.QRCodeDetector()

    data, bbox, _ = detector.detectAndDecode(img)
    if data:
        return data.strip()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    data, bbox, _ = detector.detectAndDecode(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR))
    if data:
        return data.strip()

    return ""


def decode_qr_from_image(image_bytes: bytes) -> str:
    """Decode QR code from image bytes. Returns the decoded string.

    Uses pyzbar (libzbar) as the primary decoder since it is far more
    tolerant of small, low-contrast, or tightly-cropped QR images (common
    with free online QR generators), falling back to OpenCV's built-in
    QRCodeDetector if pyzbar is unavailable or fails.
    """
    # Convert bytes to numpy array
    nparr = np_cv.frombuffer(image_bytes, np_cv.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image. Make sure it is a valid image file (PNG, JPG, etc.).")

    img = _upscale_if_small(img)

    # Try pyzbar first — most robust
    data = _decode_with_pyzbar(img)
    if data:
        return data

    # Fall back to OpenCV's detector
    data = _decode_with_opencv(img)
    if data:
        return data

    raise ValueError("No QR code detected in this image. Make sure the image is clear and the QR code is fully visible.")

def _resolve_final_url(url: str, timeout: float = 5.0) -> str:
    """Follow redirects (shorteners, QR tracking links like me-qr.com, bit.ly,
    etc.) to find the final destination URL. Returns the original URL
    unchanged if resolution fails for any reason — never raises."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ScamShieldBot/1.0)'}
        resp = http_requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        # Some servers don't support HEAD properly (405/403) — retry with GET
        if resp.status_code >= 400 or resp.url == url:
            resp = http_requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
            resp.close()
        return resp.url or url
    except Exception:
        return url


def classify_qr_content(content: str) -> dict:
    """
    Classify what type of content a QR code holds.
    Returns a dict with: type, platform, is_media, scan_text, note
    """
    content = content.strip()

    # ── Check if it is a URL ──────────────────────────────────────────────────
    is_url = content.startswith(('http://', 'https://', 'www.', 'ftp://'))

    if not is_url:
        # Plain text — scan directly
        return {
            'type':       'plain_text',
            'platform':   'qr',
            'is_media':   False,
            'scan_text':  content,
            'note':       'Plain text extracted from QR code.',
            'url':        None,
        }

    # ── Resolve redirects/shorteners (e.g. me-qr.com, bit.ly, tinyurl) ────────
    # QR codes very commonly encode a tracking/redirect link rather than the
    # final destination. We resolve it first so classification and content
    # extraction reflect where it actually leads, not the shortener itself.
    original_content = content
    resolved_url = _resolve_final_url(content)
    used_redirect = resolved_url != original_content
    content = resolved_url

    # ── It is a URL — parse it ────────────────────────────────────────────────
    try:
        parsed = urlparse(content if content.startswith('http') else 'https://' + content)
        path   = parsed.path.lower()
        ext    = '.' + path.split('.')[-1] if '.' in path else ''
    except Exception:
        parsed = None
        path   = ''
        ext    = ''

    redirect_note = f' (resolved from shortener/redirect: {original_content})' if used_redirect else ''

    # ── Check if URL points directly to a media file ──────────────────────────
    if ext in MEDIA_EXTENSIONS:
        return {
            'type':      'media_file',
            'platform':  'qr',
            'is_media':  True,
            'scan_text': None,
            'note':      f'This QR code links directly to a media file ({ext}){redirect_note}. There is no text content to scan for scams.',
            'url':       content,
            'original_url': original_content,
            'used_redirect': used_redirect,
        }

    # ── Check if URL is a recognized social media link ────────────────────────
    matched_platform = None
    for platform_name, patterns in SOCIAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matched_platform = platform_name
                break
        if matched_platform:
            break

    # ── Extract page content (title / description) for ANY URL ────────────────
    # Not just recognized social platforms — plain scam/phishing pages are
    # just as important to analyze based on real page content rather than
    # the bare URL string.
    extracted = _extract_page_text(content)

    if matched_platform:
        if extracted:
            return {
                'type':      'social_media_url',
                'platform':  matched_platform,
                'is_media':  False,
                'scan_text': extracted,
                'note':      f'Social media link detected ({matched_platform.capitalize()}){redirect_note}. Post caption extracted from page.',
                'url':       content,
                'original_url': original_content,
                'used_redirect': used_redirect,
            }
        else:
            return {
                'type':      'social_media_url',
                'platform':  matched_platform,
                'is_media':  False,
                'scan_text': content,
                'note':      f'Social media link detected ({matched_platform.capitalize()}){redirect_note}. Caption could not be extracted — scanning URL text instead.',
                'url':       content,
                'original_url': original_content,
                'used_redirect': used_redirect,
            }

    # ── Generic URL — use extracted page content if available, else the URL ──
    return {
        'type':      'url',
        'platform':  'qr',
        'is_media':  False,
        'scan_text': extracted if extracted else content,
        'note':      (f'URL extracted from QR code{redirect_note}. '
                      + ('Page content extracted and scanned for scam indicators.' if extracted
                         else 'Could not extract page content — scanning URL text instead.')),
        'url':       content,
        'original_url': original_content,
        'used_redirect': used_redirect,
    }

import html as _html_module  # for unescaping HTML entities

# Boilerplate signals — QR-hosting/redirect services (me-qr.com and similar
# "QR code as a service" sites) reuse the same generic meta description for
# every dynamically-hosted page. When a description matches this pattern, we
# treat it as unreliable and prefer the page's actual visible body text,
# which is where the real encoded content (e.g. a "text"-type QR's payload)
# usually lives instead.
_BOILERPLATE_META_HINTS = (
    'qr code generator', 'make qr code', 'create qr code', 'scan qr code',
    'making free qr', 'qr codes online', 'free qr code',
)


def _looks_like_boilerplate(text: str) -> bool:
    t = text.lower()
    return any(hint in t for hint in _BOILERPLATE_META_HINTS)


def _extract_body_text(html_src: str, max_len: int = 1000) -> str | None:
    """Strip scripts/styles/nav/header/footer and pull the visible text left
    in <body>. This is what catches content on pages (like me-qr's 'text'
    QR display pages) where the real payload lives in the body, not in any
    meta tag."""
    # Isolate <body> if present
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_src, re.IGNORECASE | re.DOTALL)
    body = body_match.group(1) if body_match else html_src

    # Remove non-content elements entirely (including their inner text)
    body = re.sub(r'<(script|style|noscript|nav|header|footer)[^>]*>.*?</\1>', ' ', body, flags=re.IGNORECASE | re.DOTALL)

    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', body)
    text = _html_module.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text[:max_len] if text else None


def _extract_page_text(url: str) -> str | None:
    """
    Fetch a URL and extract representative text for scam analysis.
    Tries Open Graph description / meta description / <title> first (works
    well for standard social platforms), but falls back to — or overrides
    with — the page's actual visible body text when those meta fields look
    like generic site boilerplate rather than real content (common on
    QR-hosting/redirect services that dynamically display arbitrary text
    or links behind a templated page).
    Fails silently — never crashes the main flow.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ScamShieldBot/1.0)',
        }
        resp = http_requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if resp.status_code != 200:
            return None
        html_src = resp.text

        meta_candidate = None

        og_desc = re.search(r"""<meta[^>]+property=["'](og:description)["'][^>]+content=["'](.*?)["']""", html_src, re.IGNORECASE | re.DOTALL)
        if og_desc and og_desc.group(2).strip():
            meta_candidate = _html_module.unescape(og_desc.group(2).strip())[:1000]

        if not meta_candidate:
            meta_desc = re.search(r"""<meta[^>]+name=["'](description)["'][^>]+content=["'](.*?)["']""", html_src, re.IGNORECASE | re.DOTALL)
            if meta_desc and meta_desc.group(2).strip():
                meta_candidate = _html_module.unescape(meta_desc.group(2).strip())[:1000]

        # If the meta description looks like generic QR-service boilerplate,
        # don't trust it — try to pull the real content from the body instead.
        if meta_candidate and not _looks_like_boilerplate(meta_candidate):
            return meta_candidate

        body_text = _extract_body_text(html_src)
        if body_text and not _looks_like_boilerplate(body_text):
            return body_text

        # Nothing better found — fall back to whatever we have
        if meta_candidate:
            return meta_candidate
        if body_text:
            return body_text

        # Last resort: <title> tag
        title = re.search(r"""<title[^>]*>(.*?)</title>""", html_src, re.IGNORECASE | re.DOTALL)
        if title and title.group(1).strip():
            return _html_module.unescape(title.group(1).strip())[:1000]

        return None
    except Exception:
        return None

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status":    "running",
        "mock_mode": MOCK_MODE,
        "device":    str(DEVICE),
        "docs":      "http://localhost:8000/docs"
    }

@app.get("/health")
def health():
    """Dedicated health check endpoint — used by browser extension and frontend."""
    return {
        "status":    "ok",
        "mock_mode": MOCK_MODE,
        "device":    str(DEVICE),
    }

@app.post("/scan-qr")
@limiter.limit("20/minute")
async def scan_qr(request: Request, file: UploadFile = File(...)):
    """
    QR Code scanning endpoint.
    Accepts an image upload, decodes the QR, classifies the content,
    and runs it through the scam detection pipeline.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp", "image/gif"}
    content_type  = (file.content_type or "").lower()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PNG, JPG, WEBP, or BMP image."
        )

    # ── Read and decode QR ────────────────────────────────────────────────────
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 10MB.")

    try:
        qr_content = decode_qr_from_image(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── Classify the QR content ───────────────────────────────────────────────
    classified = classify_qr_content(qr_content)

    # ── Reject pure media files ───────────────────────────────────────────────
    if classified["is_media"]:
        return {
            "qr_content":  qr_content,
            "content_type": classified["type"],
            "platform":    "qr",
            "note":        classified["note"],
            "resolved_url": classified.get("url"),
            "used_redirect": classified.get("used_redirect", False),
            "rejected":    True,
            "verdict":     None,
            "risk_score":  None,
        }

    # ── Run through scam detection pipeline ───────────────────────────────────
    scan_text = classified["scan_text"]
    if not scan_text or not scan_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract scannable text from QR content.")

    # For QR scans, metadata is not applicable — use neutral default values
    DEFAULT_AGE  = 365.0
    DEFAULT_FREQ = 1.0

    # Check for duplicate
    existing = find_duplicate(scan_text, "qr", DEFAULT_AGE, DEFAULT_FREQ)
    if existing:
        return {
            "qr_content":   qr_content,
            "content_type": classified["type"],
            "platform":     classified["platform"],
            "note":         classified["note"],
            "url":          classified.get("url"),
            "original_url": classified.get("original_url"),
            "used_redirect": classified.get("used_redirect", False),
            "scan_text":    scan_text,
            "rejected":     False,
            "is_duplicate": True,
            "label":        existing.get("label", -1),
            "verdict":      existing.get("verdict", ""),
            "confidence":   existing.get("confidence", ""),
            "scam_prob":    existing.get("scam_prob", ""),
            "legit_prob":   existing.get("legit_prob", ""),
            "is_mock":      bool(existing.get("is_mock", 0)),
        }

    # Create a fake PredictRequest for the existing pipeline
    class _QRRequest:
        text              = scan_text
        platform          = "qr"
        account_age       = DEFAULT_AGE
        posting_frequency = DEFAULT_FREQ

    qr_req = _QRRequest()
    result = mock_predict(qr_req) if MOCK_MODE else real_predict(qr_req)

    # Save to database
    save_detection({
        "text":              scan_text,
        "platform":          "qr",
        "account_age":       DEFAULT_AGE,
        "posting_frequency": DEFAULT_FREQ,
        **result,
    }, is_mock=MOCK_MODE)

    return {
        "qr_content":   qr_content,
        "content_type": classified["type"],
        "platform":     classified["platform"],
        "note":         classified["note"],
        "url":          classified.get("url"),
        "original_url": classified.get("original_url"),
        "used_redirect": classified.get("used_redirect", False),
        "scan_text":    scan_text,
        "rejected":     False,
        "is_duplicate": False,
        **result,
    }

@app.post("/predict")
@limiter.limit("30/minute")
def predict(req: PredictRequest, request: Request):
    # Check for duplicate before running the model
    existing = find_duplicate(
        req.text, req.platform, req.account_age, req.posting_frequency
    )
    if existing:
        # Return cached result — model not invoked, database not re-written
        return {
            "label":           existing.get("label", -1),
            "verdict":         existing.get("verdict", ""),
            "confidence":      existing.get("confidence", ""),
            "scam_prob":       existing.get("scam_prob", ""),
            "legit_prob":      existing.get("legit_prob", ""),
            "platform":        existing.get("platform", req.platform),
            "is_mock":         bool(existing.get("is_mock", 0)),
            "is_duplicate":    True,
            "duplicate_count": existing.get("duplicate_count", 1),
        }

    # New input — run model and save
    result = mock_predict(req) if MOCK_MODE else real_predict(req)
    result["is_duplicate"] = False
    save_detection({**req.dict(), **result}, is_mock=MOCK_MODE)
    return result

@app.get("/detections")
@limiter.limit("60/minute")
def get_detections(request: Request, limit: int = 100, platform: Optional[str] = None):
    with get_db() as conn:
        if platform:
            # Platform is encrypted — fetch all and filter after decryption
            rows = conn.execute(
                "SELECT * FROM detections ORDER BY id DESC LIMIT 500"
            ).fetchall()
            result = [decrypt_row(dict(r)) for r in rows]
            result = [r for r in result if r["platform"] == platform][:limit]
        else:
            rows = conn.execute(
                "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            result = [decrypt_row(dict(r)) for r in rows]
    return result

@app.get("/stats")
@limiter.limit("60/minute")
def get_stats(request: Request):
    today = datetime.date.today().isoformat()
    with get_db() as conn:
        # Single optimized query for all counts
        row = conn.execute("""
            SELECT
                COUNT(*)                                      AS total,
                SUM(CASE WHEN label=1 THEN 1 ELSE 0 END)     AS scam,
                SUM(CASE WHEN label=0 THEN 1 ELSE 0 END)     AS legit,
                SUM(CASE WHEN timestamp LIKE ? THEN 1 ELSE 0 END) AS today_ct
            FROM detections
        """, (f"{today}%",)).fetchone()
        total    = row["total"]    or 0
        scam     = row["scam"]     or 0
        legit    = row["legit"]    or 0
        today_ct = row["today_ct"] or 0

        # Platform counts — decrypt platform field and count
        all_rows = conn.execute(
            "SELECT platform FROM detections"
        ).fetchall()

    fb = sum(1 for r in all_rows if decrypt(r["platform"]) == "facebook")
    tw = sum(1 for r in all_rows if decrypt(r["platform"]) == "twitter")

    return {
        "total_detections": total,
        "scam_count":       scam,
        "legit_count":      legit,
        "scam_rate":        f"{(scam/total*100):.1f}%" if total > 0 else "0%",
        "facebook_total":   fb,
        "twitter_total":    tw,
        "detections_today": today_ct,
        "mock_mode":        MOCK_MODE,
    }

@app.delete("/detections/clear")
def clear_detections():
    with get_db() as conn:
        conn.execute("DELETE FROM detections")
        conn.commit()
    return {"message": "All detections cleared."}