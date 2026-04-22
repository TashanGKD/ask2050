#!/usr/bin/env python3
"""Validate ask2050 packaged data and search behavior after mounting."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
MANUAL = REF / "manual"
SCRIPT = ROOT / "scripts" / "search_activities.py"


REQUIRED_FILES = [
    ROOT / "SKILL.md",
    REF / "coverage_report.md",
    REF / "evidence_status.md",
    REF / "tashan_world_bridge.md",
    REF / "activity_index.min.json",
    REF / "article_activity_crosswalk.json",
    REF / "articles_index.json",
    MANUAL / "article_curation.md",
    MANUAL / "article_aliases.json",
    SCRIPT,
]

EXPECTED_ALIAS_IDS = {
    "YOLO": {"12224", "12251", "12276"},
    "AI芯片": {"12220"},
    "WaytoAGI": {"12432", "12430", "12446", "12588", "12444", "12445"},
    "waytoagi": {"12432", "12430", "12446", "12588", "12444", "12445"},
    "课创黑客松": {"12267"},
    "设计自己": {"12424", "12420", "12633"},
}

CONFLICT_EXCLUDED = {
    "AI芯片": {"12224", "12251", "12276"},
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def ids_from_search(query: str) -> set[str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "30"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    return set(re.findall(r"/activity/(\d+)", completed.stdout))


def main() -> int:
    missing = [path.relative_to(ROOT).as_posix() for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    activities = load_json(REF / "activity_index.min.json")
    crosswalk = load_json(REF / "article_activity_crosswalk.json")
    articles = load_json(REF / "articles_index.json")
    aliases = load_json(MANUAL / "article_aliases.json")

    if len(activities) < 286:
        fail(f"activity index has {len(activities)} rows, expected at least 286")
    if len(articles) < 77:
        fail(f"article index has {len(articles)} rows, expected at least 77")
    if not isinstance(crosswalk, dict) or not crosswalk.get("records"):
        fail("article_activity_crosswalk.json must be an object with non-empty records")
    forbidden_full_index = REF / ("activity_index." + "full.json")
    if forbidden_full_index.exists():
        fail("full activity index should not be packaged in the default skill")
    if any((REF / "article_ocr").glob("*.md")):
        fail("raw article_ocr markdown should not be packaged in the default skill")

    activity_ids = {str(item.get("activity_id")) for item in activities}
    curation_text = (MANUAL / "article_curation.md").read_text(encoding="utf-8")
    curation_ids = set(re.findall(r"`(\d{5})`", curation_text))
    missing_curation_ids = sorted(curation_ids - activity_ids)
    if missing_curation_ids:
        fail(f"manual curation references unknown activity IDs: {missing_curation_ids}")

    crosswalk_ids = set()
    for record in crosswalk.get("records", []):
        for unit in record.get("units", []):
            crosswalk_ids.update(str(activity_id) for activity_id in unit.get("matched_activity_ids", []))
    missing_crosswalk_ids = sorted(crosswalk_ids - activity_ids)
    if missing_crosswalk_ids:
        fail(f"crosswalk references unknown activity IDs: {missing_crosswalk_ids}")

    for alias, expected_ids in EXPECTED_ALIAS_IDS.items():
        actual_alias_ids = set()
        for alias_key, ids in aliases.items():
            if alias.lower() == alias_key.lower():
                actual_alias_ids.update(str(item) for item in ids)
        missing_alias_ids = expected_ids - actual_alias_ids
        if missing_alias_ids:
            fail(f"alias {alias} missing IDs in article_aliases.json: {sorted(missing_alias_ids)}")

        actual_search_ids = ids_from_search(alias)
        missing_search_ids = expected_ids - actual_search_ids
        if missing_search_ids:
            fail(f"query {alias} missing IDs from search path: {sorted(missing_search_ids)}")

        excluded = CONFLICT_EXCLUDED.get(alias, set())
        unexpected = actual_search_ids & excluded
        if unexpected:
            fail(f"query {alias} unexpectedly mixed conflict IDs: {sorted(unexpected)}")

    for dirty_query in ["2025", "技术" + "峰会"]:
        dirty_results = ids_from_search(dirty_query)
        if dirty_results:
            fail(f"query {dirty_query} should not return default activities: {sorted(dirty_results)}")

    print("OK: ask2050 packaged data and search path passed")
    dirty_hits = []
    dirty_patterns = [
        "2025" + "年度",
        "AI " + "技术" + "峰会",
        "AI" + "技术" + "峰会",
        "技术" + "峰会",
    ]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern in text for pattern in dirty_patterns):
            dirty_hits.append(path.relative_to(ROOT).as_posix())
    if dirty_hits:
        fail(f"dirty non-2050 meeting terms found: {sorted(set(dirty_hits))}")

    print(f"activities={len(activities)} articles={len(articles)} raw_ocr_packaged=0")
    print(f"manual_curation_ids={len(curation_ids)} alias_keys={len(aliases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
