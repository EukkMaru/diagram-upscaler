# filter.py
import requests
import time
import json
from xml.etree import ElementTree as ET

CATEGORIES = [
    "math.CO",
    "cs.LG", "cs.DS", "cs.AI", "cs.NE"
]
KEYWORDS = ["graph theory", "graph neural", "graph isomorphism", "graph classification"]

MAX_RESULTS_PER_QUERY = 300
TOTAL_DESIRED = 3000
OUTFILE = "filtered_papers.json"

base_url = "http://export.arxiv.org/api/query"

headers = {
    "User-Agent": "arxiv-diagram-crawler/0.1 (fuyunemaru@gmail.com)"
}

def fetch_arxiv(category, keyword, start=0, max_results=100, retries=3):
    query = f"cat:{category}+AND+(ti:{keyword}+OR+abs:{keyword})"
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    for attempt in range(retries):
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[!] Error: {e}")
            if attempt < retries - 1:
                print(f"    Retrying in 5s...")
                time.sleep(5)
            else:
                return None

def extract_entries(raw_xml):
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw_xml)
    entries = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.strip().split("/")[-1]
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        categories = [tag.attrib["term"] for tag in entry.findall("atom:category", ns)]
        entries.append({
            "id": arxiv_id,
            "title": title,
            "summary": summary,
            "categories": categories
        })
    return entries

all_results = []
seen_ids = set()

all_results = []
seen_ids = set()

for cat in CATEGORIES:
    for kw in KEYWORDS:
        print(f"\n--- Searching in {cat} for '{kw}' ---")
        for offset in range(0, TOTAL_DESIRED, MAX_RESULTS_PER_QUERY):
            xml = fetch_arxiv(
                category=cat,
                keyword=kw,
                start=offset,
                max_results=MAX_RESULTS_PER_QUERY
            )
            if xml is None:
                break

            entries = extract_entries(xml)
            new_entries = [e for e in entries if e["id"] not in seen_ids]
            if not new_entries:
                break

            for e in new_entries:
                seen_ids.add(e["id"])
                all_results.append(e)

            print(f"  [+] Fetched {len(new_entries)} new entries (Total: {len(all_results)})")
            
            if offset % (MAX_RESULTS_PER_QUERY * 2) == 0 and offset != 0:
                print("  [*] Saving checkpoint...")
                with open(OUTFILE, "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)

            time.sleep(5)  # throttle


with open(OUTFILE, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(all_results)} entries to {OUTFILE}")
