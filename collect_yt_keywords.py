#!/usr/bin/env python3
"""
collect_yt_keywords.py

Small script to query the YouTube Data API (v3) for a list of seed keywords
and write the search results into a timestamped JSON file under `outputs/`.

It expects YOUTUBE_API_KEY to be present in the environment. If the key is
missing the script will exit with a non-zero status and print a helpful message.

This script uses only the Python standard library so it can run on plain
GitHub Actions python runners without extra dependencies.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime

DEFAULT_KEYWORDS = [
    "python tutorial",
    "how to code",
    "youtube api",
]

API_URL = "https://www.googleapis.com/youtube/v3/search"


def get_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("Error: YOUTUBE_API_KEY environment variable is not set.")
        print("Set it in GitHub Actions secrets (YOUTUBE_API_KEY) or pass it in the environment.")
        sys.exit(1)
    return key


def query_youtube(api_key: str, q: str, max_results: int = 5):
    params = {
        "part": "snippet",
        "q": q,
        "maxResults": str(max_results),
        "type": "video",
        "key": api_key,
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as resp:
        raw = resp.read()
        return json.loads(raw)


def save_output(all_results):
    os.makedirs("outputs", exist_ok=True)
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join("outputs", f"yt_results_{now}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2, ensure_ascii=False)
    print(f"Saved results to: {out_path}")


def main():
    # Accept keywords from CLI args, otherwise use defaults
    keywords = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_KEYWORDS

    # If YOUTUBE_API_KEY is not present, the script will exit with code 1
    api_key = get_api_key()

    all_results = {"fetched_at": datetime.utcnow().isoformat() + "Z", "queries": []}

    for q in keywords:
        print(f"Querying: {q}")
        try:
            data = query_youtube(api_key, q)
        except Exception as exc:
            print(f"Failed to query YouTube for '{q}': {exc}")
            data = {"error": str(exc)}
        all_results["queries"].append({"q": q, "result": data})

    save_output(all_results)


if __name__ == "__main__":
    main()
