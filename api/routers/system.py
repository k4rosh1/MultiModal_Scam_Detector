from fastapi import APIRouter, Request
from typing import Optional
import datetime
import config
import database

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status":    "ok",
        "mock_mode": config.MOCK_MODE,
        "device":    str(config.DEVICE),
    }

@router.get("/detections")
@config.limiter.limit("60/minute")
def get_detections(request: Request, limit: int = 100, platform: Optional[str] = None):
    with database.get_db() as conn:
        if platform:
            rows = conn.execute("SELECT * FROM detections ORDER BY id DESC LIMIT 500").fetchall()
            result = [database.decrypt_row(dict(r)) for r in rows]
            result = [r for r in result if r["platform"] == platform][:limit]
        else:
            rows = conn.execute("SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            result = [database.decrypt_row(dict(r)) for r in rows]
    return result

@router.get("/stats")
@config.limiter.limit("60/minute")
def get_stats(request: Request):
    today = datetime.date.today().isoformat()
    with database.get_db() as conn:
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

        all_rows = conn.execute("SELECT platform FROM detections").fetchall()

    fb = sum(1 for r in all_rows if config.decrypt(r["platform"]) == "facebook")
    tw = sum(1 for r in all_rows if config.decrypt(r["platform"]) == "twitter")

    return {
        "total_detections": total,
        "scam_count":       scam,
        "legit_count":      legit,
        "scam_rate":        f"{(scam/total*100):.1f}%" if total > 0 else "0%",
        "facebook_total":   fb,
        "twitter_total":    tw,
        "detections_today": today_ct,
        "mock_mode":        config.MOCK_MODE,
    }

@router.delete("/detections/clear")
def clear_detections():
    with database.get_db() as conn:
        conn.execute("DELETE FROM detections")
        conn.commit()
    return {"message": "All detections cleared."}