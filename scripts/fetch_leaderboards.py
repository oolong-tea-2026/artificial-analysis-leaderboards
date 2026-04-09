#!/usr/bin/env python3
"""
Fetch Artificial Analysis leaderboard data via their official API.
Saves daily snapshots + latest.json pointer.

Endpoints:
  - /data/llms/models              → LLM benchmarks, pricing, speed
  - /data/media/text-to-image      → T2I ELO rankings
  - /data/media/image-editing      → Image editing ELO rankings
  - /data/media/text-to-speech     → TTS ELO rankings
  - /data/media/text-to-video      → T2V ELO rankings
  - /data/media/image-to-video     → I2V ELO rankings

Usage:
  AA_API_KEY=aa_xxx python3 scripts/fetch_leaderboards.py

Environment:
  AA_API_KEY  - Artificial Analysis API key (required)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.error

API_BASE = "https://artificialanalysis.ai/api/v2"

# Endpoint config: (slug, api_path, include_categories)
ENDPOINTS = [
    ("llms",            "/data/llms/models",            False),
    ("text-to-image",   "/data/media/text-to-image",    True),
    ("image-editing",   "/data/media/image-editing",    False),
    ("text-to-speech",  "/data/media/text-to-speech",   False),
    ("text-to-video",   "/data/media/text-to-video",    True),
    ("image-to-video",  "/data/media/image-to-video",   True),
]


def fetch_endpoint(path: str, api_key: str, include_categories: bool = False) -> dict:
    """Fetch a single API endpoint with retry logic."""
    url = f"{API_BASE}{path}"
    if include_categories:
        url += "?include_categories=true"

    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "User-Agent": "artificial-analysis-leaderboards/1.0",
    }

    req = urllib.request.Request(url, headers=headers)

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") != 200:
                    raise RuntimeError(f"API returned status {data.get('status')}: {data.get('message', '')}")
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 120))
                wait = max(retry_after, 30 * (attempt + 1))
                print(f"  Rate limited (attempt {attempt+1}), waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"  Attempt {attempt+1} HTTP {e.code}: {e.reason}", file=sys.stderr)
                if attempt < max_attempts - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise
        except urllib.error.URLError as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < max_attempts - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise

    raise RuntimeError(f"Failed to fetch {path} after {max_attempts} attempts")


def normalize_llm(raw: dict) -> dict:
    """Normalize an LLM model entry."""
    return {
        "id": raw["id"],
        "name": raw["name"],
        "slug": raw["slug"],
        "release_date": raw.get("release_date"),
        "creator": {
            "id": raw["model_creator"]["id"],
            "name": raw["model_creator"]["name"],
            "slug": raw["model_creator"].get("slug"),
        },
        "evaluations": raw.get("evaluations", {}),
        "pricing": raw.get("pricing", {}),
        "speed": {
            "output_tokens_per_second": raw.get("median_output_tokens_per_second"),
            "time_to_first_token_seconds": raw.get("median_time_to_first_token_seconds"),
            "time_to_first_answer_token": raw.get("median_time_to_first_answer_token"),
        },
    }


def normalize_media(raw: dict) -> dict:
    """Normalize a media model entry (ELO-based)."""
    result = {
        "id": raw["id"],
        "name": raw["name"],
        "slug": raw["slug"],
        "release_date": raw.get("release_date"),
        "creator": {
            "id": raw["model_creator"]["id"],
            "name": raw["model_creator"]["name"],
        },
        "elo": raw.get("elo"),
        "rank": raw.get("rank"),
        "ci95": raw.get("ci95"),
        "appearances": raw.get("appearances"),
    }
    if "categories" in raw:
        result["categories"] = raw["categories"]
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Artificial Analysis leaderboards")
    parser.add_argument("--only", nargs="*", help="Only fetch these endpoint slugs")
    parser.add_argument("--delay", type=int, default=30, help="Delay between requests in seconds")
    args = parser.parse_args()

    api_key = os.environ.get("AA_API_KEY")
    if not api_key:
        print("ERROR: AA_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    # Filter endpoints if --only specified
    endpoints = ENDPOINTS
    if args.only:
        endpoints = [(s, p, c) for s, p, c in ENDPOINTS if s in args.only]
        if not endpoints:
            print(f"ERROR: No matching endpoints for {args.only}", file=sys.stderr)
            sys.exit(1)

    # Determine paths
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    fetched_at = now.isoformat()

    day_dir = repo_root / "data" / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    # Load existing index if retrying
    index_path = day_dir / "_index.json"
    if index_path.exists() and args.only:
        with open(index_path) as f:
            index = json.load(f)
        index["fetched_at"] = fetched_at  # Update timestamp
    else:
        index = {
            "date": date_str,
            "fetched_at": fetched_at,
            "source": "https://artificialanalysis.ai",
            "endpoints": {},
        }

    success_count = 0
    total = len(endpoints)

    for slug, path, include_cats in endpoints:
        print(f"Fetching {slug}...", end=" ", flush=True)
        try:
            raw = fetch_endpoint(path, api_key, include_cats)
            models = raw.get("data", [])

            # Normalize
            if slug == "llms":
                normalized = [normalize_llm(m) for m in models]
            else:
                normalized = [normalize_media(m) for m in models]

            # Build output
            output = {
                "meta": {
                    "endpoint": slug,
                    "api_path": path,
                    "source_url": f"https://artificialanalysis.ai",
                    "fetched_at": fetched_at,
                    "model_count": len(normalized),
                },
                "models": normalized,
            }

            # Add prompt_options for LLMs
            if "prompt_options" in raw:
                output["meta"]["prompt_options"] = raw["prompt_options"]

            # Write file
            out_path = day_dir / f"{slug}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            index["endpoints"][slug] = {"model_count": len(normalized)}
            success_count += 1
            print(f"✓ {len(normalized)} models")

        except Exception as e:
            print(f"✗ {e}", file=sys.stderr)
            index["endpoints"][slug] = {"error": str(e)}

        # Respect rate limits
        time.sleep(args.delay)

    # Write index
    index_path = day_dir / "_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # Update latest.json pointer
    latest_path = repo_root / "data" / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "path": f"data/{date_str}"}, f, indent=2)

    print(f"\nDone: {success_count}/{total} endpoints, saved to data/{date_str}/")

    if success_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
