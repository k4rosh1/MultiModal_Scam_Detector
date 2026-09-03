import os
import sys
import argparse
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# Import architecture and dataset class from the main script
from scam_detection import EarlyFusionScamDetector, TextOnlyScamDetector, ScamDataset, MAX_LEN, DEVICE, MODEL_NAME, METADATA_COLS

def main():
    parser = argparse.ArgumentParser(description="Test Scam Detection Models")
    parser.add_argument("--model", type=str, choices=["multimodal", "baseline"], default="multimodal", help="Which model to test")
    args = parser.parse_args()

    print(f"Using device: {DEVICE}")
    print("\n[1/4] Loading hard_test_dataset.csv...")
    if not os.path.exists("hard_test_dataset.csv"):
        print("❌ Error: 'hard_test_dataset.csv' not found in current directory.")
        sys.exit(1)
        
    df = pd.read_csv("hard_test_dataset.csv")
    print(f"   Total test samples: {len(df)}  |  Scam: {df['label'].sum()}  |  Legit: {(df['label']==0).sum()}")

    X_text = df["text"].values
    X_meta = df[METADATA_COLS].values.astype(np.float32)
    y      = df["label"].values

    print("\n[2/4] Loading Pre-Trained Assets (Tokenizer, Scaler, Model)...")
    try:
        scaler = joblib.load("./scam_model/scaler.pkl")
        tokenizer = AutoTokenizer.from_pretrained("./scam_model")
        
        if args.model == "multimodal":
            model = EarlyFusionScamDetector(bert_model_name=MODEL_NAME)
            model.load_state_dict(torch.load("./scam_model/model.pt", map_location=DEVICE))
        else:
            model = TextOnlyScamDetector(bert_model_name=MODEL_NAME)
            model.load_state_dict(torch.load("./scam_model/baseline_model.pt", map_location=DEVICE))
            
        model.to(DEVICE)
        model.eval()
        print("   ✅ Assets loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading assets: {e}")
        print("   Did you train the model first by running scam_detection.py?")
        sys.exit(1)

    print("\n[3/4] Preparing DataLoader...")
    X_meta_scaled = scaler.transform(X_meta)
    test_dataset = ScamDataset(X_text, X_meta_scaled, y, tokenizer, max_len=MAX_LEN)
    test_loader  = DataLoader(test_dataset, batch_size=16, shuffle=False)

    print("\n[4/4] Running Inference on Hard Test Set...")
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

    # Dynamic file paths based on model choice
    if args.model == "multimodal":
        fp_path = "./results/false_positives.csv"
        fn_path = "./results/false_negatives.csv"
        cm_path = "./results/hard_test_confusion_matrix.png"
        metrics_path = "./scam_model/metrics.json"
        eval_title = "FUSED SYSTEM — HARD TEST EVALUATION"
        cm_title = "Confusion Matrix — Hard Test Set"
    else:
        fp_path = "./results/baseline_false_positives.csv"
        fn_path = "./results/baseline_false_negatives.csv"
        cm_path = "./results/baseline_hard_test_confusion_matrix.png"
        metrics_path = "./scam_model/baseline_metrics.json"
        eval_title = "BASELINE SYSTEM — HARD TEST EVALUATION"
        cm_title = "Confusion Matrix — Baseline Hard Test Set"

    # Save False Positives and False Negatives to CSV
    os.makedirs("./results", exist_ok=True)
    all_preds_arr = np.array(all_preds)
    all_labels_arr = np.array(all_labels)
    
    fp_indices = np.where((all_preds_arr == 1) & (all_labels_arr == 0))[0]
    fn_indices = np.where((all_preds_arr == 0) & (all_labels_arr == 1))[0]
    
    df.iloc[fp_indices].to_csv(fp_path, index=False)
    df.iloc[fn_indices].to_csv(fn_path, index=False)
    print("   ✅ Exported actual text data for FP/FN to ./results/")

    print(f"\n{'='*55}")
    print(f"  {eval_title}")
    print(f"{'='*55}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"\n{classification_report(all_labels, all_preds, target_names=['Legitimate','Scam'])}")

    # Generate Confusion Matrix for Hard Test
    plt.figure(figsize=(6, 5))
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(all_labels, all_preds)
    tn, fp, fn, tp = cm.ravel()
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Reds', xticklabels=["Legit","Scam"], yticklabels=["Legit","Scam"])
    plt.title(cm_title)
    plt.ylabel("True"); plt.xlabel("Predicted")
    plt.tight_layout()
    os.makedirs("./results", exist_ok=True)
    plt.savefig(cm_path, dpi=150)
    print(f"   ✅ Confusion matrix saved to {cm_path}")

    import json
    import datetime
    metrics = {
        "accuracy": float(acc * 100),
        "precision": float(prec * 100),
        "recall": float(rec * 100),
        "f1": float(f1 * 100),
        "total_samples": len(df),
        "scam_samples": int((df['label'] == 1).sum()),
        "legit_samples": int((df['label'] == 0).sum()),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "evaluation_date": datetime.datetime.now().strftime("%b %d, %Y • %I:%M %p")
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"   ✅ Metrics saved to {metrics_path}")

if __name__ == "__main__":
    main()
