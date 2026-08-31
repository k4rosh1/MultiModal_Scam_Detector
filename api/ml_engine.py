import os
import torch
import torch.nn as nn
import numpy as np
import config
from schemas import PredictRequest

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

class TextOnlyBaseline(nn.Module):
    def __init__(self, bert_model_name):
        super().__init__()
        from transformers import AutoModel
        self.bert       = AutoModel.from_pretrained(bert_model_name)
        self.classifier = nn.Linear(768, 2)

    def forward(self, input_ids, attention_mask):
        bert_out      = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = bert_out.last_hidden_state[:, 0, :]
        return self.classifier(cls_embedding)

tokenizer       = None
scaler          = None
model           = None
text_only_model = None

if not config.MOCK_MODE:
    try:
        import joblib
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(config.MODEL_DIR)
        scaler    = joblib.load(os.path.join(config.MODEL_DIR, "scaler.pkl"))
        model     = EarlyFusionScamDetector(bert_model_name="bert-base-multilingual-cased")
        model.load_state_dict(
            torch.load(os.path.join(config.MODEL_DIR, "model.pt"), map_location=config.DEVICE),
            strict=False
        )
        model.to(config.DEVICE)
        model.eval()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        config.MOCK_MODE = True

    text_only_path = os.path.join(config.MODEL_DIR, "text_only_model.pt")
    if os.path.exists(text_only_path):
        try:
            text_only_model = TextOnlyBaseline(bert_model_name="bert-base-multilingual-cased")
            text_only_model.load_state_dict(
                torch.load(text_only_path, map_location=config.DEVICE),
                strict=False
            )
            text_only_model.to(config.DEVICE)
            text_only_model.eval()
        except Exception:
            text_only_model = None

def mock_predict(req: PredictRequest) -> dict:
    text  = req.text.lower()
    score = 0
    scam_keywords = ["kumita", "pesos", "₱", "gcash", "dm mo", "libre", "free", "promo", "raffle", "invest", "click", "bit.ly", "tinyurl", "congratulations", "nanalo", "limited", "urgent", "verify"]
    for kw in scam_keywords:
        if kw in text: score += 15
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

UNCERTAIN_THRESHOLD = 75.0  # Below this confidence → Uncertain / Out of Context

UNCERTAIN_EXPLANATION = (
    "The AI model is not confident enough to classify this text as either a scam or legitimate. "
    "This usually means the input does not match typical social media post patterns found in the training data. "
    "The text may be out of context, too short, or unrelated to online scam content."
)

def real_predict(req: PredictRequest) -> dict:
    enc = tokenizer(req.text, max_length=config.MAX_LEN, padding='max_length', truncation=True, return_tensors='pt')
    input_ids      = enc['input_ids'].to(config.DEVICE)
    attention_mask = enc['attention_mask'].to(config.DEVICE)
    meta_raw    = np.array([[req.account_age, req.posting_frequency]], dtype=np.float32)
    meta_scaled = scaler.transform(meta_raw)
    metadata    = torch.tensor(meta_scaled, dtype=torch.float32).to(config.DEVICE)
    with torch.no_grad():
        logits = model(input_ids, attention_mask, metadata)
        probs  = torch.softmax(logits, dim=1)[0]
        label  = logits.argmax(dim=1).item()
    confidence = probs[label].item() * 100
    scam_prob  = probs[1].item() * 100
    legit_prob = probs[0].item() * 100

    # Fallout detection: if confidence is below threshold, mark as uncertain
    if confidence < UNCERTAIN_THRESHOLD:
        return {
            "label":       2,
            "verdict":     "UNCERTAIN",
            "confidence":  f"{confidence:.1f}%",
            "scam_prob":   f"{scam_prob:.1f}%",
            "legit_prob":  f"{legit_prob:.1f}%",
            "platform":    req.platform,
            "is_mock":     False,
            "explanation": UNCERTAIN_EXPLANATION,
        }

    return {
        "label":       label,
        "verdict":     "SCAM" if label == 1 else "LEGITIMATE",
        "confidence":  f"{confidence:.1f}%",
        "scam_prob":   f"{scam_prob:.1f}%",
        "legit_prob":  f"{legit_prob:.1f}%",
        "platform":    req.platform,
        "is_mock":     False,
        "explanation": "The text contains strong indicators of a scam based on language patterns and metadata analysis." if label == 1 else "The text appears to be a normal, legitimate social media post with no significant scam indicators detected.",
    }

def real_predict_text_only(text: str, platform: str = "qr") -> dict:
    enc = tokenizer(text, max_length=config.MAX_LEN, padding='max_length', truncation=True, return_tensors='pt')
    input_ids      = enc['input_ids'].to(config.DEVICE)
    attention_mask = enc['attention_mask'].to(config.DEVICE)
    with torch.no_grad():
        logits = text_only_model(input_ids, attention_mask)
        probs  = torch.softmax(logits, dim=1)[0]
        label  = logits.argmax(dim=1).item()
    confidence = probs[label].item() * 100
    scam_prob  = probs[1].item() * 100
    legit_prob = probs[0].item() * 100

    if confidence < UNCERTAIN_THRESHOLD:
        return {
            "label":       2,
            "verdict":     "UNCERTAIN",
            "confidence":  f"{confidence:.1f}%",
            "scam_prob":   f"{scam_prob:.1f}%",
            "legit_prob":  f"{legit_prob:.1f}%",
            "platform":    platform,
            "is_mock":     False,
            "model_used":  "text_only",
            "explanation": UNCERTAIN_EXPLANATION,
        }

    return {
        "label":       label,
        "verdict":     "SCAM" if label == 1 else "LEGITIMATE",
        "confidence":  f"{confidence:.1f}%",
        "scam_prob":   f"{scam_prob:.1f}%",
        "legit_prob":  f"{legit_prob:.1f}%",
        "platform":    platform,
        "is_mock":     False,
        "model_used":  "text_only",
        "explanation": "The text contains strong indicators of a scam based on language patterns and metadata analysis." if label == 1 else "The text appears to be a normal, legitimate social media post with no significant scam indicators detected.",
    }