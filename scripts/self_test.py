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
SOURCE_CHANNELS_SCRIPT = ROOT / "scripts" / "source_channels.py"


REQUIRED_FILES = [
    ROOT / "SKILL.md",
    REF / "tashan_world_bridge.md",
    REF / "activity_index.min.json",
    REF / "activity_facets.json",
    REF / "article_activity_crosswalk.json",
    REF / "article_facets.json",
    REF / "article_evidence_index.json",
    REF / "articles_index.json",
    REF / "extraction_schema.md",
    MANUAL / "article_curation.md",
    MANUAL / "article_aliases.json",
    SCRIPT,
    SOURCE_CHANNELS_SCRIPT,
]

FORBIDDEN_REFERENCE_DOCS = {
    "coverage_report.md",
    "evidence_status.md",
    "source_inventory.md",
    "tag_index.md",
    "test_report.md",
}

ALLOWED_TOP_LEVEL = {
    ".git",
    ".gitignore",
    "SKILL.md",
    "agents",
    "assets",
    "references",
    "scripts",
}

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
    {"name": "multi_container_or_mindnet_explorer", "q": "思想约会 探索空间", "include": {"12243", "12404"}},
    {"name": "multi_container_or_forum_rainforest", "q": "新生论坛 热带雨林", "include": {"12636", "12261"}},
    {"name": "facet_low_energy", "q": "低能量用户", "include": {"12276"}},
    {"name": "facet_demo_audience", "q": "想看现场 demo", "include": {"12446"}},
    {"name": "facet_hands_on", "q": "动手工作坊", "include": {"12261", "12446"}},
    {"name": "facet_solo_ai_booth", "q": "一个人也能参加 AI 展台", "include": {"12375"}},
    {"name": "natural_non_technical_art_relax", "q": "不懂AI 艺术 放松", "include": {"12221", "12378"}},
    {"name": "natural_hardware_soft_constraint", "q": "硬件 低强度 看展体验", "include": {"12375", "12446"}},
    {"name": "natural_networking_hardware", "q": "我想找人合作 做AI硬件", "include": {"12375", "12446"}},
]

RANKED_CASES = [
    {"name": "hardware_hands_on_top", "q": "AI 硬件 动手工作坊", "first": "12375"},
]

OUTPUT_CASES = [
    {"name": "logistics_source_output", "q": "2050PASS 交通 餐饮", "require": ["文章线索", "公众号"], "forbid": ["source |", "matched_activity_ids", "@2025@2026"]},
    {"name": "article_unit_output", "q": "AI生成公共空间", "require": ["文章小节", "来源文章"], "forbid": ["unit |", "matched_activity_ids", "unknown"]},
    {"name": "activity_output_labels", "q": "WaytoAGI", "require": ["标签:", "推荐画像:", "来源:"], "forbid": ["tags:", "profile:", "summary:", "url:"]},
    {"name": "first_time_itinerary_has_forum", "q": "第一次来 2050 安排一天", "require": ["新生论坛", "热带雨林"], "forbid": ["source |", "matched_activity_ids"]},
    {"name": "evening_itinerary_keeps_forum_anchor", "q": "晚上 放松 露营 音乐 2050 安排一天", "require": ["新生论坛", "星空露营"], "forbid": ["source |", "matched_activity_ids"]},
    {"name": "networking_query_has_connection_places", "q": "我想找人合作 做AI硬件", "require": ["探索空间", "推荐画像:"], "forbid": ["source |", "matched_activity_ids"]},
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
    {"name": "source_logistics_pass_traffic_food", "q": "2050PASS 交通 餐饮", "min_sources": 2},
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
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "80", "--debug"],
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
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "80", "--debug"],
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


def first_activity_id_from_search(query: str) -> str | None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--q", query, "--limit", "10"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    match = re.search(r"/activity/(\d+)", completed.stdout)
    return match.group(1) if match else None


def output_from_search(query: str, *, limit: int = 5) -> str:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--q", query, "--limit", str(limit)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"search_activities.py failed for {query}: {completed.stderr.strip()}")
    return completed.stdout


def main() -> int:
    unexpected_top_level = sorted(
        path.name for path in ROOT.iterdir() if path.name not in ALLOWED_TOP_LEVEL
    )
    if unexpected_top_level:
        fail(f"unexpected top-level skill artifacts: {unexpected_top_level}")

    forbidden_docs = sorted(path.name for path in REF.glob("*.md") if path.name in FORBIDDEN_REFERENCE_DOCS)
    if forbidden_docs:
        fail(f"process/stat reference docs should not be packaged: {forbidden_docs}")

    missing = [path.relative_to(ROOT).as_posix() for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_phrase in [
        "scripts/search_activities.py",
        "不要把脚本输出原样粘给用户",
        "不要为了第一轮匹配整篇加载很大的 `by_topic` 或 `by_location` 文件",
        "认知主线：至少安排一个相关的新生论坛",
        "不要因为低压力活动更容易匹配，就在正常行程里省掉新生论坛",
        "路线里都先找一个相关新生论坛做认知锚点",
        "好的 2050 路线要有节奏",
        "低能量用户，不是删除新生论坛，而是降低强度",
        "先判断用户真正要解决什么",
        "要像一个熟悉 2050 的同伴",
        "区分事实和推荐判断",
        "用户想找人或合作时，要告诉他去哪里遇见人、适合用什么开场问题",
        "用户问交通、通行证、吃饭、地图时，先解决实际问题",
        "他山世界/OpenClaw 是后台画像和身份通道，不是用户对话里的流程提示",
        "不要问用户“是否已接入”",
        "后台如果已经有画像标签，静默用于匹配",
        "如果用户没有给足标签，主动问 1-3 个最影响推荐的问题",
        "个性化路线也不要先谈后台接入",
    ]:
        if required_phrase not in skill_text:
            fail(f"SKILL.md missing service guidance: {required_phrase}")

    user_visible_forbidden = [
        "先确认：你是否已完成",
        "未接入也可以先给你一版预览路线",
        "你的参与标签：",
    ]
    for forbidden_phrase in user_visible_forbidden:
        if forbidden_phrase in skill_text:
            fail(f"SKILL.md still exposes backend onboarding wording: {forbidden_phrase}")
    for forbidden_phrase in ["匹配分", "N 个活动", "意图速查不是", "排除新生论坛", "--debug", "测试用例", "打包过程"]:
        if forbidden_phrase in skill_text:
            fail(f"SKILL.md still exposes implementation/debug wording: {forbidden_phrase}")

    agent_yaml = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    for forbidden_phrase in ["先确认", "轻量接入", "OpenClaw"]:
        if forbidden_phrase in agent_yaml:
            fail(f"agents/openai.yaml default prompt exposes backend onboarding wording: {forbidden_phrase}")

    bridge_text = (REF / "tashan_world_bridge.md").read_text(encoding="utf-8")
    for required_phrase in [
        "## 四、启动、刷新与认证",
        "npm install -g topiclab-cli --registry=https://registry.npmmirror.com",
        "npm update -g topiclab-cli --registry=https://registry.npmmirror.com",
        "topiclab session ensure --base-url https://world.tashan.chat --bind-key <skill_link_key> --json",
        "curl -fsSL -X POST https://world.tashan.chat/api/v1/auth/openclaw-guest",
        "bootstrap_path",
        "skill_path",
        "bind_key",
        "下载后的完整 skill 可直接替换本地缓存 skill",
        "临时账号升级",
        "当前 OpenClaw 已经可以直接稳定使用",
        "主动把注册链接或登录认领链接发给用户",
        "会自动把当前临时账号、OpenClaw 身份和已有分身打通到正式账号",
        "不询问“是否已接入他山世界/OpenClaw”",
        "如果后台已有画像，直接用于推荐",
    ]:
        if required_phrase not in bridge_text:
            fail(f"tashan_world_bridge.md missing OpenClaw auth guidance: {required_phrase}")

    route_guidance_files = [
        MANUAL / "recommendation_layer.md",
        REF / "route_templates" / "first_time_visitor.md",
        REF / "route_templates" / "hardware_robotics.md",
        REF / "route_templates" / "low_energy_social.md",
    ]
    for path in route_guidance_files:
        text = path.read_text(encoding="utf-8")
        if "新生论坛" not in text:
            fail(f"{path.relative_to(ROOT)} must mention 新生论坛 route anchoring")
        if path == MANUAL / "recommendation_layer.md":
            for required_phrase in [
                "低能量不是删除论坛的理由",
                "短听、可提前离场、只听最相关一场",
            ]:
                if required_phrase not in text:
                    fail(f"{path.relative_to(ROOT)} missing forum intensity guidance: {required_phrase}")

    size_budgets = {
        REF / "activity_facets.json": 360_000,
        REF / "article_facets.json": 90_000,
    }
    for path, max_bytes in size_budgets.items():
        if path.stat().st_size > max_bytes:
            fail(f"{path.relative_to(ROOT)} is too large: {path.stat().st_size} bytes > {max_bytes}")

    activities = load_json(REF / "activity_index.min.json")
    crosswalk = load_json(REF / "article_activity_crosswalk.json")
    activity_facets = load_json(REF / "activity_facets.json")
    article_facets = load_json(REF / "article_facets.json")
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
    facet_ids = set(activity_facets)
    if facet_ids != activity_ids:
        fail("activity_facets.json must cover exactly the packaged activity IDs")
    required_facet_fields = {
        "activity_id",
        "primary_topics",
        "secondary_topics",
        "experience_modes",
        "participation_style",
        "recommended_for",
        "intensity",
        "social_density",
        "planning_role",
        "time_pattern",
        "venue_context",
        "route_note",
        "source_level",
        "search_terms",
    }
    incomplete_facets = [
        activity_id
        for activity_id, facet in activity_facets.items()
        if not required_facet_fields.issubset(facet)
        or not facet.get("primary_topics")
        or not facet.get("experience_modes")
        or not facet.get("recommended_for")
    ]
    if incomplete_facets:
        fail(f"activity facets missing recommendation fields: {incomplete_facets[:10]}")
    if set(article_facets) != {record.get("result_file") for record in evidence.get("records", [])}:
        fail("article_facets.json must cover exactly the article evidence records")
    required_article_facet_fields = {
        "source_id",
        "article_url",
        "source_role",
        "linked_activity_ids",
        "communities_or_aliases",
        "extracted_topics",
        "experience_modes",
        "participation_style",
        "route_use",
        "confidence",
        "search_terms",
    }
    incomplete_article_facets = [
        source_id
        for source_id, facet in article_facets.items()
        if not required_article_facet_fields.issubset(facet)
        or not facet.get("source_role")
        or not facet.get("route_use")
    ]
    if incomplete_article_facets:
        fail(f"article facets missing recommendation fields: {incomplete_article_facets[:10]}")
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

    for case in RANKED_CASES:
        actual_first = first_activity_id_from_search(case["q"])
        if actual_first != case["first"]:
            fail(f"ranked case {case['name']} expected first ID {case['first']}, got {actual_first}")

    for case in OUTPUT_CASES:
        output = output_from_search(case["q"])
        missing = [text for text in case["require"] if text not in output]
        if missing:
            fail(f"output case {case['name']} missing display text: {missing}")
        forbidden = [text for text in case["forbid"] if text in output]
        if forbidden:
            fail(f"output case {case['name']} leaked internal display text: {forbidden}")

    source_channels = subprocess.run(
        [sys.executable, str(SOURCE_CHANNELS_SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if source_channels.returncode != 0:
        fail(f"source_channels.py failed: {source_channels.stderr.strip()}")
    for required_text in [
        "2050 官网活动页",
        "微信公众号文章",
        "本地抓取/OCR 结果",
        "节目/板块指南",
        "抓取/OCR 成功",
        "批处理中跳过",
        "后续更新顺序",
    ]:
        if required_text not in source_channels.stdout:
            fail(f"source_channels.py output missing: {required_text}")

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
        if "__pycache__" in path.parts or path.suffix == ".pyc":
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
