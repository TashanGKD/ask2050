#!/usr/bin/env python3
"""Search ask2050 activity index by date/topic/container/free text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references" / "activity_index.min.json"
LOW_OCR_ALIASES = ROOT / "references" / "manual" / "low_ocr_alias_index.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--topic", action="append", default=[])
    parser.add_argument("--container")
    parser.add_argument("--q", default="")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    data = json.loads(INDEX.read_text(encoding="utf-8"))
    manual_ids = []
    if args.q and LOW_OCR_ALIASES.exists():
        aliases = json.loads(LOW_OCR_ALIASES.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        for alias, ids in aliases.items():
            if q_lower in alias.lower() or alias.lower() in q_lower:
                manual_ids.extend(str(activity_id) for activity_id in ids)

    results = []
    seen = set()
    for item in data:
        activity_id = str(item.get("activity_id", ""))
        haystack = " ".join([
            activity_id,
            item.get("title", ""),
            item.get("summary", ""),
            item.get("container", ""),
            item.get("location", ""),
            " ".join(item.get("recommendation_tags", [])),
        ]).lower()
        if args.date and args.date not in item.get("date_tags", []):
            continue
        if args.container and args.container not in item.get("container", ""):
            continue
        if args.topic and not all(topic in item.get("recommendation_tags", []) for topic in args.topic):
            continue
        manual_match = activity_id in manual_ids
        if args.q and args.q.lower() not in haystack and not manual_match:
            continue
        if activity_id in seen:
            continue
        seen.add(activity_id)
        results.append(item)

    for item in results[: args.limit]:
        print(f"{item['date']} {item['time']} | {item['container']} | {item['title']} | {item['location']}")
        print(f"  tags: {', '.join(item['recommendation_tags'])}")
        print(f"  summary: {item['summary']}")
        print(f"  url: {item['url']}")
    print(f"matched={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
