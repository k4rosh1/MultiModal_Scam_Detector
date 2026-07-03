import os
import torch
from cryptography.fernet import Fernet
from slowapi import Limiter
from slowapi.util import get_remote_address

MOCK_MODE  = False
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "scam_model")
DB_PATH    = os.path.join(os.path.dirname(__file__), "detections.db")
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LEN    = 128
METADATA_COLS = ["account_age", "posting_frequency"]

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
    return new_key

_fernet = Fernet(_load_key())

def encrypt(value: str) -> str:
    if not value: return ""
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    if not value: return ""
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        return value

limiter = Limiter(key_func=get_remote_address)

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
    return ["http://localhost:3000"]

ALLOWED_ORIGINS = _load_allowed_origins()