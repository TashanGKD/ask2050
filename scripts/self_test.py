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
    REF / "source_inventory.md",
    REF / "tashan_world_bridge.md",
    REF / "activity_index.min.json",
    REF / "article_activity_crosswalk.json",
    REF / "article_evidence_index.json",
    REF / "articles_index.json",
    MANUAL / "article_curation.md",
    MANUAL / "article_aliases.json",
    SCRIPT,
]

EXPECTED_ALIAS_IDS = {
    "YOLO": {"12224", "12251", "12276"},
    "AI芯片": {"12220"},
    "OpenClaw": {"12432", "12430", "12446", "12588"},
    "WaytoAGI": {"12432", "12430", "12446", "12588", "12444", "12445"},
    "waytoagi": {"12432", "12430", "12446", "12588", "12444", "12445"},
    "课创黑客松": {"12267"},
    "设计自己": {"12424", "12420", "12633"},
    "少数派": {"12358", "12540"},
    "未来城邦": {"12363"},
    "自然读书会": {"12455"},
    "少年有请": {"12598", "12700"},
}

CONFLICT_EXCLUDED = {
    "AI芯片": {"12224", "12251", "12276"},
}

EXPECTED_DATE_COUNTS = {
    "2026-04-24": 54,
    "2026-04-25": 197,
    "2026-04-26": 35,
}

EXPECTED_CONTAINER_COUNTS = {
    "新生论坛": 96,
    "热带雨林": 57,
    "青年团聚": 48,
    "探索空间": 44,
    "思想约会": 20,
    "青春舞台": 13,
    "星空露营": 4,
    "热力运动": 4,
}

SEARCH_CASES = [
    {"name": "date_waytoagi_opening", "q": "WaytoAGI", "date": "2026-04-24", "include": {"12432"}, "exclude": {"12430"}},
    {"name": "container_waytoagi_explorer", "q": "WaytoAGI", "container": "探索空间", "include": {"12446"}, "exact": {"12446"}},
    {"name": "container_agent_forum", "q": "Agent", "container": "新生论坛", "include": {"12430", "12361"}},
    {"name": "topic_education_date", "date": "2026-04-25", "topic": ["education"], "include": {"12243", "12267", "12415"}},
    {"name": "topic_hardware_date", "date": "2026-04-25", "topic": ["robotics-hardware"], "include": {"12446", "12375"}},
    {"name": "travel_mindnet", "q": "旅行", "container": "思想约会", "include": {"12224"}},
    {"name": "next_gen_public_voice", "q": "社会听到更多青年人的声音", "container": "新生论坛", "include": {"12688"}},
    {"name": "rainforest_public_space", "q": "AI生成公共空间", "include": {"12248"}},
    {"name": "accessibility_playground_unit", "q": "2050无障碍游乐场", "include": {"12507"}},
]

UNIT_CASES = [
    {"name": "painting_truth_unit", "q": "绘画的真理", "min_units": 1},
    {"name": "future_programming_unit", "q": "未来编程", "min_units": 1},
    {"name": "sustainable_youth_unit", "q": "童星未来", "min_units": 1},
    {"name": "young_director_unit", "q": "青年导演 X AI", "min_units": 1},
    {"name": "ai_jargon_unit", "q": "黑话", "min_units": 1},
    {"name": "four_hundred_boxes_unit", "q": "四百盒子社区", "min_units": 1},
    {"name": "afterparty_unit", "q": "AfterParty", "min_units": 1},
]

SOURCE_CASES = [
    {"name": "source_deskclaw", "q": "DeskClaw", "min_sources": 1, "include": {"12361", "12258", "12446"}},
    {"name": "source_kaiyun_space", "q": "开运集团", "min_sources": 1, "include": {"12326", "12657", "12654", "12653"}},
    {"name": "source_three_wishes", "q": "三个愿望", "min_sources": 1, "include": {"12207", "12206", "12437", "12439"}},
    {"name": "source_pass_guide", "q": "2050PASS", "min_sources": 1},
    {"name": "source_linggan_trade", "q": "灵感交易所", "min_sources": 1, "include": {"12206"}},
]

ARTICLE_UNIT_COMPLETE_URLS = {
    "https://mp.weixin.qq.com/s/w1DwPt9yp_h1Cl1wgvJEuw",
    "https://mp.weixin.qq.com/s/0pk6F8FvoqjysXBApdrrdA",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def ids_from_search(
    query: str = "",
    *,
    date: str | None = None,
    topic: list[str] | None = None,
    container: str | None = None,
    limit: int = 80,
) -> set[str]:
    command = [sys.executable, str(SCRIPT)]
    if query:
        command.extend(["--q", query])
    if date:
        command.extend(["--date", date])
    if topic:
        for item in topic:
            command.extend(["--topic", item])
    if container:
        command.extend(["--container", container])
    command.extend(["--limit", str(limit)])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    return set(re.findall(r"/activity/(\d+)", completed.stdout))


def unit_count_from_search(query: str) -> int:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "80"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    match = re.search(r"matched_units=(\d+)", completed.stdout)
    if not match:
        fail(f"query {query} did not report matched_units")
    return int(match.group(1))


def source_count_from_search(query: str) -> int:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "80"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    match = re.search(r"matched_sources=(\d+)", completed.stdout)
    if not match:
        fail(f"query {query} did not report matched_sources")
    return int(match.group(1))


def main() -> int:
    missing = [path.relative_to(ROOT).as_posix() for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    activities = load_json(REF / "activity_index.min.json")
    crosswalk = load_json(REF / "article_activity_crosswalk.json")
    evidence = load_json(REF / "article_evidence_index.json")
    articles = load_json(REF / "articles_index.json")
    aliases = load_json(MANUAL / "article_aliases.json")

    if len(activities) < 286:
        fail(f"activity index has {len(activities)} rows, expected at least 286")
    if len(articles) < 77:
        fail(f"article index has {len(articles)} rows, expected at least 77")
    counts = evidence.get("counts", {})
    expected_evidence_counts = {
        "articles_csv_rows": 77,
        "activity_rows": 286,
        "result_markdown_files": 82,
        "batch_success": 12,
        "batch_failed": 1,
        "batch_skipped": 69,
        "matched_to_articles_csv": 77,
        "unmatched_articles_csv": 0,
    }
    for key, expected in expected_evidence_counts.items():
        if counts.get(key) != expected:
            fail(f"article_evidence_index count {key} expected {expected}, got {counts.get(key)}")
    if counts.get("manual_reviewed") != 82:
        fail(f"article_evidence_index manual_reviewed expected 82, got {counts.get('manual_reviewed')}")
    source_years = {str(record.get("article_published_at", ""))[:4] for record in evidence.get("records", []) if record.get("article_published_at")}
    if source_years != {"2026"}:
        fail(f"article evidence should only use 2026 article publish years, got {sorted(source_years)}")
    if any("search_text" in record for record in evidence.get("records", [])):
        fail("article_evidence_index should not carry source body excerpts in search_text")
    if any(not isinstance(record.get("search_terms"), list) for record in evidence.get("records", [])):
        fail("article_evidence_index records must carry compact search_terms lists")
    if not isinstance(crosswalk, dict) or not crosswalk.get("records"):
        fail("article_activity_crosswalk.json must be an object with non-empty records")
    forbidden_full_index = REF / ("activity_index." + "full.json")
    if forbidden_full_index.exists():
        fail("full activity index should not be packaged in the default skill")
    if any((REF / "article_ocr").glob("*.md")):
        fail("raw article_ocr markdown should not be packaged in the default skill")

    activity_ids = {str(item.get("activity_id")) for item in activities}
    date_counts = {}
    container_counts = {}
    for item in activities:
        date_counts[item.get("date")] = date_counts.get(item.get("date"), 0) + 1
        container_counts[item.get("container")] = container_counts.get(item.get("container"), 0) + 1
        if item.get("date") not in EXPECTED_DATE_COUNTS:
            fail(f"unexpected activity date: {item.get('date')} for {item.get('activity_id')}")
    if date_counts != EXPECTED_DATE_COUNTS:
        fail(f"date distribution changed: {date_counts}")
    if container_counts != EXPECTED_CONTAINER_COUNTS:
        fail(f"container distribution changed: {container_counts}")

    curation_text = (MANUAL / "article_curation.md").read_text(encoding="utf-8")
    curation_ids = set(re.findall(r"`(\d{5})`", curation_text))
    missing_curation_ids = sorted(curation_ids - activity_ids)
    if missing_curation_ids:
        fail(f"manual curation references unknown activity IDs: {missing_curation_ids}")

    evidence_ids = {
        str(activity_id)
        for record in evidence.get("records", [])
        for activity_id in record.get("matched_activity_ids", [])
    }
    for record in evidence.get("records", []):
        for rule in record.get("query_activity_rules", []):
            evidence_ids.update(str(activity_id) for activity_id in rule.get("activity_ids", []))
    missing_evidence_ids = sorted(evidence_ids - activity_ids)
    if missing_evidence_ids:
        fail(f"article evidence references unknown activity IDs: {missing_evidence_ids}")

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
        if dirty_query == "2025" and source_count_from_search(dirty_query) != 0:
            fail("query 2025 should not return source matches in the default 2050@2026 route scope")

    for case in SEARCH_CASES:
        actual_ids = ids_from_search(
            case.get("q", ""),
            date=case.get("date"),
            topic=case.get("topic"),
            container=case.get("container"),
        )
        missing = case.get("include", set()) - actual_ids
        if missing:
            fail(f"case {case['name']} missing IDs: {sorted(missing)}")
        unexpected = actual_ids & case.get("exclude", set())
        if unexpected:
            fail(f"case {case['name']} unexpectedly returned IDs: {sorted(unexpected)}")
        expected_exact = case.get("exact")
        if expected_exact is not None and actual_ids != expected_exact:
            fail(f"case {case['name']} expected exact IDs {sorted(expected_exact)}, got {sorted(actual_ids)}")

    for case in UNIT_CASES:
        actual_units = unit_count_from_search(case["q"])
        if actual_units < case["min_units"]:
            fail(f"case {case['name']} expected at least {case['min_units']} unit matches, got {actual_units}")

    for case in SOURCE_CASES:
        actual_sources = source_count_from_search(case["q"])
        if actual_sources < case["min_sources"]:
            fail(f"case {case['name']} expected at least {case['min_sources']} source matches, got {actual_sources}")
        include = case.get("include", set())
        if include:
            actual_ids = ids_from_search(case["q"])
            missing = include - actual_ids
            if missing:
                fail(f"source case {case['name']} missing IDs from search path: {sorted(missing)}")

    for record in crosswalk.get("records", []):
        if record.get("article_url") not in ARTICLE_UNIT_COMPLETE_URLS:
            continue
        for unit in record.get("units", []):
            section_title = unit.get("section_title", "")
            if not section_title:
                fail(f"article unit without section title in {record.get('article_title')}")
            actual_units = unit_count_from_search(section_title)
            if actual_units < 1:
                fail(f"article unit is not searchable: {section_title}")

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

    print("OK: ask2050 packaged data and search path passed")
    print(f"activities={len(activities)} articles={len(articles)} raw_ocr_packaged=0")
    print(f"manual_curation_ids={len(curation_ids)} alias_keys={len(aliases)} manual_reviewed_sources={counts.get('manual_reviewed')}")
    checked_article_units = sum(
        len(record.get("units", []))
        for record in crosswalk.get("records", [])
        if record.get("article_url") in ARTICLE_UNIT_COMPLETE_URLS
    )
    print(f"search_cases={len(EXPECTED_ALIAS_IDS) + len(SEARCH_CASES) + len(UNIT_CASES) + len(SOURCE_CASES) + checked_article_units + 2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
