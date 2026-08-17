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
import time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "..", "scam_model")

HF_MODEL_REPO = os.environ.get("HF_MODEL_REPO")  # e.g. "your-username/scamshield-model"
HF_TOKEN = os.environ.get("HF_TOKEN")  # only needed for private repos

FILES = ["model.pt", "scaler.pkl"]

MAX_ATTEMPTS = 5
RETRY_BACKOFF_SECONDS = 5  # doubles each attempt: 5, 10, 20, 40...


def _remote_size(url: str, headers: dict) -> int | None:
    """HEAD request to find the expected file size. Returns None if unavailable."""
    try:
        resp = requests.head(url, headers=headers, allow_redirects=True, timeout=30)
        size = resp.headers.get("Content-Length")
        return int(size) if size is not None else None
    except requests.RequestException:
        return None


def download_file(filename: str) -> None:
    dest_path = os.path.join(MODEL_DIR, filename)
    tmp_path = dest_path + ".part"

    if not HF_MODEL_REPO:
        print(f"❌ HF_MODEL_REPO environment variable is not set — cannot download {filename}.")
        sys.exit(1)

    url = f"https://huggingface.co/{HF_MODEL_REPO}/resolve/main/{filename}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

    expected_size = _remote_size(url, headers)

    # Skip only if a fully-downloaded, correctly-sized file already exists.
    # (A partial file from a previous failed attempt will NOT match and will be redownloaded.)
    if os.path.exists(dest_path):
        existing_size = os.path.getsize(dest_path)
        if expected_size is not None and existing_size == expected_size:
            print(f"✅ {filename} already present and complete ({existing_size / 1_000_000:.1f} MB), skipping.")
            return
        elif expected_size is None and existing_size > 0:
            # Couldn't verify remote size, but a file is there — assume OK rather than re-pull 700MB needlessly.
            print(f"⚠️  {filename} exists ({existing_size / 1_000_000:.1f} MB) but remote size unknown; skipping re-download.")
            return
        else:
            print(f"⚠️  {filename} exists but is incomplete/incorrect size "
                  f"({existing_size / 1_000_000:.1f} MB vs expected {expected_size / 1_000_000:.1f} MB) — redownloading.")
            os.remove(dest_path)

    os.makedirs(MODEL_DIR, exist_ok=True)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"⬇️  Downloading {filename} from {url} (attempt {attempt}/{MAX_ATTEMPTS}) ...")
            downloaded = 0
            with requests.get(url, headers=headers, stream=True, timeout=(30, 60)) as resp:
                if resp.status_code != 200:
                    print(f"❌ HTTP {resp.status_code} for {filename}.")
                    print("   Check that HF_MODEL_REPO is correct and the repo/file is public "
                          "(or that HF_TOKEN is set correctly for a private repo).")
                    sys.exit(1)

                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1_048_576):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

            # Verify completeness before trusting the download
            if expected_size is not None and downloaded != expected_size:
                raise IOError(
                    f"Incomplete download: got {downloaded} bytes, expected {expected_size} bytes."
                )

            os.replace(tmp_path, dest_path)  # atomic rename — only now does the "real" file exist
            print(f"✅ Downloaded {filename} ({downloaded / 1_000_000:.1f} MB)")
            return

        except (requests.RequestException, IOError) as e:
            print(f"⚠️  Attempt {attempt} failed for {filename}: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if attempt == MAX_ATTEMPTS:
                print(f"❌ Giving up on {filename} after {MAX_ATTEMPTS} attempts.")
                sys.exit(1)
            wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"   Retrying in {wait}s...")
            time.sleep(wait)


if __name__ == "__main__":
    for fname in FILES:
        download_file(fname)
    print("Done. Model files ready in scam_model/.")