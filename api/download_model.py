"""
Downloads model.pt and scaler.pkl into scam_model/ before the API starts.

Why this exists: these two files are in .gitignore (too large for GitHub),
so they never reach Render via the normal git push. This script pulls them
from a Hugging Face model repo instead, as part of Render's Build Command.

Setup required before this will work:
1. Upload model.pt and scaler.pkl to a Hugging Face model repo
   (e.g. https://huggingface.co/YOUR_USERNAME/YOUR_REPO).
2. Set the HF_MODEL_REPO environment variable on Render to "YOUR_USERNAME/YOUR_REPO".
3. If the repo is private, also set HF_TOKEN to a Hugging Face access token
   (Settings -> Access Tokens on huggingface.co). Public repos don't need this.
"""
import os
import sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "..", "scam_model")

HF_MODEL_REPO = os.environ.get("HF_MODEL_REPO")  # e.g. "your-username/scamshield-model"
HF_TOKEN = os.environ.get("HF_TOKEN")  # only needed for private repos

FILES = ["model.pt", "scaler.pkl"]


def download_file(filename: str) -> None:
    dest_path = os.path.join(MODEL_DIR, filename)

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"✅ {filename} already present, skipping download.")
        return

    if not HF_MODEL_REPO:
        print(f"❌ HF_MODEL_REPO environment variable is not set — cannot download {filename}.")
        sys.exit(1)

    url = f"https://huggingface.co/{HF_MODEL_REPO}/resolve/main/{filename}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

    print(f"⬇️  Downloading {filename} from {url} ...")
    with requests.get(url, headers=headers, stream=True, timeout=120) as resp:
        if resp.status_code != 200:
            print(f"❌ Failed to download {filename}: HTTP {resp.status_code}")
            print("   Check that HF_MODEL_REPO is correct and the repo/file is public "
                  "(or that HF_TOKEN is set correctly for a private repo).")
            sys.exit(1)
        os.makedirs(MODEL_DIR, exist_ok=True)
        total = 0
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)
    print(f"✅ Downloaded {filename} ({total / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    for fname in FILES:
        download_file(fname)
    print("Done. Model files ready in scam_model/.")
