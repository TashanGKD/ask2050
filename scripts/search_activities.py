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
ARTICLE_EVIDENCE = ROOT / "references" / "article_evidence_index.json"


def item_tags(item: dict) -> list[str]:
    tags = item.get("recommendation_tags")
    if tags:
        return [str(tag) for tag in tags]
    derived = []
    for value in [item.get("date"), item.get("container")]:
        if value:
            derived.append(str(value))
    derived.extend(str(tag) for tag in item.get("topic_tags", []))
    derived.extend(str(tag) for tag in item.get("format_tags", []))
    return sorted(set(derived))


def source_activity_ids(record: dict, query: str) -> list[str]:
    q_lower = query.lower()
    weak_year_queries = {"2024", "2025", "2026"}
    if q_lower.strip() in weak_year_queries:
        return []
    for rule in record.get("query_activity_rules", []):
        keywords = [str(keyword).lower() for keyword in rule.get("keywords", [])]
        if any(keyword in q_lower for keyword in keywords):
            return [str(activity_id) for activity_id in rule.get("activity_ids", [])]
    return [str(activity_id) for activity_id in record.get("matched_activity_ids", [])]


def filter_activity_ids(
    activity_ids: list[str],
    activity_lookup: dict[str, dict],
    *,
    date: str | None = None,
    container: str | None = None,
) -> list[str]:
    filtered = []
    for activity_id in activity_ids:
        activity = activity_lookup.get(activity_id)
        if not activity:
            continue
        if date and date != activity.get("date"):
            continue
        if container and container not in activity.get("container", ""):
            continue
        filtered.append(activity_id)
    return filtered


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
            " ".join(item_tags(item)),
        ]).lower()
        if args.date and args.date != item.get("date"):
            continue
        if args.container and args.container not in item.get("container", ""):
            continue
        tags = item_tags(item)
        if args.topic and not all(topic in tags for topic in args.topic):
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
        print(f"  tags: {', '.join(item_tags(item))}")
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

    source_results = []
    if args.q and ARTICLE_EVIDENCE.exists():
        evidence = json.loads(ARTICLE_EVIDENCE.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        old_year_only = q_lower.strip() in {"2024", "2025"}
        if not old_year_only:
            for record in evidence.get("records", []):
                source_haystack = " ".join([
                    record.get("title", ""),
                    record.get("article_csv_title") or "",
                    record.get("manual_summary", ""),
                    " ".join(str(term) for term in record.get("search_terms", [])),
                    " ".join(str(activity_id) for activity_id in source_activity_ids(record, args.q)),
                ]).lower()
                if q_lower not in source_haystack:
                    continue
                source_results.append(record)

    for record in source_results[: args.limit]:
        ids = filter_activity_ids(
            source_activity_ids(record, args.q),
            activity_lookup,
            date=args.date,
            container=args.container,
        )
        print(f"source | {record.get('result_file')} | {record.get('batch_status')} | {record.get('title')}")
        print(f"  review: {record.get('review_tier')} manual_reviewed={record.get('manual_reviewed')}")
        if record.get("manual_summary"):
            print(f"  summary: {record.get('manual_summary')}")
        if record.get("article_url"):
            print(f"  article_url: {record.get('article_url')}")
        if ids:
            print(f"  matched_activity_ids: {', '.join(ids)}")
            for activity_id in ids:
                activity = activity_lookup.get(activity_id)
                if activity:
                    print(f"  url: {activity['url']}")
        else:
            print("  matched_activity_ids: none")

    print(f"matched={len(results)} matched_units={len(unit_results)} matched_sources={len(source_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
