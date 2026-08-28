from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
import config
from schemas import PredictRequest
import qr_utils
import ml_engine
import database

router = APIRouter()

@router.post("/scan-qr")
@config.limiter.limit("20/minute")
async def scan_qr(request: Request, file: UploadFile = File(...), session_id: str = Form(None)):
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp", "image/gif"}
    content_type  = (file.content_type or "").lower()
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PNG, JPG, WEBP, or BMP image.")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 10MB.")

    try:
        qr_content = qr_utils.decode_qr_from_image(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    classified = qr_utils.classify_qr_content(qr_content)

    if classified["is_media"] or classified.get("is_payment"):
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

    scan_text = classified["scan_text"]
    if not scan_text or not scan_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract scannable text from QR content.")

    DEFAULT_AGE  = 365.0
    DEFAULT_FREQ = 1.0

    existing = database.find_duplicate(scan_text, "qr", DEFAULT_AGE, DEFAULT_FREQ, session_id)
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

    class _QRRequest:
        text              = scan_text
        platform          = "qr"
        account_age       = DEFAULT_AGE
        posting_frequency = DEFAULT_FREQ

    qr_req = _QRRequest()

    if config.MOCK_MODE:
        result = ml_engine.mock_predict(qr_req)
    elif ml_engine.text_only_model is not None:
        result = ml_engine.real_predict_text_only(scan_text, platform="qr")
    else:
        result = ml_engine.real_predict(qr_req)

    database.save_detection({
        "text":              scan_text,
        "platform":          "qr",
        "account_age":       DEFAULT_AGE,
        "posting_frequency": DEFAULT_FREQ,
        "session_id":        session_id,
        **result,
    }, is_mock=config.MOCK_MODE)

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

@router.post("/predict")
@config.limiter.limit("30/minute")
def predict(req: PredictRequest, request: Request):
    existing = database.find_duplicate(req.text, req.platform, req.account_age, req.posting_frequency, req.session_id)
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

    result = ml_engine.mock_predict(req) if config.MOCK_MODE else ml_engine.real_predict(req)
    result["is_duplicate"] = False
    database.save_detection({**req.dict(), **result}, is_mock=config.MOCK_MODE)
    return result