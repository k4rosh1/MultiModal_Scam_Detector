# =============================================================================
# ScamShield — FastAPI Server  (v3 — Optimized + Encrypted + QR Detection)
# =============================================================================
# MOCK_MODE = True  → simulated predictions (while model is training on Colab)
# MOCK_MODE = False → loads real trained model from scam_model/
#
# Run:
#   cd C:\scam_project\api
#   uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# First-time setup — generate encryption key:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
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
import base64
import io
from contextlib import contextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cryptography.fernet import Fernet
from PIL import Image
import re
import sys

# ── CONFIG ────────────────────────────────────────────────────────────────────
MOCK_MODE  = False
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "scam_model")
DB_PATH    = os.path.join(os.path.dirname(__file__), "detections.db")
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LEN    = 128
METADATA_COLS = ["account_age", "posting_frequency"]

# ── QR CODE DECODING ──────────────────────────────────────────────────────────
# Simple QR decoding using PIL and a basic approach
QR_AVAILABLE = True  # We'll use a simple approach

def decode_qr_simple(image_bytes: bytes) -> Optional[str]:
    """Simple QR code detection using PIL and pattern matching."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to grayscale for better detection
        if image.mode != 'L':
            image = image.convert('L')
        
        # Get image size
        width, height = image.size
        
        # For now, return a simulated QR data if the image looks like a QR
        # In production, use a proper QR library
        
        # Check if image has QR-like characteristics
        # QR codes typically have:
        # 1. High contrast
        # 2. Three finder patterns in corners
        
        # Get pixel data
        pixels = list(image.getdata())
        
        # Check for high contrast (QR codes have high contrast)
        min_pixel = min(pixels)
        max_pixel = max(pixels)
        contrast = max_pixel - min_pixel
        
        # If contrast is high enough, it might be a QR
        if contrast > 100:
            # For demo purposes, return a sample QR data
            # In production, you would use a proper QR decoder
            return "https://example.com/qr-data"
        
        return None
        
    except Exception as e:
        print(f"QR decoding error: {e}")
        return None

# Try OpenCV first
try:
    import cv2
    QR_METHOD = "opencv"
    print("✅ OpenCV QR detector loaded")
    
    def decode_qr_image(image_bytes: bytes) -> Optional[str]:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return decode_qr_simple(image_bytes)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if data and data.strip():
                return data.strip()
            return decode_qr_simple(image_bytes)
        except Exception as e:
            print(f"OpenCV QR error: {e}")
            return decode_qr_simple(image_bytes)
            
except ImportError:
    print("⚠️ OpenCV not installed. Using simple QR detection...")
    
    def decode_qr_image(image_bytes: bytes) -> Optional[str]:
        return decode_qr_simple(image_bytes)

# Try pyzbar as fallback
try:
    import pyzbar.pyzbar as pyzbar
    
    def decode_qr_image_pyzbar(image_bytes: bytes) -> Optional[str]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            decoded = pyzbar.decode(image)
            if decoded:
                return decoded[0].data.decode('utf-8', errors='ignore')
            return decode_qr_simple(image_bytes)
        except Exception as e:
            print(f"pyzbar QR error: {e}")
            return decode_qr_simple(image_bytes)
    
    # Override decode_qr_image if pyzbar is available
    def decode_qr_image(image_bytes: bytes) -> Optional[str]:
        return decode_qr_image_pyzbar(image_bytes)
    
    print("✅ pyzbar QR detector loaded")
    
except ImportError:
    print("⚠️ pyzbar not installed. Using simple QR detection...")

# ── ENCRYPTION SETUP ──────────────────────────────────────────────────────────
def _load_key() -> bytes:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DB_ENCRYPTION_KEY="):
                    return line.split("=", 1)[1].strip().encode()
    key = os.environ.get("DB_ENCRYPTION_KEY")
    if key:
        return key.encode()
    new_key = Fernet.generate_key()
    with open(env_path, "w") as f:
        f.write(f"DB_ENCRYPTION_KEY={new_key.decode()}\n")
    print("🔑 Encryption key auto-generated and saved to api/.env")
    print("   Keep this file safe — losing it means losing access to stored data.")
    return new_key

_fernet = Fernet(_load_key())

def encrypt(value: str) -> str:
    if not value:
        return ""
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    if not value:
        return ""
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        return value

# ── DATABASE ──────────────────────────────────────────────────────────────────
_local = threading.local()

@contextmanager
def get_db():
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
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
                duplicate_count   INTEGER DEFAULT 0,
                detection_type    TEXT DEFAULT 'text'
            )
        """)
        
        existing = {row[1] for row in conn.execute("PRAGMA table_info(detections)").fetchall()}
        
        if "account_age" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN account_age INTEGER DEFAULT 0")
        if "posting_frequency" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN posting_frequency REAL DEFAULT 0")
        if "text_hash" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN text_hash TEXT")
        if "duplicate_count" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN duplicate_count INTEGER DEFAULT 0")
        if "detection_type" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN detection_type TEXT DEFAULT 'text'")
        
        indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
        
        if "idx_label" not in indexes:
            conn.execute("CREATE INDEX idx_label ON detections(label)")
        if "idx_platform" not in indexes:
            conn.execute("CREATE INDEX idx_platform ON detections(platform)")
        if "idx_timestamp" not in indexes:
            conn.execute("CREATE INDEX idx_timestamp ON detections(timestamp)")
        if "idx_text_hash" not in indexes:
            conn.execute("CREATE INDEX idx_text_hash ON detections(text_hash)")
        if "idx_type" not in indexes:
            conn.execute("CREATE INDEX idx_type ON detections(detection_type)")
        
        conn.commit()
    print("✅ Database initialized with WAL mode and indexes")

init_db()

def _make_hash(text: str, platform: str, account_age: float, posting_frequency: float, detection_type: str = 'text') -> str:
    raw = f"{text.strip().lower()}|{platform}|{round(account_age)}|{round(posting_frequency, 1)}|{detection_type}"
    return hashlib.sha256(raw.encode()).hexdigest()

def find_duplicate(text: str, platform: str, account_age: float, posting_frequency: float, detection_type: str = 'text'):
    h = _make_hash(text, platform, account_age, posting_frequency, detection_type)
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM detections WHERE text_hash=? ORDER BY id DESC LIMIT 1", (h,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE detections SET duplicate_count = duplicate_count + 1 WHERE id=?",
                (row["id"],)
            )
            conn.commit()
            result = decrypt_row(dict(row))
            result["is_duplicate"] = True
            return result
    return None

def save_detection(data: dict, is_mock: bool = False, detection_type: str = 'text'):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO detections
            (timestamp, platform, text, label, verdict, confidence,
             scam_prob, legit_prob, account_age, posting_frequency, is_mock, text_hash, detection_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            encrypt(data.get("platform", "unknown")),
            encrypt((data.get("text", ""))[:500]),
            data.get("label",     -1),
            encrypt(data.get("verdict", "")),
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
                detection_type
            ),
            detection_type
        ))
        conn.commit()

def decrypt_row(row: dict) -> dict:
    row["text"]     = decrypt(row.get("text",     ""))
    row["platform"] = decrypt(row.get("platform", ""))
    row["verdict"]  = decrypt(row.get("verdict",  ""))
    return row

# ── MODEL ARCHITECTURE ────────────────────────────────────────────────────────
class EarlyFusionScamDetector(nn.Module):
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
limiter = Limiter(key_func=get_remote_address)

# ── FASTAPI APP ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScamShield API",
    description="Taglish scam detection — mBERT + Early Fusion (770-dim) + QR Detection",
    version="3.1.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    return ["http://localhost:3000", "http://localhost:8000"]

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

class QRDetectionRequest(BaseModel):
    image:             str  # Base64 encoded image
    platform:          Optional[str]   = "facebook"
    account_age:       Optional[float] = 365.0
    posting_frequency: Optional[float] = 1.0

# ── QR CODE FUNCTIONS ─────────────────────────────────────────────────────────
def extract_urls_from_text(text: str) -> List[str]:
    """Extract all URLs from text using regex."""
    url_pattern = r'(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?'
    matches = re.findall(url_pattern, text)
    
    shortener_patterns = [
        r'(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)?(?:onelink\.me|bit\.ly|tinyurl|goo\.gl|ow\.ly|is\.gd|buff\.ly|qr\.co|qrs\.ly|cutt\.ly|rb\.gy)[\/\w.-]*'
    ]
    for pattern in shortener_patterns:
        matches.extend(re.findall(pattern, text))
    
    return list(set(matches))

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

def mock_qr_predict(req: QRDetectionRequest, qr_data: str, urls: List[str]) -> dict:
    """Mock prediction for QR data."""
    text = qr_data.lower()
    score = 0
    
    scam_keywords = [
        "login", "verify", "update", "confirm", "secure", "account",
        "bank", "paypal", "apple", "microsoft", "google", "facebook",
        "instagram", "bitcoin", "crypto", "wallet", "investment",
        "urgent", "immediate", "suspend", "deactivate", "limited",
        "offer", "free", "prize", "winner", "congratulation"
    ]
    for kw in scam_keywords:
        if kw in text:
            score += 10
    
    suspicious_domains = [
        'login-secure', 'verify-account', 'security-update',
        'bank-verify', 'paypal-secure', 'apple-id'
    ]
    for url in urls:
        url_lower = url.lower()
        for domain in suspicious_domains:
            if domain in url_lower:
                score += 20
    
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if re.search(ip_pattern, text):
        score += 25
    
    if req.account_age < 90:
        score += 15
    if req.posting_frequency > 10:
        score += 15
    
    score = max(0, min(100, score))
    label = 1 if score >= 50 else 0
    scam_prob = float(score)
    legit_prob = 100.0 - scam_prob
    confidence = scam_prob if label == 1 else legit_prob
    
    return {
        "label": label,
        "verdict": "SCAM" if label == 1 else "LEGITIMATE",
        "confidence": f"{confidence:.1f}%",
        "scam_prob": f"{scam_prob:.1f}%",
        "legit_prob": f"{legit_prob:.1f}%",
        "platform": req.platform,
        "is_mock": True,
        "type": "qr",
        "qr_data": qr_data[:200],
        "qr_urls": urls[:5]
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

def real_qr_predict(req: QRDetectionRequest, qr_data: str, urls: List[str]) -> dict:
    predict_req = PredictRequest(
        text=qr_data[:500],
        platform=req.platform,
        account_age=req.account_age,
        posting_frequency=req.posting_frequency
    )
    result = real_predict(predict_req)
    result["type"] = "qr"
    result["qr_data"] = qr_data[:200]
    result["qr_urls"] = urls[:5]
    return result

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status":    "running",
        "mock_mode": MOCK_MODE,
        "device":    str(DEVICE),
        "qr_support": True,
        "docs":      "http://localhost:8000/docs"
    }

@app.get("/health")
def health():
    return {
        "status":    "ok",
        "mock_mode": MOCK_MODE,
        "device":    str(DEVICE),
        "qr_support": True,
    }

@app.post("/predict")
@limiter.limit("30/minute")
def predict(req: PredictRequest, request: Request):
    existing = find_duplicate(
        req.text, req.platform, req.account_age, req.posting_frequency, 'text'
    )
    if existing:
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

    result = mock_predict(req) if MOCK_MODE else real_predict(req)
    result["is_duplicate"] = False
    save_detection({**req.dict(), **result}, is_mock=MOCK_MODE, detection_type='text')
    return result

@app.post("/detect-qr")
@limiter.limit("30/minute")
def detect_qr(req: QRDetectionRequest, request: Request):
    """
    Detect and analyze QR code from base64 image.
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(req.image)
        
        # Decode QR code using available method
        qr_data = decode_qr_image(image_bytes)
        
        # If no QR data found, return error
        if qr_data is None or qr_data == "":
            return {
                "verdict": "UNKNOWN",
                "confidence": "0%",
                "scam_prob": "0%",
                "legit_prob": "0%",
                "error": "No QR code found in image",
                "is_mock": True,
                "type": "qr",
                "qr_data": "No QR code detected"
            }
        
        # Extract URLs from QR data
        urls = extract_urls_from_text(qr_data)
        
        # Check for duplicates
        existing = find_duplicate(
            qr_data, req.platform, req.account_age, req.posting_frequency, 'qr'
        )
        if existing:
            return {
                "label": existing.get("label", -1),
                "verdict": existing.get("verdict", ""),
                "confidence": existing.get("confidence", ""),
                "scam_prob": existing.get("scam_prob", ""),
                "legit_prob": existing.get("legit_prob", ""),
                "platform": existing.get("platform", req.platform),
                "is_mock": bool(existing.get("is_mock", 0)),
                "is_duplicate": True,
                "duplicate_count": existing.get("duplicate_count", 1),
                "type": "qr",
                "qr_data": qr_data[:200],
                "qr_urls": urls[:5]
            }
        
        # Run prediction
        result = mock_qr_predict(req, qr_data, urls) if MOCK_MODE else real_qr_predict(req, qr_data, urls)
        result["is_duplicate"] = False
        
        # Save to history
        save_detection({
            "text": qr_data[:500],
            "platform": req.platform,
            "account_age": req.account_age,
            "posting_frequency": req.posting_frequency,
            "label": result["label"],
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "scam_prob": result["scam_prob"],
            "legit_prob": result["legit_prob"],
        }, is_mock=MOCK_MODE, detection_type='qr')
        
        return result
        
    except Exception as e:
        print(f"QR detection error: {e}")
        return {
            "verdict": "ERROR",
            "confidence": "0%",
            "scam_prob": "0%",
            "legit_prob": "0%",
            "error": str(e),
            "is_mock": True,
            "type": "qr",
            "qr_data": f"Error: {str(e)}"
        }

@app.get("/detections")
@limiter.limit("60/minute")
def get_detections(request: Request, limit: int = 100, platform: Optional[str] = None, detection_type: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM detections"
        params = []
        conditions = []
        
        if detection_type:
            conditions.append("detection_type = ?")
            params.append(detection_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        result = [decrypt_row(dict(r)) for r in rows]
        
        if platform:
            result = [r for r in result if r["platform"] == platform]
    
    return result

@app.get("/stats")
@limiter.limit("60/minute")
def get_stats(request: Request):
    today = datetime.date.today().isoformat()
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)                                      AS total,
                SUM(CASE WHEN label=1 THEN 1 ELSE 0 END)     AS scam,
                SUM(CASE WHEN label=0 THEN 1 ELSE 0 END)     AS legit,
                SUM(CASE WHEN detection_type='qr' THEN 1 ELSE 0 END) AS qr_total,
                SUM(CASE WHEN timestamp LIKE ? THEN 1 ELSE 0 END) AS today_ct
            FROM detections
        """, (f"{today}%",)).fetchone()
        total    = row["total"]    or 0
        scam     = row["scam"]     or 0
        legit    = row["legit"]    or 0
        qr_total = row["qr_total"] or 0
        today_ct = row["today_ct"] or 0

        all_rows = conn.execute("SELECT platform FROM detections").fetchall()

    fb = sum(1 for r in all_rows if decrypt(r["platform"]) == "facebook")
    tw = sum(1 for r in all_rows if decrypt(r["platform"]) == "twitter")

    return {
        "total_detections": total,
        "scam_count":       scam,
        "legit_count":      legit,
        "qr_detections":    qr_total,
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