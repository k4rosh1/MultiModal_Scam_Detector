# =============================================================================
# Merge your separate REAL dataset CSVs into one training-ready file
# =============================================================================
# This does NOT touch or include your synthetic dataset (scam_dataset.csv) —
# it only combines your real dataset files with each other, since they're
# currently split across multiple CSVs. Output schema matches what
# scam_detection.py expects:
#
#   text, account_age, posting_frequency, label
#
# Usage:
#   1. Edit INPUT_FILES below to list all your REAL dataset CSV paths.
#   2. python merge_datasets.py
#   3. This produces merged_real_dataset.csv — point scam_detection.py at
#      this file when you want to train on real data only.
# =============================================================================

import pandas as pd
import re as _re

# ── COLUMN NORMALIZATION ───────────────────────────────────────────────────────
# Different sources often name columns slightly differently
# (extra whitespace, unit suffixes like "(days)"). This maps common variants
# to the exact names scam_detection.py expects.
_COLUMN_ALIASES = {
    "text":               ["text", "text ", " text", "post", "message", "content"],
    "account_age":        ["account_age", "account_age (days)", "account age", "account_age(days)"],
    "posting_frequency":  ["posting_frequency", "posting_frequency (per day)", "posting frequency", "posting_frequency(per day)"],
    "label":              ["label", "labels", "class"],
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda c: c.strip())
    rename_map = {}
    for standard_name, variants in _COLUMN_ALIASES.items():
        for col in df.columns:
            if col.strip().lower() in [v.lower() for v in variants]:
                rename_map[col] = standard_name
                break
    return df.rename(columns=rename_map)

# ── CONFIG ────────────────────────────────────────────────────────────────────
# List only your real dataset CSVs here. Do NOT include scam_dataset.csv
# (the synthetic one) — this script keeps that entirely separate.
INPUT_FILES = [
    "500_Selling_Related_Legit_Posts__Facebook_.csv",
    "500_Selling_Related_Legit_Posts__X_.csv",
    "X-FB_English_Legit.csv",
    "500_Investment_Legit_Posts__Facebook_.csv",
    "500_Investment_Legit_Posts__X_.csv",
    "FB_Selling_Scams.csv",
    "X_Investment_Scams.csv",
    "X_Selling_Scams.csv",
    "X-FB_English_Scams.csv",
    "FB_Investment_Scams.csv",
]

OUTPUT_FILE = "merged_real_dataset.csv"

# Set to True to keep duplicate rows as-is (no deduplication).
# Set to False to drop exact-duplicate text rows (recommended if you plan to
# do a train/test split afterward — identical text landing in both splits
# inflates reported accuracy without real generalization).
KEEP_DUPLICATES = True

REQUIRED_COLS = ["text", "account_age", "posting_frequency", "label"]

# ── LOAD + VALIDATE EACH FILE ─────────────────────────────────────────────────
frames = []
for path in INPUT_FILES:
    try:
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            print(f"   {path}: not valid UTF-8, retrying with cp1252 encoding...")
            df = pd.read_csv(path, encoding="cp1252")
    except FileNotFoundError:
        print(f"⚠️  Skipping {path} — file not found.")
        continue

    df = _normalize_columns(df)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"❌ {path} is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Rename/add columns so every file has: {REQUIRED_COLS}"
        )

    # Keep only the columns we need, in a consistent order
    df = df[REQUIRED_COLS].copy()

    # Basic type coercion / cleanup
    df["text"]  = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(int)

    before = len(df)
    df = df[df["text"].str.len() > 0]                       # drop empty text
    df = df[df["label"].isin([0, 1])]                        # drop bad labels
    dropped = before - len(df)
    if dropped:
        print(f"   {path}: dropped {dropped} row(s) with empty text or invalid label")

    print(f"✅ Loaded {path}: {len(df)} rows  |  Scam: {df['label'].sum()}  |  Legit: {(df['label']==0).sum()}")
    frames.append(df)

if not frames:
    raise RuntimeError("No valid input files were loaded — check INPUT_FILES paths.")

# ── COMBINE ────────────────────────────────────────────────────────────────────
merged = pd.concat(frames, ignore_index=True)

# ── DEDUPLICATE (optional) ─────────────────────────────────────────────────────
if KEEP_DUPLICATES:
    print(f"\n🔁 KEEP_DUPLICATES is True — duplicate rows were left in as-is.")
else:
    # Exact-duplicate text (case-insensitive) — common when the same message
    # shows up in more than one source dataset.
    before = len(merged)
    merged["_text_key"] = merged["text"].str.lower().str.strip()
    merged = merged.drop_duplicates(subset="_text_key", keep="first").drop(columns="_text_key")
    dropped = before - len(merged)
    if dropped:
        print(f"\n🧹 Dropped {dropped} exact-duplicate row(s) across combined files")

# ── SHUFFLE ────────────────────────────────────────────────────────────────────
merged = merged.sample(frac=1, random_state=42).reset_index(drop=True)

# ── SAVE ───────────────────────────────────────────────────────────────────────
merged.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"\n{'='*55}")
print(f"  Merged dataset saved to {OUTPUT_FILE}")
print(f"{'='*55}")
print(f"  Total samples : {len(merged)}")
print(f"  Scam          : {merged['label'].sum()}")
print(f"  Legitimate    : {(merged['label']==0).sum()}")
print(f"\n  Next step: point scam_detection.py's pd.read_csv(...) at "
      f"'{OUTPUT_FILE}' to train on your real data.\n"
      f"  (Your synthetic dataset was left untouched — this file contains "
      f"real data only.)")