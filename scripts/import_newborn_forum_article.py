#!/usr/bin/env python3
"""Import the detailed 2050@2026 newborn forum article into layered references."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
ACTIVITY_INDEX = REF / "activity_index.min.json"
CROSSWALK = REF / "article_activity_crosswalk.json"
ARTICLE_FACETS = REF / "article_facets.json"
ARTICLE_EVIDENCE = REF / "article_evidence_index.json"
FOCUS_SESSIONS = REF / "focus_sessions.min.json"

ARTICLE_URL = "https://mp.weixin.qq.com/s/0pk6F8FvoqjysXBApdrrdA"
SOURCE_ID = "008.md"
ARTICLE_TITLE = "新生论坛@2050@2026：500+脑暴席卷云栖，年青就要最大声分享！"


TOPIC_RULES = [
    ("ai", ["AI", "大模型", "Agent", "智能体", "AIGC", "Token", "生成式"]),
    ("research-science", ["科研", "科学", "AI4Science", "物理", "数学", "天文", "宇宙", "地球", "海洋", "气象", "油气", "量子"]),
    ("education", ["教育", "科普", "学习", "课程", "学校", "青少年", "创客", "教师", "学生"]),
    ("health-medical", ["医疗", "医生", "患者", "生命", "罕见病", "健康", "助老", "养老", "康复"]),
    ("robotics-hardware", ["机器人", "硬件", "芯片", "具身", "制造", "低空", "航天", "旋翼", "3D 打印"]),
    ("arts-media-design", ["艺术", "影像", "电影", "导演", "绘画", "创作", "音乐", "设计", "游戏", "文旅"]),
    ("philosophy-mind", ["哲学", "意识", "心理", "心", "人文", "人类", "人生", "手工艺", "爱情", "身体", "伦理"]),
    ("community-youth", ["青年", "社区", "社群", "OPC", "共创", "合作", "创业", "开放麦"]),
    ("social-impact", ["公益", "无障碍", "可持续", "乡土", "未来城邦", "助盲", "绿色"]),
    ("startup-product", ["产品", "项目", "商业", "创业", "一人公司", "组织", "品牌", "投资"]),
    ("opensource-tech", ["开源", "开发者", "工具", "编程", "黑客松", "数字分身", "OpenRD", "WaytoAGI"]),
]

RECOMMENDED_FOR = {
    "ai": "AI实践者",
    "research-science": "科研/科学传播方向",
    "education": "教育/科普方向",
    "health-medical": "医疗健康或公益技术方向",
    "robotics-hardware": "硬件/机器人/工程方向",
    "arts-media-design": "影像艺术和内容创作者",
    "philosophy-mind": "喜欢人文哲学深聊的人",
    "community-youth": "社区组织者和想找同伴的人",
    "social-impact": "公共议题和可持续实践者",
    "startup-product": "创业者和产品实践者",
    "opensource-tech": "开源技术和工具建设者",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize(value: str) -> str:
    value = str(value).lower().replace("al", "ai")
    return re.sub(r"[\s\-—–：:，,。！!？?·・「」“”\"'()（）【】\[\]@|｜+]+", "", value)


def clean_heading(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).strip()


def hall_location(heading: str) -> str:
    mapping = [
        ("五云厅", "A区 2F 2050学习节(五云厅)"),
        ("学习节", "A区 2F 2050学习节(五云厅)"),
        ("风云厅", "A区 3F 风云厅"),
        ("蔚云厅", "A区 3F 蔚云厅"),
        ("皓云厅", "A区 3F 皓云厅"),
        ("青云厅", "A区 3F 青云厅"),
        ("智云厅", "A区 1F 智云厅"),
        ("慧云厅", "A区 1F 慧云厅"),
        ("彩云厅", "A区 1F 彩云厅"),
        ("贤云厅", "A区 1F 贤云厅"),
        ("云栖厅", "A区 2F 360环屏(千人云栖厅)"),
    ]
    for key, location in mapping:
        if key in heading:
            return location
    return ""


def parse_time(lines: list[str]) -> str:
    pattern = re.compile(r"(\d{1,2})[:：](\d{2})\s*[—–\-~～至]\s*(\d{1,2})[:：](\d{2})")
    for line in lines[:10]:
        match = pattern.search(line)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}-{int(match.group(3)):02d}:{match.group(4)}"
    return ""


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
    return end - start >= 300 or str(value) in {"09:00-15:30", "14:00-23:55", "12:30-23:55"}


def time_relation(activity_time: str, session_time: str) -> str:
    activity = parse_time_range(activity_time)
    session = parse_time_range(session_time)
    if not activity or not session:
        return "unknown"
    if activity[0] <= session[0] and session[1] <= activity[1]:
        return "contained"
    if activity[0] == session[0]:
        return "same_start"
    if not (session[1] <= activity[0] or activity[1] <= session[0]):
        return "overlap"
    if is_broad_time(activity_time):
        return "broad_outside"
    return "outside"


def strip_markup(line: str) -> str:
    value = line.strip()
    value = re.sub(r"^[-*]\s+", "", value)
    value = re.sub(r"^>\s*", "", value)
    value = re.sub(r"^#+\s*", "", value)
    value = value.replace("**", "").replace("*", "").strip()
    return value


def parse_talks(lines: list[str], fallback_title: str) -> list[dict]:
    talks: list[dict] = []
    current: dict | None = None
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if re.search(r"\d{1,2}[:：]\d{2}\s*[—–\-~～至]\s*\d{1,2}[:：]\d{2}", stripped):
            continue
        if stripped.startswith("召集人"):
            continue
        heading = re.match(r"^#####\s+(.+)$", stripped)
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        quote = re.match(r"^>\s+(.+)$", stripped)
        if heading or bullet or quote:
            title = strip_markup((heading or bullet or quote).group(1))
            if title and not title.startswith("场景"):
                current = {"title": title, "speaker": "", "tags": infer_topics(title)}
                talks.append(current)
            continue
        if current and not current.get("speaker"):
            value = strip_markup(stripped)
            if value and not value.startswith("（待更新") and len(value) <= 90:
                current["speaker"] = value
    if not talks:
        talks.append({"title": fallback_title, "speaker": "", "tags": infer_topics(fallback_title)})
    for talk in talks:
        if not talk.get("tags"):
            talk["tags"] = infer_topics(" ".join([fallback_title, talk.get("title", ""), talk.get("speaker", "")]))
    return talks


def infer_topics(*parts: str) -> list[str]:
    text = " ".join(str(part) for part in parts)
    topics = []
    for topic, keywords in TOPIC_RULES:
        if any(keyword.lower() in text.lower() for keyword in keywords):
            topics.append(topic)
    return topics or ["general"]


def recommended_for(topics: list[str], title: str) -> list[str]:
    values = [RECOMMENDED_FOR[topic] for topic in topics if topic in RECOMMENDED_FOR]
    if "第一次来 2050" not in values:
        values.append("第一次来 2050、想快速判断是否值得听的人")
    return values[:5]


def parse_article(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sessions: list[dict] = []
    hall = ""
    location = ""
    date = ""
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("##") and not line.startswith("###"):
            hall = clean_heading(line)
            location = hall_location(hall)
            continue
        if line.startswith("### ") and not line.startswith("####"):
            match = re.search(r"(25|26)日?", line)
            if match:
                date = f"2026-04-{match.group(1)}"
            continue
        match = re.match(r"^####\s+\d+\s+(.+?)\s*$", line)
        if match and not line.startswith("#####"):
            if current:
                sessions.append(current)
            current = {
                "title": match.group(1).strip(),
                "hall": hall,
                "location": location,
                "date": date,
                "body": [],
            }
            continue
        if current:
            current["body"].append(line)
    if current:
        sessions.append(current)

    for session in sessions:
        session["time"] = parse_time(session["body"])
        session["talks"] = parse_talks(session["body"], session["title"])
        session["topic_tags"] = infer_topics(
            session["title"],
            session["location"],
            " ".join(talk.get("title", "") for talk in session["talks"]),
            " ".join(talk.get("speaker", "") for talk in session["talks"]),
        )
        for talk in session["talks"]:
            if talk.get("tags") == ["general"]:
                talk["tags"] = session["topic_tags"][:3]
    return sessions


def similar_location(left: str, right: str) -> bool:
    left_norm = normalize(left)
    right_norm = normalize(right)
    return bool(left_norm and right_norm and (left_norm in right_norm or right_norm in left_norm))


def keyword_bonus(session_text: str, activity_text: str) -> int:
    keywords = [
        "ai",
        "agent",
        "opc",
        "waytoagi",
        "罕见病",
        "教育",
        "科学",
        "科教",
        "科研",
        "青年",
        "社区",
        "硬件",
        "芯片",
        "量子",
        "医疗",
        "太空",
        "宇航",
        "制造",
        "公益",
        "助老",
        "绘画",
        "电影",
        "导演",
        "数学",
        "物理",
        "冷湖",
        "钱学森",
        "低空",
        "农业",
        "海洋",
        "气象",
        "外滩",
        "蚂蚁",
        "数字分身",
        "青智助老",
        "未来城邦",
    ]
    score = sum(8 for keyword in keywords if keyword in session_text and keyword in activity_text)
    return min(score, 40)


def score_activity(session: dict, activity: dict) -> float:
    if session.get("date") and activity.get("date") != session.get("date"):
        return -1
    session_title = normalize(session.get("title", ""))
    activity_title = normalize(activity.get("title", ""))
    activity_text = normalize(
        " ".join(str(activity.get(key, "")) for key in ["title", "summary", "convener", "location"])
    )
    score = difflib.SequenceMatcher(None, session_title, activity_title).ratio() * 55
    title_related = bool(session_title and (session_title in activity_text or activity_title in session_title))
    if session_title and (session_title in activity_text or activity_title in session_title):
        score += 45
    score += keyword_bonus(session_title, activity_text)
    if session.get("location") and similar_location(session["location"], activity.get("location", "")):
        score += 25
    relation = time_relation(activity.get("time", ""), session.get("time", ""))
    if session.get("time") and session.get("time") == activity.get("time"):
        score += 20
    elif session.get("time") and activity.get("time") and session["time"].split("-")[0] == activity["time"].split("-")[0]:
        score += 8
    elif relation == "outside":
        score -= 70
    elif relation == "overlap" and not title_related:
        score -= 20
    if "ai全链路" in session_title and "ai全链路" in activity_text and similar_location(
        session.get("location", ""), activity.get("location", "")
    ):
        score += 80
    if "青智助老" in session_title and "青智助老" in activity_text:
        score += 80
    if "opc" in session_title and "opc" in activity_text and similar_location(
        session.get("location", ""), activity.get("location", "")
    ):
        score += 60
    if "罕见病" in session_title and "罕见病" in activity_text:
        score += 60
    if "青年导演" in session_title and "青年导演" in activity_text:
        score += 60
    if "黑话" in session_title and "黑话" in activity_text:
        score += 60
    if "冷湖宇宙" in session_title and "冷湖宇宙" in activity_text:
        score += 60
    return score


def official_location_for_unit(session: dict, matched_ids: list[str], activity_lookup: dict[str, dict]) -> str:
    if not matched_ids:
        return session.get("location") or "地点待确认"
    activity = activity_lookup.get(str(matched_ids[0]))
    if not activity:
        return session.get("location") or "地点待确认"
    official = activity.get("location", "")
    article_location = session.get("location", "")
    if official and "厅" in official and article_location and not similar_location(article_location, official):
        return official
    return article_location or official or "地点待确认"


def official_time_for_focus(session: dict, activity: dict) -> str:
    relation = time_relation(activity.get("time", ""), session.get("time", ""))
    if relation in {"same_start", "outside", "overlap"} and not is_broad_time(activity.get("time", "")):
        return activity.get("time", "") or session.get("time", "")
    return session.get("time") or activity.get("time", "")


def match_activities(session: dict, activities: list[dict]) -> tuple[list[str], str]:
    scored = sorted(
        ((score_activity(session, activity), activity) for activity in activities),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score = scored[0][0] if scored else -1
    if best_score >= 75:
        ids = [str(activity.get("activity_id")) for score, activity in scored if score >= max(75, best_score - 8)]
        return ids[:2], "high"
    if best_score >= 60:
        return [str(scored[0][1].get("activity_id"))], "medium"
    return [], "article_only"


def unit_from_session(session: dict, matched_ids: list[str], confidence: str, activity_lookup: dict[str, dict]) -> dict:
    return {
        "section_title": session["title"],
        "unit_type": "forum_block",
        "matched_activity_ids": matched_ids,
        "date_tags": [session["date"]] if session.get("date") else [],
        "time_range": session.get("time") or "待更新",
        "location_hint": official_location_for_unit(session, matched_ids, activity_lookup),
        "topic_tags": session["topic_tags"],
        "talks": session["talks"],
        "confidence": confidence,
    }


def focus_from_session(session: dict, activity: dict, sequence: int) -> dict:
    topics = session["topic_tags"]
    return {
        "session_id": f"008-{activity['activity_id']}-{sequence:03d}",
        "parent_activity_id": str(activity["activity_id"]),
        "parent_title": activity["title"],
        "title": session["title"],
        "container": activity["container"],
        "date": session.get("date") or activity["date"],
        "time": official_time_for_focus(session, activity),
        "location": official_location_for_unit(session, [str(activity["activity_id"])], {str(activity["activity_id"]): activity}),
        "summary": f"{activity['container']}分厅节目，围绕{session['title']}展开；适合作为该长时段活动里的具体进入点。",
        "recommended_for": recommended_for(topics, session["title"]),
        "topic_tags": topics,
        "talks": session["talks"],
        "source": ARTICLE_URL,
    }


def update_crosswalk(units: list[dict]) -> None:
    crosswalk = load_json(CROSSWALK, {"schema_version": "0.1", "status": "", "scope_note": "", "records": []})
    records = [record for record in crosswalk.get("records", []) if record.get("article_url") != ARTICLE_URL]
    records.append(
        {
            "article_url": ARTICLE_URL,
            "article_title": ARTICLE_TITLE,
            "source_ocr_file": SOURCE_ID,
            "container": "新生论坛",
            "crosswalk_status": "article_outline_complete_forum_venues_curated",
            "units": units,
        }
    )
    crosswalk["records"] = records
    save_json(CROSSWALK, crosswalk)


def update_article_facets(units: list[dict]) -> None:
    facets = load_json(ARTICLE_FACETS, {})
    linked_ids = sorted({activity_id for unit in units for activity_id in unit.get("matched_activity_ids", [])})
    topics = sorted({topic for unit in units for topic in unit.get("topic_tags", [])})
    search_terms = []
    for unit in units:
        search_terms.append(unit["section_title"])
        search_terms.extend(talk.get("title", "") for talk in unit.get("talks", [])[:3])
    search_terms = [term for term in dict.fromkeys(term for term in search_terms if term)]
    facets[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "article_url": ARTICLE_URL,
        "source_role": "program-guide",
        "linked_activity_ids": linked_ids,
        "communities_or_aliases": [
            ARTICLE_TITLE,
            "新生论坛",
            "云栖厅",
            "五云厅",
            "风云厅",
            "蔚云厅",
            "皓云厅",
            "青云厅",
            "智云厅",
            "慧云厅",
            "彩云厅",
            "贤云厅",
        ],
        "extracted_topics": topics,
        "experience_modes": ["听报告", "深聊", "找同伴"],
        "participation_style": ["listen", "deep-talk"],
        "route_use": "解释新生论坛及分厅节目、报告和适合人群，必要时补充官方活动表未细分的节目线索",
        "confidence": "high",
        "search_terms": search_terms[:160],
    }
    save_json(ARTICLE_FACETS, facets)


def update_article_evidence(units: list[dict]) -> None:
    evidence = load_json(ARTICLE_EVIDENCE, {})
    linked_ids = sorted({activity_id for unit in units for activity_id in unit.get("matched_activity_ids", [])})
    search_terms = [ARTICLE_TITLE, "新生论坛完整分厅日程", "新生论坛报告级节目"]
    for unit in units:
        search_terms.append(unit["section_title"])
        search_terms.append(unit.get("location_hint", ""))
        search_terms.extend(unit.get("topic_tags", []))
        search_terms.extend(talk.get("title", "") for talk in unit.get("talks", [])[:4])
        search_terms.extend(talk.get("speaker", "") for talk in unit.get("talks", [])[:4])
    search_terms.extend(linked_ids)
    search_terms = [term for term in dict.fromkeys(str(term) for term in search_terms if term)]
    for record in evidence.get("records", []):
        if record.get("result_file") != SOURCE_ID:
            continue
        record["matched_activity_ids"] = linked_ids
        record["manual_summary"] = (
            "新生论坛文章，已整理 4 月 25-26 日分厅节目、报告题目、讲者线索、时间和地点；"
            "能回到官网活动表的条目已关联活动 ID，官网未细分的条目保留为文章小节线索。"
        )
        record["search_terms"] = search_terms[:240]
        record["review_tier"] = "manual_program_curated"
        record["manual_reviewed"] = True
        break
    save_json(ARTICLE_EVIDENCE, evidence)


def update_focus_sessions(sessions: list[dict], units: list[dict], activity_lookup: dict[str, dict]) -> int:
    focus_sessions = load_json(FOCUS_SESSIONS, [])
    by_key = {
        (
            str(item.get("parent_activity_id")),
            normalize(item.get("title", "")),
            item.get("date", ""),
            item.get("time", ""),
        ): item
        for item in focus_sessions
    }
    added_or_updated = 0
    sequence_by_activity: dict[str, int] = {}
    generated_session_ids: set[str] = set()
    for session, unit in zip(sessions, units, strict=True):
        ids = unit.get("matched_activity_ids", [])
        if not ids or unit.get("confidence") not in {"high", "medium"}:
            continue
        activity = activity_lookup.get(str(ids[0]))
        if not activity:
            continue
        activity_id = str(activity["activity_id"])
        sequence_by_activity[activity_id] = sequence_by_activity.get(activity_id, 0) + 1
        focus = focus_from_session(session, activity, sequence_by_activity[activity_id])
        generated_session_ids.add(focus["session_id"])
        key = (
            str(focus.get("parent_activity_id")),
            normalize(focus.get("title", "")),
            focus.get("date", ""),
            focus.get("time", ""),
        )
        if key in by_key:
            by_key[key].update(focus)
        else:
            focus_sessions.append(focus)
            by_key[key] = focus
        added_or_updated += 1
    focus_sessions = [
        item
        for item in focus_sessions
        if not (
            str(item.get("session_id", "")).startswith("008-")
            and item.get("source") == ARTICLE_URL
            and item.get("session_id") not in generated_session_ids
        )
    ]

    def focus_rank(item: dict) -> tuple[int, int, str]:
        activity = activity_lookup.get(str(item.get("parent_activity_id")))
        if not activity:
            return (9, 9, str(item.get("time", "")))
        relation = time_relation(activity.get("time", ""), item.get("time", ""))
        if item.get("time") == activity.get("time"):
            return (0, 0, str(item.get("time", "")))
        if relation in {"contained", "overlap", "same_start"}:
            return (1, 0, str(item.get("time", "")))
        return (2, 0, str(item.get("time", "")))

    deduped_by_session_id: dict[str, dict] = {}
    for item in focus_sessions:
        session_id = str(item.get("session_id", ""))
        if not session_id:
            continue
        if session_id not in deduped_by_session_id or focus_rank(item) < focus_rank(deduped_by_session_id[session_id]):
            deduped_by_session_id[session_id] = item
    focus_sessions = list(deduped_by_session_id.values())
    focus_sessions.sort(key=lambda item: (item.get("date", ""), item.get("time", ""), item.get("location", ""), item.get("title", "")))
    save_json(FOCUS_SESSIONS, focus_sessions)
    return added_or_updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article-md", required=True, help="Path to the newborn forum markdown article")
    args = parser.parse_args()

    sessions = parse_article(Path(args.article_md))
    activities = load_json(ACTIVITY_INDEX, [])
    activity_lookup = {str(item.get("activity_id")): item for item in activities}

    units = []
    for session in sessions:
        matched_ids, confidence = match_activities(session, activities)
        units.append(unit_from_session(session, matched_ids, confidence, activity_lookup))

    update_crosswalk(units)
    update_article_facets(units)
    update_article_evidence(units)
    focus_count = update_focus_sessions(sessions, units, activity_lookup)

    matched_units = sum(1 for unit in units if unit.get("matched_activity_ids"))
    print(
        f"imported_sessions={len(sessions)} matched_units={matched_units} "
        f"article_only={len(sessions) - matched_units} focus_added_or_updated={focus_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
