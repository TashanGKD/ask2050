#!/usr/bin/env python3
"""Audit cross-layer references between official activities, article units, and focus sessions."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    raise SystemExit(f"cross-reference audit failed: {message}")


def parse_time_range(value: str) -> tuple[int, int] | None:
    match = re.search(r"(\d{1,2}):(\d{2})\s*[-—–~～至]\s*(\d{1,2}):(\d{2})", str(value))
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2)), int(match.group(3)) * 60 + int(match.group(4))


def is_broad_time(value: str) -> bool:
    parsed = parse_time_range(value)
    if not parsed:
        return True
    start, end = parsed
    return end - start >= 300 or str(value) in {"09:00-15:30", "12:30-23:55", "14:00-23:55"}


def time_relation(official_time: str, observed_time: str) -> str:
    official = parse_time_range(official_time)
    observed = parse_time_range(observed_time)
    if not official or not observed:
        return "unknown"
    if official[0] <= observed[0] and observed[1] <= official[1]:
        return "contained"
    if not (observed[1] <= official[0] or official[1] <= observed[0]):
        return "overlap"
    if is_broad_time(official_time):
        return "broad_outside"
    return "outside"


def normalize_location(value: str) -> str:
    value = str(value).lower()
    replacements = [
        "云栖小镇国际会展中心一期",
        "云栖小镇国际会展中心",
        "国际会展中心一期",
        "国际会展中心",
        "a区云栖小镇",
        "a区",
        "区",
    ]
    for old in replacements:
        value = value.replace(old, "")
    value = value.replace("２", "2").replace("３", "3").replace("１", "1")
    return re.sub(r"[\s\-—–：:，,。！!？?·・「」“”\"'()（）【】\[\]@|｜+]+", "", value)


def is_specific_hall(location: str) -> bool:
    return "厅" in str(location)


def assert_time_compatible(label: str, official: dict, observed_time: str) -> None:
    if not observed_time or str(observed_time).startswith("待"):
        return
    if is_broad_time(official.get("time", "")):
        return
    relation = time_relation(official.get("time", ""), observed_time)
    if relation == "outside":
        fail(
            f"{label} time {observed_time} is outside official "
            f"{official.get('activity_id')} {official.get('time')}"
        )


def assert_location_compatible(label: str, official: dict, observed_location: str) -> None:
    if not observed_location or not is_specific_hall(official.get("location", "")):
        return
    observed_norm = normalize_location(observed_location)
    official_norm = normalize_location(official.get("location", ""))
    if observed_norm != official_norm:
        fail(
            f"{label} location {observed_location!r} conflicts with official "
            f"{official.get('activity_id')} {official.get('location')!r}"
        )


def main() -> int:
    activities = load_json(REF / "activity_index.min.json")
    activity_lookup = {str(item.get("activity_id")): item for item in activities}
    activity_ids = set(activity_lookup)

    focus_sessions = load_json(REF / "focus_sessions.min.json")
    session_ids = [str(item.get("session_id")) for item in focus_sessions]
    duplicate_session_ids = sorted(session_id for session_id, count in Counter(session_ids).items() if count > 1)
    if duplicate_session_ids:
        fail(f"duplicate focus session IDs: {duplicate_session_ids[:10]}")

    for item in focus_sessions:
        session_id = str(item.get("session_id"))
        parent_id = str(item.get("parent_activity_id"))
        official = activity_lookup.get(parent_id)
        if not official:
            fail(f"focus session {session_id} references unknown activity {parent_id}")
        if item.get("date") != official.get("date"):
            fail(
                f"focus session {session_id} date {item.get('date')} conflicts with "
                f"official {parent_id} {official.get('date')}"
            )
        assert_time_compatible(f"focus session {session_id}", official, str(item.get("time", "")))
        assert_location_compatible(f"focus session {session_id}", official, str(item.get("location", "")))

    crosswalk = load_json(REF / "article_activity_crosswalk.json")
    for record in crosswalk.get("records", []):
        for unit in record.get("units", []):
            section = unit.get("section_title", "")
            for activity_id in unit.get("matched_activity_ids", []):
                activity_id = str(activity_id)
                official = activity_lookup.get(activity_id)
                if not official:
                    fail(f"article unit {section!r} references unknown activity {activity_id}")
                date_tags = [str(value) for value in unit.get("date_tags", []) if value]
                if date_tags and official.get("date") not in date_tags:
                    fail(
                        f"article unit {section!r} date tags {date_tags} conflict with "
                        f"official {activity_id} {official.get('date')}"
                    )
                assert_time_compatible(f"article unit {section!r}", official, str(unit.get("time_range", "")))
                assert_location_compatible(
                    f"article unit {section!r}",
                    official,
                    str(unit.get("location_hint", "")),
                )

    article_facets = load_json(REF / "article_facets.json")
    for source_id, facet in article_facets.items():
        unknown_ids = sorted(str(activity_id) for activity_id in facet.get("linked_activity_ids", []) if str(activity_id) not in activity_ids)
        if unknown_ids:
            fail(f"article facet {source_id} references unknown activities: {unknown_ids[:10]}")

    evidence = load_json(REF / "article_evidence_index.json")
    for record in evidence.get("records", []):
        source_id = record.get("result_file")
        unknown_ids = sorted(
            str(activity_id)
            for activity_id in record.get("matched_activity_ids", [])
            if str(activity_id) not in activity_ids
        )
        if unknown_ids:
            fail(f"article evidence {source_id} references unknown activities: {unknown_ids[:10]}")

    print("cross_reference_audit ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
