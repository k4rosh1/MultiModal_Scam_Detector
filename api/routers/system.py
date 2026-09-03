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
def get_detections(request: Request, limit: int = 100, platform: Optional[str] = None, session_id: Optional[str] = None):
    if not session_id:
        return []

    with database.get_db() as conn:
        query = "SELECT * FROM detections WHERE session_id = ?"
        params = [session_id]
        
        query += " ORDER BY id DESC LIMIT 500"
        rows = conn.execute(query, params).fetchall()
        result = [database.decrypt_row(dict(r)) for r in rows]
        if platform:
            result = [r for r in result if r["platform"] == platform][:limit]
        else:
            result = result[:limit]
    return result

@router.get("/stats")
@config.limiter.limit("60/minute")
def get_stats(request: Request, session_id: Optional[str] = None):
    if not session_id:
        return {
            "total_detections": 0, "scam_count": 0, "legit_count": 0,
            "scam_rate": "0%", "facebook_total": 0, "twitter_total": 0,
            "detections_today": 0, "mock_mode": config.MOCK_MODE
        }

    today = datetime.date.today().isoformat()
    with database.get_db() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)                                      AS total,
                SUM(CASE WHEN label=1 THEN 1 ELSE 0 END)     AS scam,
                SUM(CASE WHEN label=0 THEN 1 ELSE 0 END)     AS legit,
                SUM(CASE WHEN timestamp LIKE ? THEN 1 ELSE 0 END) AS today_ct
            FROM detections
            WHERE session_id = ?
        """, (f"{today}%", session_id)).fetchone()
        
        all_rows = conn.execute("SELECT platform FROM detections WHERE session_id = ?", (session_id,)).fetchall()
        
        total    = row["total"]    or 0
        scam     = row["scam"]     or 0
        legit    = row["legit"]    or 0
        today_ct = row["today_ct"] or 0

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



import os
import json
import config

@router.get("/metrics")
def get_metrics(model_type: Optional[str] = "multimodal"):
    if model_type == "baseline":
        metrics_path = os.path.join(config.MODEL_DIR, "baseline_metrics.json")
    else:
        metrics_path = os.path.join(config.MODEL_DIR, "metrics.json")
        
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "total_samples": 0,
        "scam_samples": 0,
        "legit_samples": 0,
        "true_positives": 0,
        "true_negatives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "evaluation_date": "N/A"
    }