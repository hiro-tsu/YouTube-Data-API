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
import csv
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

# We'll use the videos API to fetch the current mostPopular (trending) videos.
API_URL = "https://www.googleapis.com/youtube/v3/videos"


def get_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("Error: YOUTUBE_API_KEY environment variable is not set.")
        print("Set it in GitHub Actions secrets (YOUTUBE_API_KEY) or pass it in the environment.")
        sys.exit(1)
    return key


def query_trending(api_key: str, region: str = "JP", max_results: int = 10):
    """Query the videos API for the mostPopular chart (trending videos).

    - region: 2-letter regionCode (ISO 3166-1 alpha-2), default JP
    - max_results: number of results to fetch (max 50 according to API)
    """
    if max_results > 50:
        max_results = 50
    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": str(max_results),
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


def save_csv(all_results):
    # write a CSV summarizing id, title, channel, viewCount for each video
    os.makedirs("outputs", exist_ok=True)
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    csv_path = os.path.join("outputs", f"yt_trending_{now}.csv")

    items = all_results.get("items")
    if not items or not isinstance(items, dict) or "items" not in items:
        # nothing to write
        print("No items present to write CSV output; skipping CSV.")
        return None

    rows = []
    for item in items.get("items", []):
        # video id may be a dict (search results) or a string (videos API)
        vid = item.get("id")
        if isinstance(vid, dict):
            video_id = vid.get("videoId") or vid.get("kind")
        else:
            video_id = vid

        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})

        rows.append({
            "videoId": video_id or "",
            "title": snippet.get("title", "")[:500],
            "channelTitle": snippet.get("channelTitle", "")[:200],
            "viewCount": stats.get("viewCount", ""),
        })

    if not rows:
        print("No parsed rows for CSV; skipping CSV.")
        return None

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["videoId", "title", "channelTitle", "viewCount"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Saved CSV summary to: {csv_path}")
    return csv_path


def main():

    # Now behave as a trending collector.
    # Region code can be passed as a single CLI arg or via env YOUTUBE_REGION.
    cli_region = sys.argv[1] if len(sys.argv) > 1 else None
    region = cli_region or os.environ.get("YOUTUBE_REGION") or "JP"

    # If YOUTUBE_API_KEY is not present, the script will exit with code 1
    api_key = get_api_key()

    all_results = {"fetched_at": datetime.utcnow().isoformat() + "Z", "region": region, "items": []}

    print(f"Fetching trending videos for region: {region}")
    try:
        data = query_trending(api_key, region=region)
    except Exception as exc:
        print(f"Failed to query trending videos: {exc}")
        data = {"error": str(exc)}

    all_results["items"] = data

    # write a CSV summary if available
    save_csv(all_results)

    save_output(all_results)


if __name__ == "__main__":
    main()
