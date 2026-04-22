#!/usr/bin/env python3
"""Search ask2050 activity index by date/topic/container/free text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references" / "activity_index.min.json"
ARTICLE_ALIASES = ROOT / "references" / "manual" / "article_aliases.json"
CROSSWALK = ROOT / "references" / "article_activity_crosswalk.json"


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
    if args.q and ARTICLE_ALIASES.exists():
        aliases = json.loads(ARTICLE_ALIASES.read_text(encoding="utf-8"))
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

    activity_lookup = {str(item.get("activity_id")): item for item in data}

    for item in results[: args.limit]:
        print(f"{item['date']} {item['time']} | {item['container']} | {item['title']} | {item['location']}")
        print(f"  tags: {', '.join(item['recommendation_tags'])}")
        print(f"  summary: {item['summary']}")
        print(f"  url: {item['url']}")

    unit_results = []
    if args.q and CROSSWALK.exists():
        crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        for record in crosswalk.get("records", []):
            if args.container and args.container not in record.get("container", ""):
                continue
            for unit in record.get("units", []):
                if args.date and args.date not in unit.get("date_tags", []):
                    continue
                unit_haystack = " ".join([
                    unit.get("section_title", ""),
                    unit.get("unit_type", ""),
                    unit.get("time_range", ""),
                    unit.get("location_hint", ""),
                    " ".join(unit.get("topic_tags", [])),
                ]).lower()
                if q_lower not in unit_haystack:
                    continue
                unit_results.append((record, unit))

    for record, unit in unit_results[: args.limit]:
        ids = [str(activity_id) for activity_id in unit.get("matched_activity_ids", [])]
        print(f"unit | {record.get('container')} | {unit.get('section_title')} | {unit.get('time_range', 'unknown')} | {unit.get('location_hint', '')}")
        print(f"  article: {record.get('article_title')}")
        print(f"  tags: {', '.join(unit.get('topic_tags', []))}")
        if ids:
            print(f"  matched_activity_ids: {', '.join(ids)}")
            for activity_id in ids:
                activity = activity_lookup.get(activity_id)
                if activity:
                    print(f"  url: {activity['url']}")
        else:
            print("  matched_activity_ids: none")

    print(f"matched={len(results)} matched_units={len(unit_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
