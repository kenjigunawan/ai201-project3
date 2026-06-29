"""Fetch r/AskReddit titles from Hugging Face (Pushshift archive 2013-2018).

Used as fallback when Reddit's WAF blocks direct API access.
Dataset: derek-thomas/dataset-creator-askreddit (public, no auth needed).

Run from the project root:
    .venv/bin/python scripts/fetch_from_hf.py

Output: data/raw_titles.csv (~3000 rows, deduplicated, length-filtered)
"""

import csv
import re
from pathlib import Path

from datasets import load_dataset

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw_titles.csv"
TARGET = 3000  # post-filter target

# Length bounds (chars). Very short titles ("Worst fear?") and very long ones
# (rant-style posts) tend to be either trivially classifiable or confusing edge
# cases that don't represent typical r/AskReddit discourse.
MIN_LEN = 30
MAX_LEN = 200


def looks_like_question(title: str) -> bool:
    # Most r/AskReddit posts end with ?; a few use the title-as-question pattern.
    return title.strip().endswith("?") or "what" in title.lower() or \
           "who" in title.lower() or "when" in title.lower() or \
           "how" in title.lower() or "why" in title.lower()


def main() -> None:
    ds = load_dataset(
        "derek-thomas/dataset-creator-askreddit",
        split="all_days",
        streaming=True,
    )

    seen_titles: set[str] = set()
    rows: list[dict] = []

    for row in ds:
        title = (row.get("title") or "").strip()
        title = re.sub(r"\s+", " ", title)  # normalize whitespace
        if not title or title in seen_titles:
            continue
        if len(title) < MIN_LEN or len(title) > MAX_LEN:
            continue
        if not looks_like_question(title):
            continue
        seen_titles.add(title)
        rows.append({
            "id": row.get("id", ""),
            "title": title,
            "score": row.get("score", 0),
            "permalink": row.get("permalink", ""),
            "created_utc": row.get("created_utc", 0),
        })
        if len(rows) >= TARGET:
            break

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["id", "title", "score", "permalink", "created_utc"]
        )
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} titles to {OUT_PATH}")


if __name__ == "__main__":
    main()
