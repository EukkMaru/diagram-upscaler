import requests
import time
import json
from pathlib import Path

SOURCE_FILE = "filtered_papers.json"
OUT_DIR = Path("sources")
OUT_DIR.mkdir(exist_ok=True)
MAX_DOWNLOADS = 5000
RETRIES = 3
WAIT_TIME = 10

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

arxiv_ids = [paper["id"].split("v")[0] for paper in papers]
arxiv_ids = list(dict.fromkeys(arxiv_ids))  # deduplicate while preserving order

downloaded = 0
for arxiv_id in arxiv_ids:
    out_file = OUT_DIR / f"{arxiv_id}.tar.gz"
    if out_file.exists():
        print(f"[-] Already downloaded {arxiv_id}, skipping.")
        continue

    success = False
    for attempt in range(1, RETRIES + 1):
        try:
            print(f"[+] Downloading {arxiv_id} (Attempt {attempt})...")
            resp = requests.get(f"https://arxiv.org/e-print/{arxiv_id}", timeout=30)
            if resp.status_code == 200:
                with open(out_file, "wb") as f:
                    f.write(resp.content)
                print(f"[O] Saved to {out_file}")
                success = True
                downloaded += 1
                break
            else:
                print(f"[!] HTTP {resp.status_code} for {arxiv_id}")
        except Exception as e:
            print(f"[!] Error downloading {arxiv_id}: {e}")

        time.sleep(WAIT_TIME)

    if not success:
        print(f"[!] Failed to download {arxiv_id} after {RETRIES} attempts.")

    if downloaded >= MAX_DOWNLOADS:
        print(f"\n[+] Reached max download cap ({MAX_DOWNLOADS}). Stopping.")
        break

    time.sleep(WAIT_TIME)
