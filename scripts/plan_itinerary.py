#!/usr/bin/env python3
"""Build a conflict-aware sample itinerary from ask2050 activity data."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
FOCUS_SESSIONS = REF / "focus_sessions.min.json"

INTENSITY_LABELS = {"low": "低", "medium": "中", "high": "高"}
LONG_WINDOW_CONTAINERS = {"新生论坛", "探索空间", "思想约会"}
SPECIFIC_LOCATION_HINTS = [
    "厅",
    "楼",
    "层",
    "F",
    "f",
    "展台",
    "基地",
    "草坪",
    "帐篷",
    "玻璃房",
    "云栖之眼",
    "空间",
    "区",
]

PROFILE_ALIASES = {
    "ai4s": ["ai4science", "科学", "科研"],
    "天文学": ["太空", "宇宙", "地外文明", "物理", "科学"],
    "科普": ["教育", "提问", "课程", "学习"],
    "科教": ["教育", "学习", "课程"],
    "开源": ["opensource-tech", "开源", "技术"],
    "社区运营": ["社区", "社群", "找同伴"],
    "哲学": ["哲学", "思想", "深聊"],
    "动手": ["动手工作坊", "看展体验", "硬件"],
    "硬件": ["robotics-hardware", "机器人", "芯片", "具身", "制造", "AI硬件"],
    "机器人": ["robotics-hardware", "硬件", "具身", "制造"],
    "小团体": ["小范围交流", "找同伴", "青年团聚", "热带雨林"],
}

INTENT_KEYWORDS = {
    "research_science": ["ai4s", "ai4science", "科研", "博士", "天文学", "科学研究", "物理"],
    "education": ["教育", "科普", "科教", "课程", "学习", "老师", "学校", "教研"],
    "hardware": ["硬件", "机器人", "芯片", "具身", "制造", "robotics-hardware"],
    "philosophy": ["哲学", "思想", "人文", "深聊", "观点", "社会科学"],
    "community": ["社区", "社群", "运营", "找同伴", "小团体", "合作"],
    "arts": ["艺术", "创作", "音乐", "表演", "影像", "设计"],
    "low_energy": ["低能量", "轻松", "放松", "不想太累", "随便逛"],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def fmt(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def parse_time_range(value: str) -> tuple[int, int] | None:
    match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", str(value))
    if not match:
        return None
    start = minutes(match.group(1))
    end = minutes(match.group(2))
    if end <= start:
        end += 24 * 60
    return start, end


def profile_terms(profile: str) -> list[str]:
    text = profile.lower()
    terms = [part for part in re.split(r"[\s,，;；:：+]+", text) if part]
    for key, aliases in PROFILE_ALIASES.items():
        if key.lower() in text:
            terms.extend(alias.lower() for alias in aliases)
    return list(dict.fromkeys(terms))


def profile_intents(profile: str, terms: list[str]) -> set[str]:
    text = f"{profile.lower()} {' '.join(terms)}"
    intents = set()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            intents.add(intent)
    return intents


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def haystack(item: dict, facet: dict | None) -> str:
    parts = [
        item.get("title", ""),
        item.get("container", ""),
        item.get("summary", ""),
        item.get("location", ""),
    ]
    if facet:
        for key in [
            "primary_topics",
            "secondary_topics",
            "experience_modes",
            "participation_style",
            "recommended_for",
            "search_terms",
        ]:
            value = facet.get(key)
            if isinstance(value, list):
                parts.extend(str(v) for v in value)
        for key in ["planning_role", "route_note", "intensity", "social_density"]:
            if facet.get(key):
                parts.append(str(facet[key]))
    return " ".join(str(part).lower() for part in parts)


def score_item(item: dict, facet: dict | None, terms: list[str], role: str, intents: set[str] | None = None) -> int:
    intents = intents or set()
    text = haystack(item, facet)
    title = str(item.get("title", "")).lower()
    container = str(item.get("container", ""))
    score = 0
    for term in terms:
        if term in title:
            score += 18
        if term in text:
            score += 7
    if role == "forum" and container == "新生论坛":
        score += 35
    if role == "practice" and container in {"探索空间", "热带雨林"}:
        score += 25
    if role == "deep_talk" and container in {"思想约会", "星空露营"}:
        score += 25
    if role == "social" and container in {"青年团聚", "热带雨林", "探索空间"}:
        score += 18
    if role == "evening" and container in {"星空露营", "青春舞台"}:
        score += 30
    if role == "practice" and facet and "动手工作坊" in facet.get("experience_modes", []):
        score += 14
    if role == "forum" and "ai4science" in text:
        score += 130 if "research_science" in intents or "ai4science" in terms else -25
    if role == "forum" and "hardware" in intents and contains_any(text, ["硬件", "机器人", "芯片", "具身", "制造", "robotics-hardware"]):
        score += 70
        if contains_any(title, ["硬件", "机器人", "芯片", "具身", "制造"]):
            score += 35
    if role == "forum" and "education" in intents and contains_any(text, ["教育", "科普", "科教", "课程", "学习", "学校", "教研"]):
        score += 60
        if contains_any(title, ["教育", "科普", "课程", "学习"]):
            score += 35
    if role == "forum" and "philosophy" in intents and contains_any(text, ["哲学", "思想", "人文", "社会科学", "观点"]):
        score += 55
        if contains_any(title, ["哲学", "思想", "人文", "社会"]):
            score += 35
    if role == "forum" and "community" in intents and contains_any(text, ["社区", "社群", "青年", "共创", "合作", "找同伴"]):
        score += 45
        if contains_any(title, ["社区", "社群", "青年", "共创"]):
            score += 30
    if role == "forum" and any(term in terms for term in ["太空", "宇宙", "地外文明", "物理"]) and (
        "太空" in text or "宇宙" in text or "地外文明" in text or "物理" in text
    ):
        score += 35
    if "ai4science" in terms and "ai4science" in title:
        score += 90
    if "科学" in terms and "科学" in title:
        score += 25
    if role == "practice" and ("硬件" in text or "动手" in text):
        score += 35
    if role == "practice" and facet and "动手工作坊" in facet.get("experience_modes", []):
        score += 35
    if role == "practice" and "education" in intents and contains_any(text, ["课程", "学习", "教育", "科普", "提问"]):
        score += 45
        if contains_any(title, ["课程", "学习", "提问", "教育", "黑客松"]):
            score += 70
    if role == "practice" and "philosophy" in intents and contains_any(text, ["哲学", "思想", "人文", "手工艺", "公共空间", "内在", "社会"]):
        score += 45
        if contains_any(title, ["手工艺", "公共空间", "内在", "哲学"]):
            score += 55
    if role == "practice" and "community" in intents and contains_any(text, ["社区", "共创", "伙伴", "找同伴"]):
        score += 35
    if role == "practice" and "arts" not in intents and contains_any(title, ["音乐", "舞蹈", "混音", "声音橡皮泥"]):
        score -= 85
    if role == "deep_talk" and "philosophy" in intents and contains_any(text, ["哲学", "思想", "人文", "社会", "观点"]):
        score += 70
    if role == "deep_talk" and "community" in intents and contains_any(text, ["社区", "社群", "共创", "合作"]):
        score += 45
    if role == "deep_talk" and "education" in intents and contains_any(text, ["教育", "学习", "课程"]):
        score += 45
    if role == "evening" and "community" in intents and contains_any(text, ["waytoagi", "社区", "庆生", "音乐会"]):
        score += 70
    if role == "evening" and "arts" in intents and contains_any(text, ["音乐", "表演", "舞台", "影像", "声音"]):
        score += 70
    if role == "evening" and "education" in intents and contains_any(text, ["少年", "梦想", "教育", "学习"]):
        score += 35
    official = parse_time_range(str(item.get("time", "")))
    if role == "evening" and official:
        if 19 * 60 <= official[0] <= 21 * 60:
            score += 35
        if official[0] >= 23 * 60 and "arts" not in intents and "夜间" not in terms and "深夜" not in terms:
            score -= 250
    if role == "practice" and official and official[1] - official[0] <= 150:
        score += 25
    if role == "practice" and ("教育" in terms or "科普" in terms or "科教" in terms) and ("课程" in text or "学习" in text):
        score += 20
    space_profile = "research_science" in intents and any(term in terms for term in ["太空", "宇宙", "地外文明", "天文学"])
    if role in {"deep_talk", "evening"} and space_profile and ("太空" in text or "地外文明" in text or "宇宙" in text):
        score += 55
    if role == "evening" and space_profile and ("太空" in text or "地外文明" in text):
        score += 35
    if not any(hint in str(item.get("location", "")) for hint in SPECIFIC_LOCATION_HINTS):
        score -= 40
    return score


def session_haystack(session: dict) -> str:
    parts = [
        session.get("title", ""),
        session.get("parent_title", ""),
        session.get("container", ""),
        session.get("summary", ""),
        session.get("location", ""),
    ]
    for key in ["recommended_for", "topic_tags"]:
        value = session.get(key)
        if isinstance(value, list):
            parts.extend(str(v) for v in value)
    for talk in session.get("talks", []):
        if isinstance(talk, dict):
            parts.extend(str(talk.get(key, "")) for key in ["title", "speaker"])
            parts.extend(str(tag) for tag in talk.get("tags", []))
    return " ".join(str(part).lower() for part in parts)


def score_session(session: dict, terms: list[str], role: str, intents: set[str] | None = None) -> int:
    intents = intents or set()
    text = session_haystack(session)
    title = str(session.get("title", "")).lower()
    score = 0
    for term in terms:
        if term in title:
            score += 20
        if term in text:
            score += 8
    if role == "forum":
        score += 35
    if "ai4science" in text:
        score += 120 if "research_science" in intents or "ai4science" in terms else -20
    if "ai4science" in terms and "ai4science" in text:
        score += 80
    if "科学" in terms and ("science" in text or "科学" in text):
        score += 25
    if role == "forum" and "hardware" in intents and contains_any(text, ["硬件", "机器人", "芯片", "具身", "制造", "chip"]):
        score += 80
        if contains_any(title, ["硬件", "机器人", "芯片", "具身", "制造"]):
            score += 30
    if role == "forum" and "education" in intents and contains_any(text, ["教育", "科普", "课程", "学习", "学校", "教研"]):
        score += 70
        if contains_any(title, ["教育", "学习", "课程"]):
            score += 30
    if role == "forum" and "philosophy" in intents and contains_any(text, ["哲学", "思想", "人文", "社会科学", "观点"]):
        score += 65
    if role == "forum" and "community" in intents and contains_any(text, ["社区", "社群", "青年", "共创", "合作"]):
        score += 45
    return score


def focus_session_for(item: dict, terms: list[str], role: str, intents: set[str] | None = None) -> dict | None:
    if not FOCUS_SESSIONS.exists():
        return None
    parent_id = str(item.get("activity_id"))
    candidates = []
    for session in load_json(FOCUS_SESSIONS):
        if str(session.get("parent_activity_id")) != parent_id:
            continue
        if session.get("date") != item.get("date"):
            continue
        if not parse_time_range(str(session.get("time", ""))):
            continue
        score = score_session(session, terms, role, intents)
        if score > 0:
            candidates.append((score, session))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].get("time", ""), pair[1].get("title", "")))
    return candidates[0][1] if candidates else None


def location_note(location: str) -> str:
    value = str(location or "").strip()
    if not value:
        return "地点待官方补充"
    if any(hint in value for hint in SPECIFIC_LOCATION_HINTS):
        return value
    return f"{value}（官方地点仅到总场馆，入场前复核厅/展位）"


def ranked_choices(
    activities: list[dict],
    facets: dict,
    *,
    date: str,
    terms: list[str],
    role: str,
    containers: set[str],
    exclude_ids: set[str],
    intents: set[str] | None = None,
) -> list[dict]:
    intents = intents or set()
    candidates = []
    for item in activities:
        activity_id = str(item.get("activity_id"))
        if activity_id in exclude_ids or item.get("date") != date:
            continue
        if item.get("container") not in containers:
            continue
        if not parse_time_range(str(item.get("time", ""))):
            continue
        facet = facets.get(activity_id)
        score = score_item(item, facet, terms, role, intents)
        if score <= 0:
            continue
        candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].get("time", ""), pair[1].get("title", "")))
    return [item for _, item in candidates]


def choose(
    activities: list[dict],
    facets: dict,
    *,
    date: str,
    terms: list[str],
    role: str,
    containers: set[str],
    exclude_ids: set[str],
    intents: set[str] | None = None,
) -> dict | None:
    candidates = ranked_choices(
        activities,
        facets,
        date=date,
        terms=terms,
        role=role,
        containers=containers,
        exclude_ids=exclude_ids,
        intents=intents,
    )
    return candidates[0] if candidates else None


def planned_window(item: dict, role: str, occupied: list[tuple[int, int]]) -> tuple[int, int]:
    official = parse_time_range(str(item.get("time", "")))
    if not official:
        raise ValueError(f"activity without parseable time: {item.get('activity_id')}")
    start, end = official
    duration = end - start
    if item.get("container") in LONG_WINDOW_CONTAINERS and duration > 90:
        role_windows = {
            "forum": [(start, min(start + 120, end)), (start + 60, min(start + 180, end))],
            "practice": [(max(start, 13 * 60), min(max(start, 13 * 60) + 45, end)), (max(start, 14 * 60), min(max(start, 14 * 60) + 45, end))],
            "deep_talk": [(max(start, 14 * 60), min(max(start, 14 * 60) + 60, end))],
            "social": [(max(start, 15 * 60), min(max(start, 15 * 60) + 60, end))],
        }
        for candidate in role_windows.get(role, [(start, min(start + 60, end))]):
            if candidate[1] > candidate[0] and not overlaps(candidate, occupied):
                return candidate
        cursor = start
        while cursor + 45 <= end:
            candidate = (cursor, cursor + 45)
            if not overlaps(candidate, occupied):
                return candidate
            cursor += 30
    return official


def effective_item(item: dict, terms: list[str], role: str, intents: set[str] | None = None) -> tuple[dict, dict | None]:
    session = focus_session_for(item, terms, role, intents)
    if not session:
        return item, None
    merged = dict(item)
    merged["title"] = f"{session.get('title')}（{item.get('title')}内）"
    merged["time"] = session.get("time", item.get("time", ""))
    merged["location"] = session.get("location", item.get("location", ""))
    merged["summary"] = session.get("summary", item.get("summary", ""))
    merged["source"] = session.get("source", item.get("url", ""))
    return merged, session


def overlaps(candidate: tuple[int, int], occupied: list[tuple[int, int]]) -> bool:
    start, end = candidate
    return any(start < other_end and other_start < end for other_start, other_end in occupied)


def build_plan(profile: str, date: str) -> dict:
    activities = load_json(REF / "activity_index.min.json")
    facets = load_json(REF / "activity_facets.json")
    terms = profile_terms(profile)
    intents = profile_intents(profile, terms)
    exclude_ids: set[str] = set()
    occupied: list[tuple[int, int]] = []
    rows = []

    slots = [
        ("认知主线", "forum", {"新生论坛"}, "先建立当天主题骨架；不要再并排安排另一个上午长时段活动。"),
        ("实践体验", "practice", {"探索空间", "热带雨林"}, "把论坛里的概念落到项目、硬件或课程原型上。"),
        ("深聊/社群", "deep_talk", {"思想约会", "青年团聚", "热带雨林"}, "选择一个讨论或社群入口，不和实践体验并行。"),
        ("晚间收尾", "evening", {"星空露营", "青春舞台"}, "用低压力场景收束当天，也适合继续聊。"),
    ]
    for label, role, containers, reason in slots:
        selected = None
        for item in ranked_choices(
            activities,
            facets,
            date=date,
            terms=terms,
            role=role,
            containers=containers,
            exclude_ids=exclude_ids,
            intents=intents,
        ):
            route_item, session = effective_item(item, terms, role, intents)
            window = planned_window(route_item, role, occupied)
            if overlaps(window, occupied):
                continue
            selected = (item, route_item, session, window)
            break
        if not selected:
            continue
        item, route_item, session, window = selected
        activity_id = str(item.get("activity_id"))
        facet = facets.get(activity_id, {})
        occupied.append(window)
        exclude_ids.add(activity_id)
        rows.append(
            {
                "label": label,
                "activity_id": activity_id,
                "session_id": session.get("session_id") if session else "",
                "title": route_item.get("title", ""),
                "container": route_item.get("container", ""),
                "date": route_item.get("date", ""),
                "official_time": route_item.get("time", ""),
                "suggested_window": f"{fmt(window[0])}-{fmt(window[1])}",
                "location": location_note(str(route_item.get("location", ""))),
                "reason": reason,
                "why_fit": route_item.get("summary") or facet.get("route_note") or item.get("summary", ""),
                "intensity": INTENSITY_LABELS.get(str(facet.get("intensity", "")), str(facet.get("intensity", "")) or "待判断"),
                "source": route_item.get("source") or item.get("url", ""),
            }
        )
    rows.sort(key=lambda row: minutes(row["suggested_window"].split("-")[0]))
    return {"date": date, "profile": profile, "items": rows}


def validate_plan(plan: dict) -> list[str]:
    errors = []
    windows = []
    for item in plan["items"]:
        parsed = parse_time_range(item["suggested_window"])
        if not parsed:
            errors.append(f"无法解析建议窗口: {item['title']}")
            continue
        if overlaps(parsed, windows):
            errors.append(f"建议窗口重叠: {item['title']}")
        windows.append(parsed)
        if item["location"] in {"云栖小镇国际会展中心", "云栖小镇"}:
            errors.append(f"地点不够具体且没有说明需复核: {item['title']}")
    if not any(item["container"] == "新生论坛" for item in plan["items"]):
        errors.append("缺少新生论坛认知主线")
    return errors


def print_markdown(plan: dict) -> None:
    print(f"推荐路线（{plan['date']}）")
    print()
    print("说明：下面是可执行的停留顺序。官方长时段活动只安排一个进入窗口，不代表需要全程占用；同一时间只保留一个去处。")
    print()
    print("| 建议窗口 | 官方时段 | 板块 | 活动 | 地点 | 为什么适合 |")
    print("|---|---|---|---|---|---|")
    for item in plan["items"]:
        print(
            "| {suggested_window} | {official_time} | {container} | {title} | {location} | {why_fit} |".format(
                **item
            )
        )
    print()
    print("备选规则：如果现场确认某个 09:00-15:30 长时段活动必须全程参加，就不要再把同一时段的思想约会或探索空间排进主线，只能改成备选。")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成带时间冲突校验的 ask2050 示例日程")
    parser.add_argument("--profile", required=True, help="用户画像和偏好")
    parser.add_argument("--date", default="2026-04-25", help="日期，例如 2026-04-25")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    plan = build_plan(args.profile, args.date)
    errors = validate_plan(plan)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_markdown(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
