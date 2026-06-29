"""Fetch r/AskReddit post titles via Reddit's public JSON API.

What this script does:
  1. Hits reddit.com/r/AskReddit/{feed}.json across multiple feeds and time windows
  2. Also runs label-specific searches (e.g. titles containing "of Reddit,") to
     surface posts that are likely to fall into the less-common labels
  3. Deduplicates by post ID
  4. Writes data/raw_titles.csv with columns: id, title, score, created_utc, source

What this script does NOT do:
  - Annotate (that happens in scripts/annotate.py later, run by Claude)
  - Use any Reddit credentials — only public unauthenticated endpoints
  - Touch any third-party site

Run from the project root:
    .venv/bin/python scripts/fetch_askreddit.py

Output: data/raw_titles.csv (~800-1500 rows expected, depending on Reddit rate limits)
"""

import csv
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# Reddit's API rules require a unique, identifying User-Agent.
# Format: "<platform>:<appname>:<version> (by /u/<your-reddit-username>)".
# If you have a Reddit account, replace the username below with yours.
# If not, leave as is — Reddit will accept any well-formed UA, just at a lower
# rate limit.
USER_AGENT = "macos:ai201-takemeter:0.1 (by /u/ai201_student)"

# Output path (relative to project root)
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw_titles.csv"

# (path, params, label-bias note) tuples for each query we'll run.
# Mix of general "top" feeds across time windows + targeted searches for each label.
QUERIES = [
    # General top — broadest coverage
    ("/r/AskReddit/top.json",  {"t": "all",   "limit": "100"}, "top_all"),
    ("/r/AskReddit/top.json",  {"t": "year",  "limit": "100"}, "top_year"),
    ("/r/AskReddit/top.json",  {"t": "month", "limit": "100"}, "top_month"),
    ("/r/AskReddit/top.json",  {"t": "week",  "limit": "100"}, "top_week"),
    ("/r/AskReddit/hot.json",  {"limit": "100"},               "hot"),

    # Label-biased searches. restrict_sr=on keeps results in r/AskReddit.
    # These boost the per-label sample size so we're not 80% comparison-type.
    ("/r/AskReddit/search.json",
        {"q": '"of reddit"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_experience_vocative"),
    ("/r/AskReddit/search.json",
        {"q": '"you ever"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_experience_pronoun"),
    ("/r/AskReddit/search.json",
        {"q": '"in 20 years"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_speculation_future"),
    ("/r/AskReddit/search.json",
        {"q": '"will die out"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_speculation_extinction"),
    ("/r/AskReddit/search.json",
        {"q": '"best of all time"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_comparison_superlative"),
    ("/r/AskReddit/search.json",
        {"q": '"most overrated"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_comparison_overrated"),
    ("/r/AskReddit/search.json",
        {"q": '"what do you think"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_opinion_stance"),
    ("/r/AskReddit/search.json",
        {"q": '"unpopular opinion"', "restrict_sr": "on", "sort": "top",
         "t": "all", "limit": "100"}, "search_opinion_unpopular"),
]


def fetch(path: str, params: dict) -> dict:
    """One GET to reddit.com. Returns parsed JSON or raises."""
    qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    url = f"https://www.reddit.com{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_posts(data: dict, source: str) -> list[dict]:
    children = data.get("data", {}).get("children", [])
    rows = []
    for c in children:
        d = c.get("data", {})
        title = d.get("title", "").strip()
        if not title:
            continue
        rows.append({
            "id": d.get("id", ""),
            "title": title,
            "score": d.get("score", 0),
            "created_utc": int(d.get("created_utc", 0)),
            "source": source,
        })
    return rows


def main() -> None:
    seen: set[str] = set()
    all_rows: list[dict] = []

    for path, params, source in QUERIES:
        try:
            print(f"  Fetching {source}...", end=" ", flush=True)
            data = fetch(path, params)
            rows = extract_posts(data, source)
            new_rows = [r for r in rows if r["id"] and r["id"] not in seen]
            for r in new_rows:
                seen.add(r["id"])
            all_rows.extend(new_rows)
            print(f"+{len(new_rows)} new (total {len(all_rows)})")
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} — skipping")
        except Exception as e:
            print(f"error: {e!r} — skipping")
        # Reddit's free tier is 60 requests/minute; sleep 1.1s between calls.
        time.sleep(1.1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "title", "score", "created_utc", "source"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} unique titles to {OUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
