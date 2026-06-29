"""Sample ~600 boundary-biased candidates from raw_titles.csv.

The 4-label decision rules in planning.md hinge on:
  - comparison vs experience — both can use superlatives; distinguisher is
    grammatical (presence of 'you', 'your', 'X of reddit')
  - speculation vs opinion — both can be future-oriented; distinguisher is
    prediction vs preference
  - opinion vs experience — both can be personal; distinguisher is general
    stance vs specific event

We want a candidate pool that's heavy on titles that *probe these boundaries*,
not titles that are trivially one label.

Strategy:
  - Bucket each title into a likely primary label by lightweight pattern match
  - Score "boundary-ness" by how many secondary patterns also match
  - Stratified sample: aim for ~150 candidates per label, weighted toward
    higher boundary scores
"""

import csv
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "raw_titles.csv"
OUT_PATH = ROOT / "data" / "candidates_for_labeling.csv"

random.seed(42)


# Cheap pattern signals for each label. These are NOT labels — they're hints
# used to select interesting candidates. Final labels are assigned by Claude
# applying the planning.md decision rules.
PAT_EXPERIENCE = re.compile(
    r"\b("
    r"you'?ve\s+ever|"
    r"have\s+you\s+ever|"
    r"the\s+(?:exact\s+)?moment|"
    r"the\s+time\s+(?:when|you)|"
    r"of\s+reddit|"
    r"redditors,?\s|"
    r"people\s+who'?ve"
    r")\b",
    re.IGNORECASE,
)
PAT_SPECULATION = re.compile(
    r"\b("
    r"in\s+\d+\s+years|"
    r"in\s+the\s+next\s+(?:\d+|few|five|ten|twenty)|"
    r"will\s+(?:die|exist|happen|be)|"
    r"going\s+to\s+(?:die|happen|disappear)|"
    r"future\s+of|"
    r"next\s+(?:decade|big\s+thing)|"
    r"obsolete"
    r")\b",
    re.IGNORECASE,
)
PAT_COMPARISON = re.compile(
    r"\b("
    r"(?:the\s+)?(?:best|worst|greatest|most\s+\w+|favorite)\s+\w+\s+(?:of\s+all\s+time|ever\s+made|in\s+history)|"
    r"most\s+(?:overrated|underrated|iconic)|"
    r"top\s+\d+|"
    r"which\s+(?:movie|song|book|game|player|team)"
    r")\b",
    re.IGNORECASE,
)
PAT_OPINION = re.compile(
    r"\b("
    r"what\s+do\s+you\s+think|"
    r"do\s+you\s+(?:prefer|believe)|"
    r"unpopular\s+opinion|"
    r"what'?s\s+something\s+you|"
    r"are\s+you\s+looking\s+forward|"
    r"what\s+(?:makes|matters|annoys)\s+you"
    r")\b",
    re.IGNORECASE,
)

# Boundary trip-wires — strong indicators that two labels could both apply.
PAT_SUPERLATIVE_PRONOUN = re.compile(
    r"\b(?:worst|best|weirdest|funniest|dumbest|most\s+\w+).{0,40}\byou'?(?:ve|r)\b",
    re.IGNORECASE,
)
PAT_FUTURE_PERSONAL = re.compile(
    r"\b(?:you|your).{0,30}(?:in\s+\d+\s+years|next\s+\d+|future)",
    re.IGNORECASE,
)


def score_title(title: str) -> dict:
    """Return per-label hint scores + boundary score."""
    return {
        "exp": int(bool(PAT_EXPERIENCE.search(title))),
        "spec": int(bool(PAT_SPECULATION.search(title))),
        "comp": int(bool(PAT_COMPARISON.search(title))),
        "opin": int(bool(PAT_OPINION.search(title))),
        "boundary_super": int(bool(PAT_SUPERLATIVE_PRONOUN.search(title))),
        "boundary_future": int(bool(PAT_FUTURE_PERSONAL.search(title))),
    }


def main() -> None:
    rows = list(csv.DictReader(IN_PATH.open()))
    for r in rows:
        r["_score"] = score_title(r["title"])

    # Bucket by dominant hint (or "ambiguous" if 0 or >1 matches)
    by_bucket = {"exp": [], "spec": [], "comp": [], "opin": [], "ambig": []}
    for r in rows:
        s = r["_score"]
        hits = [k for k in ("exp", "spec", "comp", "opin") if s[k]]
        if len(hits) == 1:
            by_bucket[hits[0]].append(r)
        else:
            by_bucket["ambig"].append(r)

    print("Bucket sizes from heuristic pre-pass:")
    for k, v in by_bucket.items():
        print(f"  {k:10s} {len(v)}")

    # Take from each bucket: 100 single-hint + boundary-flagged from ambig
    sample = []
    for k in ("exp", "spec", "comp", "opin"):
        # Prefer ones that ALSO trip a boundary pattern (harder cases)
        bucket = by_bucket[k]
        with_boundary = [r for r in bucket
                         if r["_score"]["boundary_super"] or
                         r["_score"]["boundary_future"]]
        without = [r for r in bucket if r not in with_boundary]
        random.shuffle(with_boundary)
        random.shuffle(without)
        chosen = (with_boundary + without)[:140]
        sample.extend(chosen)

    # Ambiguous titles (0 or >1 pattern matches) are inherently boundary cases
    random.shuffle(by_bucket["ambig"])
    sample.extend(by_bucket["ambig"][:140])

    # Deduplicate + write
    seen = set()
    out = []
    for r in sample:
        if r["title"] in seen:
            continue
        seen.add(r["title"])
        out.append({
            "id": r["id"],
            "title": r["title"],
            "score": r["score"],
            "permalink": r["permalink"],
            "hint_exp": r["_score"]["exp"],
            "hint_spec": r["_score"]["spec"],
            "hint_comp": r["_score"]["comp"],
            "hint_opin": r["_score"]["opin"],
            "boundary_super": r["_score"]["boundary_super"],
            "boundary_future": r["_score"]["boundary_future"],
        })

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    print(f"\nWrote {len(out)} candidates to {OUT_PATH.relative_to(ROOT)}")
    counts = Counter()
    for r in out:
        hits = sum(r[k] for k in ("hint_exp", "hint_spec", "hint_comp", "hint_opin"))
        counts[hits] += 1
    print(f"Hint-hit distribution: {dict(counts)}")


if __name__ == "__main__":
    main()
