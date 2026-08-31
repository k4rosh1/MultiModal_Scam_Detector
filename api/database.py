import sqlite3
import threading
import datetime
import hashlib
from contextlib import contextmanager
import config

_local = threading.local()

@contextmanager
def get_db():
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
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
                duplicate_count   INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_label ON detections(label)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON detections(platform)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON detections(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_text_hash ON detections(text_hash)")
        
        existing = {row[1] for row in conn.execute("PRAGMA table_info(detections)").fetchall()}
        if "account_age" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN account_age INTEGER DEFAULT 0")
        if "posting_frequency" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN posting_frequency REAL DEFAULT 0")
        if "text_hash" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN text_hash TEXT")
        if "duplicate_count" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN duplicate_count INTEGER DEFAULT 0")
        if "explanation" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN explanation TEXT DEFAULT ''")
        if "session_id" not in existing:
            conn.execute("ALTER TABLE detections ADD COLUMN session_id TEXT")
        conn.commit()

def _make_hash(text: str, platform: str, account_age: float, posting_frequency: float) -> str:
    raw = f"{text.strip().lower()}|{platform}|{round(account_age)}|{round(posting_frequency, 1)}"
    return hashlib.sha256(raw.encode()).hexdigest()

def find_duplicate(text: str, platform: str, account_age: float, posting_frequency: float, session_id: str = None):
    h = _make_hash(text, platform, account_age, posting_frequency)
    with get_db() as conn:
        if session_id:
            row = conn.execute("SELECT * FROM detections WHERE text_hash=? AND session_id=? ORDER BY id DESC LIMIT 1", (h, session_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM detections WHERE text_hash=? ORDER BY id DESC LIMIT 1", (h,)).fetchone()
        if row:
            conn.execute("UPDATE detections SET duplicate_count = duplicate_count + 1 WHERE id=?", (row["id"],))
            conn.commit()
            result = decrypt_row(dict(row))
            result["is_duplicate"] = True
            return result
    return None

def save_detection(data: dict, is_mock: bool = False):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO detections
            (timestamp, platform, text, label, verdict, confidence,
             scam_prob, legit_prob, account_age, posting_frequency, is_mock, text_hash, explanation, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            config.encrypt(data.get("platform", "unknown")),
            config.encrypt((data.get("text", ""))[:500]),
            data.get("label",     -1),
            config.encrypt(data.get("verdict", "")),
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
            data.get("explanation", ""),
            data.get("session_id", None),
        ))
        conn.commit()

def decrypt_row(row: dict) -> dict:
    row["text"]     = config.decrypt(row.get("text",     ""))
    row["platform"] = config.decrypt(row.get("platform", ""))
    row["verdict"]  = config.decrypt(row.get("verdict",  ""))
    return row