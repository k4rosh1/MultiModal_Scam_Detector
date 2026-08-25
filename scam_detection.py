# =============================================================================
# Multi-Modal Scam Detection System
# mBERT (Multilingual BERT) + Metadata — Early Fusion Architecture
# =============================================================================

# ── IMPORTS ───────────────────────────────────────────────────────────────────
import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score, classification_report)
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import joblib
import warnings
warnings.filterwarnings("ignore")


# ── CONFIG ────────────────────────────────────────────────────────────────────
MODEL_NAME    = "bert-base-multilingual-cased"  # mBERT — supports Tagalog + English
DEVICE        = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LEN       = 128       # maximum token sequence length
BATCH_SIZE    = 16
EPOCHS        = 5         # fixed 5 epochs as per spec
LR            = 2e-5      # AdamW learning rate
METADATA_COLS = ["account_age", "posting_frequency"]   # only 2 metadata features


# ── DATASET CLASS ─────────────────────────────────────────────────────────────
class ScamDataset(Dataset):
    """
    PyTorch Dataset that tokenizes text and returns metadata + label.
    """
    def __init__(self, texts, metadata, labels, tokenizer, max_len):
        self.texts     = texts
        self.metadata  = metadata
        self.labels    = labels
        self.tokenizer = tokenizer
        self.max_len   = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            str(self.texts[idx]),
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids':      enc['input_ids'].squeeze(0),
            'attention_mask': enc['attention_mask'].squeeze(0),
            'metadata':       torch.tensor(self.metadata[idx], dtype=torch.float32),
            'label':          torch.tensor(self.labels[idx],   dtype=torch.long),
        }


# ── MODEL ARCHITECTURE ────────────────────────────────────────────────────────
class EarlyFusionScamDetector(nn.Module):
    """
    Multi-modal early fusion model.
    Fuses 768-dim text embedding with 2-dim metadata.
    """
    def __init__(self, bert_model_name, meta_dropout_p=0.15):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model_name)

        # 768 (text) + 2 (metadata) = 770-dim
        self.classifier = nn.Linear(768 + 2, 2)

        self.meta_dropout_p = meta_dropout_p

    def forward(self, input_ids, attention_mask, metadata, training=False):
        bert_out      = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = bert_out.last_hidden_state[:, 0, :]   # [batch, 768]

        # Modality dropout
        if training:
            batch_size = cls_embedding.size(0)
            drop_mask  = torch.rand(batch_size, device=cls_embedding.device) < self.meta_dropout_p
            if drop_mask.any():
                cls_embedding = cls_embedding.clone()
                cls_embedding[drop_mask] = 0.0

        fused = torch.cat([cls_embedding, metadata], dim=1)  # [batch, 770]
        return self.classifier(fused)


# ── TRAINING FUNCTION ────────────────────────────────────────────────
def train_model(model, train_loader, val_loader, model_name="Model"):
    model.to(DEVICE)

    optimizer = torch.optim.AdamW([
        {"params": model.bert.parameters(),       "lr": LR},
        {"params": model.classifier.parameters(), "lr": 1e-3},
    ], weight_decay=0.01)

    loss_fn   = nn.CrossEntropyLoss()
    history    = {"train_loss": [], "val_loss": [], "val_acc": [], "val_f1": []}
    best_f1    = 0.0
    best_state = None

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for batch in tqdm(train_loader, desc=f"[{model_name}] Epoch {epoch+1}/{EPOCHS} Train"):
            input_ids      = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            metadata       = batch['metadata'].to(DEVICE)
            labels         = batch['label'].to(DEVICE)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask, metadata, training=True)
            loss   = loss_fn(logits, labels)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        model.eval()
        val_loss, all_preds, all_labels = 0, [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids      = batch['input_ids'].to(DEVICE)
                attention_mask = batch['attention_mask'].to(DEVICE)
                metadata       = batch['metadata'].to(DEVICE)
                labels         = batch['label'].to(DEVICE)

                logits    = model(input_ids, attention_mask, metadata)
                loss      = loss_fn(logits, labels)
                val_loss += loss.item()
                preds     = logits.argmax(dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.cpu().numpy())

        avg_val_loss = val_loss / len(val_loader)
        val_acc      = accuracy_score(all_labels, all_preds)
        val_f1       = f1_score(all_labels, all_preds)

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)
        history["val_acc"].append(val_acc)
        history["val_f1"].append(val_f1)

        print(f"   Epoch {epoch+1}/{EPOCHS}: train_loss={avg_train_loss:.4f} | "
              f"val_loss={avg_val_loss:.4f} | val_acc={val_acc:.4f} | val_f1={val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1    = val_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            os.makedirs("./checkpoints", exist_ok=True)
            torch.save({
                'epoch':            epoch + 1,
                'model_state_dict': best_state,
                'val_f1':           best_f1,
                'val_acc':          val_acc,
            }, f"./checkpoints/{model_name}_best.pt")
            print(f"   💾 Best checkpoint saved! Epoch {epoch+1} | F1={best_f1:.4f}")

    if best_state:
        model.load_state_dict(best_state)

    return history


# ── EVALUATION FUNCTION ──────────────────────────────────────────────
def evaluate_model(model, test_loader, model_name="Model"):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in test_loader:
            input_ids      = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            metadata       = batch['metadata'].to(DEVICE)
            labels         = batch['label'].to(DEVICE)

            logits = model(input_ids, attention_mask, metadata)
            preds  = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    acc  = accuracy_score(all_labels,  all_preds)
    prec = precision_score(all_labels, all_preds)
    rec  = recall_score(all_labels,    all_preds)
    f1   = f1_score(all_labels,        all_preds)

    print(f"\n{'='*55}")
    print(f"  {model_name} — Test Set Evaluation")
    print(f"{'='*55}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"\n{classification_report(all_labels, all_preds, target_names=['Legitimate','Scam'])}")

    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
            "preds": all_preds, "labels": all_labels}


# ── MAIN EXECUTION ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Using device: {DEVICE}")

    print("\n[1/7] Loading dataset...")
    df = pd.read_csv("merged_real_dataset.csv")
    print(f"   Total samples: {len(df)}  |  Scam: {df['label'].sum()}  |  Legit: {(df['label']==0).sum()}")

    X_text = df["text"].values
    X_meta = df[METADATA_COLS].values.astype(np.float32)
    y      = df["label"].values

    print("\n[2/7] Splitting data (80% train / 10% val / 10% test)...")
    X_text_train, X_text_temp, X_meta_train, X_meta_temp, y_train, y_temp = train_test_split(
        X_text, X_meta, y, test_size=0.20, random_state=42, stratify=y
    )
    X_text_val, X_text_test, X_meta_val, X_meta_test, y_val, y_test = train_test_split(
        X_text_temp, X_meta_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    print(f"   Train: {len(y_train)}  |  Val: {len(y_val)}  |  Test: {len(y_test)}")

    print("\n[3/7] Normalizing metadata with MinMaxScaler...")
    scaler         = MinMaxScaler()
    X_meta_train   = scaler.fit_transform(X_meta_train)
    X_meta_val     = scaler.transform(X_meta_val)
    X_meta_test    = scaler.transform(X_meta_test)

    os.makedirs("./scam_model", exist_ok=True)
    joblib.dump(scaler, "./scam_model/scaler.pkl")
    print("   ✅ MinMaxScaler fitted and saved to ./scam_model/scaler.pkl")

    print(f"\n[4/7] Loading mBERT tokenizer: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained("./scam_model")
    print("   ✅ Tokenizer saved to ./scam_model/")

    train_loader = DataLoader(ScamDataset(X_text_train, X_meta_train, y_train, tokenizer, MAX_LEN), batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(ScamDataset(X_text_val,   X_meta_val,   y_val,   tokenizer, MAX_LEN), batch_size=BATCH_SIZE)
    test_loader  = DataLoader(ScamDataset(X_text_test,  X_meta_test,  y_test,  tokenizer, MAX_LEN), batch_size=BATCH_SIZE)

    print("\n[5/7] Building and Training Proposed Model (Early Fusion)...")
    multimodal_model = EarlyFusionScamDetector(bert_model_name=MODEL_NAME)
    multimodal_history = train_model(multimodal_model, train_loader, val_loader, "ProposedModel")

    torch.save(multimodal_model.state_dict(), "./scam_model/model.pt")
    print("\n✅ Model saved to ./scam_model/model.pt")

    print("\n[6/7] Evaluating model on held-out test set...")
    results = evaluate_model(multimodal_model, test_loader, "Proposed Multi-Modal System")

    print("\n[7/7] Generating Plots...")
    os.makedirs("./results", exist_ok=True)
    epochs_x = list(range(1, EPOCHS + 1))

    # Training curves
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("Proposed Model — Training Curves", fontsize=13, fontweight='bold')

    axes[0].plot(epochs_x, multimodal_history["train_loss"], label="Train Loss", marker='o')
    axes[0].plot(epochs_x, multimodal_history["val_loss"],   label="Val Loss",   marker='s')
    axes[0].set_title("Loss over Epochs")
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Loss"); axes[0].legend()

    axes[1].plot(epochs_x, multimodal_history["val_acc"], label="Val Accuracy", marker='o', color='green')
    axes[1].plot(epochs_x, multimodal_history["val_f1"],  label="Val F1",       marker='s', color='orange')
    axes[1].set_title("Accuracy & F1 over Epochs")
    axes[1].set_xlabel("Epoch"); axes[1].legend()

    plt.tight_layout()
    plt.savefig("./results/training_curves.png", dpi=150)
    print("   ✅ Training curves saved to ./results/training_curves.png")

    # Confusion matrix
    plt.figure(figsize=(6, 5))
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(results["labels"], results["preds"])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=["Legit","Scam"], yticklabels=["Legit","Scam"])
    plt.title("Confusion Matrix — Proposed Model")
    plt.ylabel("True"); plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig("./results/confusion_matrix.png", dpi=150)
    print("   ✅ Confusion matrix saved to ./results/confusion_matrix.png")

    print("\n✅ Pipeline complete!")