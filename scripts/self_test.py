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
PLAN_SCRIPT = ROOT / "scripts" / "plan_itinerary.py"
SOURCE_CHANNELS_SCRIPT = ROOT / "scripts" / "source_channels.py"
REBUILD_SLICES_SCRIPT = ROOT / "scripts" / "rebuild_reference_slices.py"
OPENCLAW_SMOKE_SCRIPT = ROOT / "scripts" / "openclaw_smoke_test.py"
EXTRACT_OFFICIAL_DETAIL_SCRIPT = ROOT / "scripts" / "extract_official_detail_terms.py"
IMPORT_NEWBORN_FORUM_SCRIPT = ROOT / "scripts" / "import_newborn_forum_article.py"
AUDIT_CROSS_REFERENCES_SCRIPT = ROOT / "scripts" / "audit_cross_references.py"


REQUIRED_FILES = [
    ROOT / "SKILL.md",
    REF / "tashan_world_bridge.md",
    OPENCLAW_SMOKE_SCRIPT,
    REF / "activity_index.min.json",
    REF / "activity_facets.json",
    REF / "focus_sessions.min.json",
    REF / "article_activity_crosswalk.json",
    REF / "article_facets.json",
    REF / "article_evidence_index.json",
    REF / "articles_index.json",
    REF / "extraction_schema.md",
    REF / "official_detail_terms.json",
    MANUAL / "article_curation.md",
    MANUAL / "article_aliases.json",
    MANUAL / "supplemental_events.json",
    SCRIPT,
    PLAN_SCRIPT,
    SOURCE_CHANNELS_SCRIPT,
    REBUILD_SLICES_SCRIPT,
    EXTRACT_OFFICIAL_DETAIL_SCRIPT,
    IMPORT_NEWBORN_FORUM_SCRIPT,
    AUDIT_CROSS_REFERENCES_SCRIPT,
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
    "2026-04-25": 198,
    "2026-04-26": 36,
}

EXPECTED_CONTAINER_COUNTS = {
    "新生论坛": 97,
    "热带雨林": 59,
    "青年团聚": 48,
    "探索空间": 44,
    "思想约会": 19,
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
    {"name": "latest_youth_waytoagi", "q": "WaytoAGI 社区 青年团聚", "date": "2026-04-24", "include": {"12432"}},
    {"name": "latest_youth_agent_builder", "q": "Agent Builder 青年团聚", "date": "2026-04-24", "include": {"12373"}},
    {"name": "latest_explorer_space_life", "q": "探索空间 太空 生活 航天", "date": "2026-04-25", "include": {"12657", "12724"}},
    {"name": "latest_explorer_chip", "q": "芯片 RISC-V 自己设计", "date": "2026-04-25", "include": {"12246"}},
    {"name": "latest_explorer_parent_ai", "q": "AI反哺 父母 养老", "date": "2026-04-25", "include": {"12753"}},
    {"name": "latest_explorer_mr", "q": "文旅 MR 空间计算", "date": "2026-04-25", "include": {"12235"}},
    {"name": "official_fshd_detail", "q": "FSHD 患者 罕见特殊人群", "include": {"12368"}},
    {"name": "official_family_movie_detail", "q": "家庭故事 小电影", "include": {"12344"}},
    {"name": "official_painting_truth_live", "q": "绘画的真理 观察力 想象力 创造力", "include": {"12787"}},
]

RANKED_CASES = [
    {"name": "hardware_hands_on_top", "q": "AI 硬件 动手工作坊", "first": "12375"},
    {"name": "focus_time_location_top", "q": "少数派 共创 13:00 贤云厅", "first": "12540"},
]

OUTPUT_CASES = [
    {"name": "logistics_source_output", "q": "2050PASS 交通 餐饮", "require": ["文章线索", "公众号"], "forbid": ["source |", "matched_activity_ids", "@2025@2026"]},
    {"name": "article_unit_output", "q": "AI生成公共空间", "require": ["文章小节", "来源文章"], "forbid": ["unit |", "matched_activity_ids", "unknown"]},
    {"name": "activity_output_labels", "q": "WaytoAGI", "require": ["标签:", "推荐画像:", "来源:"], "forbid": ["tags:", "profile:", "summary:", "url:"]},
    {"name": "first_time_itinerary_has_forum", "q": "第一次来 2050 安排一天", "require": ["新生论坛", "热带雨林"], "forbid": ["source |", "matched_activity_ids"]},
    {"name": "evening_itinerary_keeps_forum_anchor", "q": "晚上 放松 露营 音乐 2050 安排一天", "require": ["新生论坛", "星空露营"], "forbid": ["source |", "matched_activity_ids"]},
    {"name": "networking_query_has_connection_places", "q": "我想找人合作 做AI硬件", "require": ["探索空间", "推荐画像:"], "forbid": ["source |", "matched_activity_ids"]},
    {"name": "ai4science_query_has_focus_session", "q": "AI4Science 科研 博士 天文学", "require": ["重点 part:", "AGI4Science：正在生长的科学地图", "A区 2F 2050学习节(五云厅)"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "ai4science_report_tags", "q": "AI4Science 数学物理", "require": ["报告:", "AI如何解决上个世纪的数学与物理", "杜伟韬"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "eldercare_focus_report", "q": "助老智能体", "require": ["青智助老", "智慧未来：助老智能体共建", "A区 1F 慧云厅"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "agentic_building_focus_location", "q": "AI协商生成公共空间", "require": ["Agentic Building", "篮球场边", "设定AI性格"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "latest_waytoagi_youth_focus", "q": "WaytoAGI 社区 青年团聚", "require": ["重点 part:", "WaytoAGI 社区青年团聚", "A区 3F 蔚云厅"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "latest_space_life_focus", "q": "探索空间 太空 生活 航天", "require": ["重点 part:", "未来在地球以外：星际生活场景体验", "探索空间1号展位"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "latest_parent_ai_focus", "q": "AI反哺 父母 养老", "require": ["重点 part:", "AI反哺计划：年轻人能用AI为父母做些什么", "探索空间74号展位"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "supplemental_tashan_forum", "q": "他山 国科大 中科院", "require": ["补充活动线索", "他山青年论坛", "A区 3F 青云厅", "中国科学院大学他山学科交叉创新协会"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "shale_report_article_unit", "q": "页岩层系 龟兔赛跑", "require": ["文章小节", "页岩油气富集机理", "页岩层系中持续百万年的\"龟兔赛跑\"", "A区 2F 360环屏(千人云栖厅)"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "earth_sustainability_report", "q": "AI与地球可持续发展 Nancy House", "require": ["文章小节", "AI与地球可持续发展新生论坛", "机遇与平衡", "Nancy House"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "opc_report_focus", "q": "AI + OPC 文科生 Agent 协作赚到钱", "require": ["重点 part:", "AI + OPC：一个人的 AI 时代生存指南", "AI 时代的文科生：如何跟 Agent 协作并赚到钱", "周晨"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "qian_xuesen_complexity_report", "q": "钱学森 复杂科学 魏云初", "require": ["重点 part:", "钱学森读书会", "钱学森与复杂科学", "魏云初"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
    {"name": "tashan_article_parts", "q": "他山青年论坛", "require": ["补充活动线索", "文章小节", "AI 时代科研协作模式如何重构", "国科大"], "forbid": ["source |", "matched_activity_ids", "D:/2050"]},
]

EXPECTED_FORUM_LOCATIONS = {
    "12260": "A区 3F 皓云厅",
    "12491": "A区 1F 贤云厅",
    "12309": "A区 2F 2050学习节(五云厅)",
    "12402": "A区 2F 2050学习节(五云厅)",
    "12298": "A区 1F 慧云厅",
    "12275": "A区 1F 贤云厅",
    "12741": "A区 2F 360环屏(千人云栖厅)",
    "12429": "A区 3F 坚云厅",
    "12633": "A区 3F 青云厅",
    "12555": "A区 1F 慧云厅",
    "12257": "A区 2F 360环屏(千人云栖厅)",
    "12669": "A区 3F 德云厅",
    "12308": "A区 1F 贤云厅",
    "12411": "A区 1F 慧云厅",
    "12360": "A区 3F 风云厅",
    "12416": "A区 1F 慧云厅",
    "12263": "A区 2F 360环屏(千人云栖厅)",
    "12630": "A区 2F 360环屏(千人云栖厅)",
    "12284": "A区 3F 德云厅",
    "12365": "A区 3F 德云厅",
    "12288": "A区 3F 青云厅",
    "12334": "A区 2F 2050学习节(五云厅)",
    "12241": "A区 2F 360环屏(千人云栖厅)",
    "12372": "A区 3F 青云厅",
    "12314": "A区 3F 皓云厅",
    "12787": "云栖小镇国际会展中心 A区一楼 智云厅",
}

ITINERARY_PROFILE = (
    "身份 AI4S科研博士生 背景 天文学 AI交叉 兴趣 科普科教 开源技术 "
    "社区运营 哲学思考 偏好 深度讨论 小团体交流 有动手体验"
)

UNIT_CASES = [
    {"name": "painting_truth_unit", "q": "绘画的真理", "min_units": 1},
    {"name": "future_city_unit", "q": "未来城邦", "min_units": 1},
    {"name": "sustainable_future_unit", "q": "重塑未来 可持续发展", "min_units": 1},
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
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
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


def plan_text(plan: dict) -> str:
    return json.dumps(plan, ensure_ascii=False).lower()


def route_item_text(item: dict) -> str:
    return " ".join(
        str(item.get(key, ""))
        for key in ["title", "container", "location", "reason", "why_fit", "official_time", "suggested_window"]
    ).lower()


def route_contains_any(plan: dict, keywords: list[str]) -> bool:
    text = plan_text(plan)
    return any(keyword.lower() in text for keyword in keywords)


def item_contains_any(item: dict, keywords: list[str]) -> bool:
    text = route_item_text(item)
    return any(keyword.lower() in text for keyword in keywords)


def count_items_with_any(plan: dict, keywords: list[str]) -> int:
    return sum(1 for item in plan.get("items", []) if item_contains_any(item, keywords))


def assert_route_quality(plan: dict, *, name: str, topic_keywords: list[str], min_topic_items: int = 2) -> None:
    items = plan.get("items", [])
    if not items:
        fail(f"plan_itinerary.py profile {name} produced no route items")
    if not any(item.get("container") == "新生论坛" for item in items):
        fail(f"plan_itinerary.py profile {name} lacks forum anchor")
    if not route_contains_any(plan, topic_keywords):
        fail(f"plan_itinerary.py profile {name} lacks topic-relevant route text")
    if count_items_with_any(plan, topic_keywords) < min_topic_items:
        fail(f"plan_itinerary.py profile {name} does not sustain topic relevance across the route")
    for item in items:
        if re.search(r"2[4-9]:", str(item.get("suggested_window", ""))):
            fail(f"plan_itinerary.py profile {name} exposed post-midnight clock in default route: {item.get('suggested_window')}")


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

    cross_audit = subprocess.run(
        [sys.executable, str(AUDIT_CROSS_REFERENCES_SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if cross_audit.returncode != 0:
        fail(cross_audit.stderr.strip() or cross_audit.stdout.strip())

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_phrase in [
        "scripts/search_activities.py",
        "不要把脚本输出原样粘给用户",
        "如果 `--topic` 在当前运行环境里不可用",
        "改用 `--q` 写入同义主题词、身份和需求重新检索",
        "不要为了第一轮匹配整篇加载很大的 `by_topic` 或 `by_location` 文件",
        "认知主线：至少安排一个相关的新生论坛",
        "不要因为低压力活动更容易匹配，就在正常行程里省掉新生论坛",
        "新生论坛不是固定模板",
        "用户画像不同，论坛锚点和后续实践都应该不同",
        "路线里都先找一个相关新生论坛做认知锚点",
        "好的 2050 路线要有节奏",
        "行程规划必须先过这些硬约束",
        "人工复盘必须覆盖这些点",
        "每一站都要能回到用户明确说过的身份、兴趣、日期、精力或合作需求",
        "主线宁可少而准",
        "换场太紧时，把后一站写成备选",
        "用户问多日、三天、全程、完整 2050 路线时",
        "对每个在场日期分别运行 `plan_itinerary.py`",
        "再做跨日综合",
        "每日主题 + 主路线 + 可替换项 + 体力提醒",
        "同一时间只能有一个主去处",
        "官方只给总场馆时，不要编厅号",
        "不要无故把晨读、晨跑、露营等轻活动塞进路线",
        "python scripts/plan_itinerary.py",
        "低能量用户，不是删除新生论坛，而是降低强度",
        "先判断用户真正要解决什么",
        "用户说“睡觉、不想参加、躺平、只想休息”时，尊重低参与意愿",
        "用户说“行动不便、不想跨区、少走路”时，地点和换场成本优先",
        "用户说“效率优先、参加最多、高密度”时，才增加活动密度",
        "用户说“晨型、早起、晨读”时，可以安排 07:00-08:00 等早间活动",
        "用户说“早睡、晚上回酒店、不想太晚”时，不安排 19:00 后主活动",
        "搜索没有结果时，不要空白返回",
        "要像一个熟悉 2050 的同伴",
        "区分事实和推荐判断",
        "用户想找人或合作时，要告诉他去哪里遇见人、适合用什么开场问题",
        "用户问交通、通行证、吃饭、地图时，先解决实际问题",
        "默认先确保他山世界/OpenClaw 轻量身份通道可用",
        "它是后台画像和身份前置，不是用户对话里的流程提示",
        "也不是可随意跳过的推荐选项",
        "不要问用户“是否已接入”",
        "后台如果已经有画像标签，静默用于匹配",
        "新会话、新安装或发现本地会话不可用时",
        "默认先完成轻量接入",
        "常规首入口是用户只安装了 `https://github.com/TashanGKD/ask2050`",
        "这种情况先做一次访客 bootstrap",
        "再用 `topiclab session ensure` 持久化",
        "接入失败不阻塞首轮推荐",
        "继续用 ask2050 内置日程、文章线索和检索脚本直接回答当前 2050 问题",
        "不要把用户转去执行 `topiclab help ask`",
        "不要用安装、刷新或命令文本代替推荐结果",
        "如果用户没有给足标签，主动问 1-3 个最影响推荐的问题",
        "个性化路线也不要先谈后台接入",
        "references/manual/supplemental_events.json",
        "不要把它说成官网活动表里的正式条目",
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
        "默认接入策略",
        "默认先建立他山世界/OpenClaw 轻量身份通道",
        "不要把它当成用户可选项",
        "常规首入口是用户只安装了 `https://github.com/TashanGKD/ask2050`",
        "先走访客 bootstrap",
        "带 `?key=...` 的专属链接只是已经完成分发后的快捷路径，不是首轮前提",
        "默认需要本机处理他山世界/OpenClaw 会话",
        "topiclab session ensure --base-url https://world.tashan.chat --bind-key <skill_link_key> --json",
        "curl -fsSL -X POST https://world.tashan.chat/api/v1/auth/openclaw-guest",
        "bootstrap_path",
        "skill_path",
        "bind_key",
        "claim_register_path",
        "claim_login_path",
        "https://world.tashan.chat<claim_register_path>",
        "https://world.tashan.chat<claim_login_path>",
        "下载后的完整 skill 可直接替换本地缓存 skill",
        "临时账号升级",
        "当前 OpenClaw 已经可以直接稳定使用",
        "主动把注册链接或登录认领链接发给用户",
        "会自动把当前临时账号、OpenClaw 身份和已有分身打通到正式账号",
        "不要把 `claim_token`、`bind_key` 或 `skill_path` 当作用户需要理解的内容",
        "不询问“是否已接入他山世界/OpenClaw”",
        "如果后台已有画像，直接用于推荐",
        "默认使用本文件建立后台身份通道",
        "普通推荐回答不展示命令、key 或接入状态",
        "接入完成后不要把当前 2050 问题转交给 `topiclab help ask`",
        "当前活动推荐、日程解释和路线规划必须继续由 ask2050 的内置资料、检索脚本和分层证据直接完成",
        "正常 2050 推荐不要依赖它生成答案",
        "python scripts/openclaw_smoke_test.py --agent-call",
        "只证明他山世界/OpenClaw 通道可用",
        "不代表当前 ask2050 的完整本地日程和推荐证据已经交给网站 agent",
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
                "主时间线必须无重叠",
                "地点精度优先",
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
    focus_sessions = load_json(REF / "focus_sessions.min.json")
    article_facets = load_json(REF / "article_facets.json")
    evidence = load_json(REF / "article_evidence_index.json")
    articles = load_json(REF / "articles_index.json")
    official_detail_terms = load_json(REF / "official_detail_terms.json")
    aliases = load_json(MANUAL / "article_aliases.json")
    supplemental_events = load_json(MANUAL / "supplemental_events.json")

    if len(activities) != 288:
        fail(f"activity index has {len(activities)} rows, expected 288 from current 2050 official list")
    if len(articles) < 77:
        fail(f"article index has {len(articles)} rows, expected at least 77")
    if set(official_detail_terms.get("activities", {})) != {str(item.get("activity_id")) for item in activities}:
        fail("official_detail_terms.json must cover exactly the packaged activity IDs")
    if len(focus_sessions) < 95:
        fail(f"focus_sessions.min.json has {len(focus_sessions)} rows, expected at least 95 curated focus sessions")
    counts = evidence.get("counts", {})
    expected_evidence_counts = {
        "articles_csv_rows": 77,
        "activity_rows": 285,
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

    required_supplemental_fields = {
        "supplemental_id",
        "title",
        "date",
        "time",
        "location",
        "summary",
        "organizer",
        "source_level",
        "source",
        "search_terms",
    }
    for event in supplemental_events:
        if not required_supplemental_fields.issubset(event):
            fail(f"supplemental event missing required fields: {event}")
        if event.get("source_level") != "user-supplied-manual":
            fail(f"supplemental event must be marked manual: {event.get('supplemental_id')}")
        if not isinstance(event.get("search_terms"), list) or len(event.get("search_terms", [])) < 5:
            fail(f"supplemental event needs searchable aliases: {event.get('supplemental_id')}")
        if str(event.get("date", "")) not in EXPECTED_DATE_COUNTS:
            fail(f"supplemental event date outside 2050@2026 scope: {event.get('supplemental_id')}")

    activity_ids = {str(item.get("activity_id")) for item in activities}
    required_activity_fields = {
        "activity_id",
        "title",
        "date",
        "time",
        "container",
        "location",
        "summary",
        "url",
    }
    incomplete_activities = []
    for item in activities:
        activity_id = str(item.get("activity_id"))
        if not required_activity_fields.issubset(item) or any(
            not str(item.get(field, "")).strip() for field in required_activity_fields
        ):
            incomplete_activities.append(activity_id)
            continue
        if not str(item.get("url", "")).startswith("https://2050.org/#/activity/"):
            fail(f"activity {activity_id} has non-official URL: {item.get('url')}")
    if incomplete_activities:
        fail(f"activity_index.min.json has incomplete core facts: {incomplete_activities[:10]}")

    missing_focus_parent_ids = sorted(
        str(item.get("parent_activity_id"))
        for item in focus_sessions
        if str(item.get("parent_activity_id")) not in activity_ids
    )
    if missing_focus_parent_ids:
        fail(f"focus_sessions.min.json references unknown activity IDs: {missing_focus_parent_ids}")
    focus_keys = {}
    duplicate_focus_keys = []
    for item in focus_sessions:
        key = (
            str(item.get("parent_activity_id")),
            str(item.get("title")),
            str(item.get("date")),
            str(item.get("location")),
        )
        if key in focus_keys:
            duplicate_focus_keys.append((key, focus_keys[key], item.get("session_id")))
        focus_keys[key] = item.get("session_id")
    if duplicate_focus_keys:
        fail(f"focus_sessions.min.json has duplicate focus sessions: {duplicate_focus_keys[:5]}")
    activity_lookup = {str(item.get("activity_id")): item for item in activities}
    location_mismatches = []
    for activity_id, expected_location in EXPECTED_FORUM_LOCATIONS.items():
        activity = activity_lookup.get(activity_id)
        if not activity:
            location_mismatches.append((activity_id, "missing", expected_location))
        elif activity.get("location") != expected_location:
            location_mismatches.append((activity_id, activity.get("location"), expected_location))
    if location_mismatches:
        fail(f"curated forum locations regressed: {location_mismatches[:10]}")

    for item in focus_sessions:
        for field in ["session_id", "parent_activity_id", "title", "container", "date", "time", "location", "summary", "source"]:
            if not item.get(field):
                fail(f"focus session missing {field}: {item}")
        for field in ["recommended_for", "topic_tags"]:
            if not isinstance(item.get(field), list) or not item.get(field):
                fail(f"focus session missing {field}: {item.get('session_id')}")
        if not isinstance(item.get("talks"), list) or not item.get("talks"):
            fail(f"focus session needs talk-level tags: {item.get('session_id')}")
        for talk in item.get("talks", []):
            if not isinstance(talk, dict) or not talk.get("title") or not talk.get("tags"):
                fail(f"focus session talk needs title and tags: {item.get('session_id')}")
            if talk.get("tags") == ["general"]:
                fail(f"focus session talk only has a generic tag: {item.get('session_id')}")

    newborn_record = next(
        (record for record in crosswalk.get("records", []) if record.get("article_url") == "https://mp.weixin.qq.com/s/0pk6F8FvoqjysXBApdrrdA"),
        None,
    )
    if not newborn_record:
        fail("newborn forum article crosswalk is missing")
    newborn_units = newborn_record.get("units", [])
    if len(newborn_units) < 100:
        fail(f"newborn forum crosswalk has {len(newborn_units)} units, expected full hall-level extraction")
    newborn_talks = sum(len(unit.get("talks", [])) for unit in newborn_units)
    if newborn_talks < 450:
        fail(f"newborn forum crosswalk has {newborn_talks} talks, expected report-level extraction")
    for unit in newborn_units:
        for field in ["section_title", "date_tags", "time_range", "location_hint", "topic_tags", "talks", "confidence"]:
            if not unit.get(field):
                fail(f"newborn forum unit missing {field}: {unit}")
        for talk in unit.get("talks", []):
            if not talk.get("title") or not talk.get("tags") or talk.get("tags") == ["general"]:
                fail(f"newborn forum talk needs non-generic tags: {unit.get('section_title')}")
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
        or not facet.get("participation_style")
        or not facet.get("route_note")
        or not facet.get("search_terms")
        or facet.get("activity_id") != activity_id
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

    for query in ["他山", "国科大", "中科院", "中国科学院大学", "人工智能驱动的科研协作与科教升级"]:
        output = output_from_search(query)
        for required_text in ["补充活动线索", "他山青年论坛", "A区 3F 青云厅"]:
            if required_text not in output:
                fail(f"supplemental query {query} missing display text: {required_text}")

    itinerary = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", ITINERARY_PROFILE, "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if itinerary.returncode != 0:
        fail(f"plan_itinerary.py failed: {itinerary.stderr.strip() or itinerary.stdout.strip()}")
    try:
        plan = json.loads(itinerary.stdout)
    except json.JSONDecodeError as exc:
        fail(f"plan_itinerary.py did not return valid JSON: {exc}")
    plan_text = json.dumps(plan, ensure_ascii=False)
    for required_text in ["AI4Science 专场", "AGI4Science：正在生长的科学地图", "A区 2F 2050学习节(五云厅)", "把AI装进硬件里", "suggested_window", "official_time"]:
        if required_text not in plan_text:
            fail(f"plan_itinerary.py output missing expected route element: {required_text}")
    if "AI4Science 专场 | 云栖小镇国际会展中心（官方地点仅到总场馆" in plan_text:
        fail("plan_itinerary.py still uses generic venue for AI4Science instead of the focused session")
    for forbidden_text in ["晨读", "带上喜欢的文字"]:
        if forbidden_text in plan_text:
            fail(f"plan_itinerary.py added unrelated low-energy starter: {forbidden_text}")
    windows: list[tuple[int, int]] = []
    for item in plan.get("items", []):
        window = str(item.get("suggested_window", ""))
        match = re.match(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})$", window)
        if not match:
            fail(f"plan_itinerary.py invalid suggested_window: {window}")
        start = int(match.group(1)) * 60 + int(match.group(2))
        end = int(match.group(3)) * 60 + int(match.group(4))
        if end <= start:
            fail(f"plan_itinerary.py non-positive window: {window}")
        if any(start < other_end and other_start < end for other_start, other_end in windows):
            fail(f"plan_itinerary.py has overlapping main route window: {window}")
        windows.append((start, end))
        location = str(item.get("location", ""))
        if location in {"云栖小镇国际会展中心", "云栖小镇"}:
            fail(f"plan_itinerary.py kept generic location without caveat: {item.get('title')}")
    if not any(item.get("container") == "新生论坛" for item in plan.get("items", [])):
        fail("plan_itinerary.py route lacks forum anchor")

    route_profiles = {
        "ai4s": {
            "profile": ITINERARY_PROFILE,
            "topic_keywords": ["ai4science", "agi4science", "科学", "科研", "物理", "数学"],
            "min_topic_items": 1,
            "forbid": ["2050说媒", "OPC Night"],
        },
        "education": {
            "profile": "第一次来2050 喜欢教育 科普 社区运营 小团体交流",
            "topic_keywords": ["教育", "科普", "学习", "课程", "教研", "高校"],
            "min_topic_items": 2,
            "forbid": ["声音橡皮泥", "离谱村音乐会"],
        },
        "hardware": {
            "profile": "第一次来2050 硬件 机器人 动手体验 开源技术",
            "topic_keywords": ["硬件", "机器人", "芯片", "具身", "制造", "openclaw", "maker"],
            "min_topic_items": 2,
        },
        "philosophy": {
            "profile": "第一次来2050 哲学 人文 深聊 AI教育 社会科学",
            "topic_keywords": ["哲学", "思想", "人文", "社会科学", "教育", "深聊"],
            "min_topic_items": 2,
            "forbid": ["离谱村音乐会"],
        },
    }
    forum_ids = set()
    for name, case in route_profiles.items():
        completed = subprocess.run(
            [sys.executable, str(PLAN_SCRIPT), "--profile", case["profile"], "--date", "2026-04-25", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            fail(f"plan_itinerary.py profile {name} failed: {completed.stderr.strip() or completed.stdout.strip()}")
        case_plan = json.loads(completed.stdout)
        case_text = json.dumps(case_plan, ensure_ascii=False)
        forums = [item for item in case_plan.get("items", []) if item.get("container") == "新生论坛"]
        assert_route_quality(
            case_plan,
            name=name,
            topic_keywords=case["topic_keywords"],
            min_topic_items=case.get("min_topic_items", 2),
        )
        forum_id = str(forums[0].get("activity_id"))
        forum_ids.add(forum_id)
        for forbidden_text in case.get("forbid", []):
            if forbidden_text in case_text:
                fail(f"plan_itinerary.py profile {name} included mismatched route text: {forbidden_text}")
    if len(forum_ids) < 3:
        fail(f"plan_itinerary.py profiles are not differentiated enough; forum anchors={sorted(forum_ids)}")

    constraint_profiles = {
        "no_participation": "只想睡觉 不想参加 躺平 休息",
        "mobility_limited": "行动不便 不想跨区 少走路 第一次来",
        "max_density": "效率优先 想参加最多 高密度 AI 硬件 社区",
        "morning_person": "晨型人 早起 喜欢晨读 教育 科普",
        "early_sleep": "早睡 晚上回酒店 不想太晚 教育 科普",
    }
    constraint_plans = {}
    for name, profile in constraint_profiles.items():
        completed = subprocess.run(
            [sys.executable, str(PLAN_SCRIPT), "--profile", profile, "--date", "2026-04-25", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            fail(f"plan_itinerary.py constraint profile {name} failed: {completed.stderr.strip() or completed.stdout.strip()}")
        constraint_plans[name] = json.loads(completed.stdout)
    if constraint_plans["no_participation"].get("items"):
        fail("plan_itinerary.py should not force activities for no-participation profile")
    if "不强行推荐" not in json.dumps(constraint_plans["no_participation"], ensure_ascii=False):
        fail("plan_itinerary.py no-participation profile lacks explicit respect for user intent")
    mobility_items = constraint_plans["mobility_limited"].get("items", [])
    if len(mobility_items) > 2:
        fail("plan_itinerary.py mobility-limited route should be short")
    mobility_zones = {str(item.get("location", "")).split("区")[0] + "区" for item in mobility_items if "区" in str(item.get("location", ""))}
    if len(mobility_zones) > 1:
        fail(f"plan_itinerary.py mobility-limited route crosses zones: {mobility_zones}")
    if len(constraint_plans["max_density"].get("items", [])) <= len(constraint_plans["mobility_limited"].get("items", [])):
        fail("plan_itinerary.py max-density route should contain more items than mobility-limited route")
    route_signatures = {
        name: tuple(item.get("activity_id") for item in plan.get("items", []))
        for name, plan in constraint_plans.items()
    }
    if route_signatures["mobility_limited"] == route_signatures["max_density"]:
        fail("plan_itinerary.py collapsed mobility-limited and max-density profiles into the same route")
    max_density_text = json.dumps(constraint_plans["max_density"], ensure_ascii=False)
    for forbidden_text in ["晨读", "舞动竹龙", "当AI通过了所有考试，别让教室成为孤岛", "照顾内在小孩"]:
        if forbidden_text in max_density_text:
            fail(f"plan_itinerary.py max-density hardware route included mismatched filler: {forbidden_text}")
    assert_route_quality(
        constraint_plans["max_density"],
        name="max_density",
        topic_keywords=["硬件", "机器人", "芯片", "具身", "制造", "openclaw", "maker", "agent", "社区", "共创"],
        min_topic_items=3,
    )
    if not any(
        item.get("container") in {"探索空间", "热带雨林", "青年团聚"}
        and item_contains_any(item, ["硬件", "机器人", "芯片", "具身", "制造", "openclaw", "maker", "agent", "社区", "共创"])
        for item in constraint_plans["max_density"].get("items", [])
    ):
        fail("plan_itinerary.py max-density route lacks a relevant practice or connection stop")
    max_windows = []
    for item in constraint_plans["max_density"].get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})$", str(item.get("suggested_window", "")))
        if not match:
            fail(f"plan_itinerary.py max-density route has invalid window: {item.get('suggested_window')}")
        max_windows.append((int(match.group(1)) * 60 + int(match.group(2)), int(match.group(3)) * 60 + int(match.group(4))))
    max_windows.sort()
    max_gap = max((start - prev_end for (_, prev_end), (start, _) in zip(max_windows, max_windows[1:])), default=0)
    if max_gap > 90:
        fail(f"plan_itinerary.py max-density route has too much idle time between items: {max_gap} minutes")
    if "晨读" not in json.dumps(constraint_plans["morning_person"], ensure_ascii=False):
        fail("plan_itinerary.py morning-person route should use the morning slot")
    if "舞动竹龙" in json.dumps(constraint_plans["morning_person"], ensure_ascii=False):
        fail("plan_itinerary.py morning-person route should not fill a deep-talk slot with unrelated early performance")
    low_energy_profile = "第一次来2050 教育工作者 科普 科教 喜欢小团体交流 不想太累"
    completed = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", low_energy_profile, "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"plan_itinerary.py low-energy profile failed: {completed.stderr.strip() or completed.stdout.strip()}")
    low_energy_plan = json.loads(completed.stdout)
    for item in low_energy_plan.get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-", str(item.get("suggested_window", "")))
        if match and int(match.group(1)) >= 19:
            fail(f"plan_itinerary.py low-energy route should not schedule evening item without explicit evening preference: {item.get('suggested_window')}")
    if any(item_contains_any(item, ["离谱村音乐会", "壁画动次大次", "三周年庆生"]) for item in low_energy_plan.get("items", [])):
        fail("plan_itinerary.py low-energy route should not use unrelated entertainment as filler")
    low_energy_0424 = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "第一次来2050 设计师 AI创作 影像艺术 想轻松认识人 不想太累", "--date", "2026-04-24", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if low_energy_0424.returncode != 0:
        fail(f"plan_itinerary.py 4/24 low-energy profile should not fail just because the only forum is late: {low_energy_0424.stderr.strip() or low_energy_0424.stdout.strip()}")
    low_energy_0424_plan = json.loads(low_energy_0424.stdout)
    if not low_energy_0424_plan.get("advice") or "晚间" not in json.dumps(low_energy_0424_plan.get("advice"), ensure_ascii=False):
        fail("plan_itinerary.py 4/24 low-energy route should explain that the available forum anchor is late")
    if any(item.get("container") == "新生论坛" for item in low_energy_0424_plan.get("items", [])):
        fail("plan_itinerary.py should not force the 4/24 late forum into a low-energy route")
    half_day = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "高校老师 科普教育 课程设计 青少年 创客 社区运营 半天可参加", "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if half_day.returncode != 0:
        fail(f"plan_itinerary.py half-day profile failed: {half_day.stderr.strip() or half_day.stdout.strip()}")
    half_day_plan = json.loads(half_day.stdout)
    half_day_windows = []
    for item in half_day_plan.get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})$", str(item.get("suggested_window", "")))
        if not match:
            fail(f"plan_itinerary.py half-day route has invalid window: {item.get('suggested_window')}")
        half_day_windows.append((int(match.group(1)) * 60 + int(match.group(2)), int(match.group(3)) * 60 + int(match.group(4))))
    if half_day_windows and max(end for _, end in half_day_windows) - min(start for start, _ in half_day_windows) > 300:
        fail("plan_itinerary.py half-day route spans too much of the day")
    if any(start >= 19 * 60 for start, _ in half_day_windows):
        fail("plan_itinerary.py half-day route should not include evening without explicit evening preference")
    morning_soft_afternoon = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "晨型 早起 科普教育 想上午优先 下午轻松", "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if morning_soft_afternoon.returncode != 0:
        fail(f"plan_itinerary.py morning profile with soft afternoon text failed: {morning_soft_afternoon.stderr.strip() or morning_soft_afternoon.stdout.strip()}")
    morning_soft_plan = json.loads(morning_soft_afternoon.stdout)
    if "afternoon_only" in set(morning_soft_plan.get("intents", [])):
        fail("plan_itinerary.py should not treat casual '下午轻松' as an afternoon-only constraint")
    if "晨读" not in json.dumps(morning_soft_plan, ensure_ascii=False):
        fail("plan_itinerary.py morning profile should still use morning slot when the user also says afternoon can be light")
    startup_indie = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "一人公司 独立开发者 少数派 产品共创 想找同类", "--date", "2026-04-24", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if startup_indie.returncode != 0:
        fail(f"plan_itinerary.py startup indie profile failed: {startup_indie.stderr.strip() or startup_indie.stdout.strip()}")
    startup_text = startup_indie.stdout
    if "罕见病基因 AI 黑客松" in startup_text:
        fail("plan_itinerary.py should not use a medical hackathon as filler for startup/product indie profile")
    for required_text in ["一人一世界", "AI小酒馆"]:
        if required_text not in startup_text:
            fail(f"plan_itinerary.py startup/product route missing expected 4/24 anchor: {required_text}")
    space_evening = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "天文学 太空 地外文明 哲学 晚上露营 深聊", "--date", "2026-04-24", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if space_evening.returncode != 0:
        fail(f"plan_itinerary.py space evening profile failed: {space_evening.stderr.strip() or space_evening.stdout.strip()}")
    space_evening_text = space_evening.stdout
    for forbidden_text in ["罕见病基因 AI 黑客松", "玩.在一起"]:
        if forbidden_text in space_evening_text:
            fail(f"plan_itinerary.py space/evening route included unrelated filler: {forbidden_text}")
    if "星空之夜" not in space_evening_text:
        fail("plan_itinerary.py space/evening route should include the star-camping evening anchor")
    space_day = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", "天文学 太空 地外文明 哲学 晚上露营 深聊", "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if space_day.returncode != 0:
        fail(f"plan_itinerary.py space day profile failed: {space_day.stderr.strip() or space_day.stdout.strip()}")
    if "2050@太空计算专题论坛" not in space_day.stdout:
        fail("plan_itinerary.py pure space/astronomy route should prefer the space-computing forum over generic AI4Science")
    mobility_philosophy_profile = "行动不便 不想跨区 少走路 哲学 人文 深聊"
    completed = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", mobility_philosophy_profile, "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"plan_itinerary.py mobility philosophy profile failed: {completed.stderr.strip() or completed.stdout.strip()}")
    mobility_philosophy_plan = json.loads(completed.stdout)
    for item in mobility_philosophy_plan.get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})$", str(item.get("suggested_window", "")))
        if not match:
            fail(f"plan_itinerary.py mobility route has invalid window: {item.get('suggested_window')}")
        duration = (int(match.group(3)) * 60 + int(match.group(4))) - (int(match.group(1)) * 60 + int(match.group(2)))
        if duration > 150:
            fail(f"plan_itinerary.py mobility route should not create a long standing window: {item.get('suggested_window')}")
    hardware_networking_profile = "第一次来2050 硬件 机器人 开源 动手 想找合作伙伴"
    completed = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", hardware_networking_profile, "--date", "2026-04-25", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        fail(f"plan_itinerary.py hardware networking profile failed: {completed.stderr.strip() or completed.stdout.strip()}")
    hardware_networking_plan = json.loads(completed.stdout)
    for item in hardware_networking_plan.get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-", str(item.get("suggested_window", "")))
        if match and int(match.group(1)) >= 19:
            fail(f"plan_itinerary.py should not add evening filler when hardware networking user did not ask for night events: {item.get('suggested_window')}")
    if not any(item_contains_any(item, ["硬件", "机器人", "芯片", "具身", "openclaw", "maker"]) for item in hardware_networking_plan.get("items", [])):
        fail("plan_itinerary.py hardware networking route lacks a hardware/robotics stop")
    hardware_markdown = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), "--profile", hardware_networking_profile, "--date", "2026-04-25"],
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if hardware_markdown.returncode != 0:
        fail(f"plan_itinerary.py hardware markdown failed: {hardware_markdown.stderr.strip() or hardware_markdown.stdout.strip()}")
    if "AI 全链路 | 原力" in hardware_markdown.stdout:
        fail("plan_itinerary.py markdown table did not escape pipe characters inside activity titles")
    if "AI 全链路 \\| 原力" not in hardware_markdown.stdout:
        fail("plan_itinerary.py markdown route should preserve pipe-like title text with escaping")
    for line in hardware_markdown.stdout.splitlines():
        if line.startswith("| ") and not line.startswith("|---") and not line.startswith("| 建议窗口"):
            if len(re.findall(r"(?<!\\)\|", line)) != 8:
                fail(f"plan_itinerary.py markdown route row has a broken table shape: {line}")
    for item in constraint_plans["early_sleep"].get("items", []):
        match = re.match(r"(\d{2}):(\d{2})-", str(item.get("suggested_window", "")))
        if match and int(match.group(1)) >= 19:
            fail(f"plan_itinerary.py early-sleep route should not schedule evening item: {item.get('suggested_window')}")
    if not any("move_note" in item for item in constraint_plans["max_density"].get("items", [])):
        fail("plan_itinerary.py should include transition notes")

    no_result = output_from_search("海洋生物 潜水")
    for required_text in ["没有找到与", "可以试试这些方向重新检索", "探索空间", "思想约会"]:
        if required_text not in no_result:
            fail(f"search_activities.py no-result feedback missing: {required_text}")

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
