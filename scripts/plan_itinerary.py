#!/usr/bin/env python3
"""Build a conflict-aware sample itinerary from ask2050 activity data."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"

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


def score_item(item: dict, facet: dict | None, terms: list[str], role: str) -> int:
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
        score += 30
    if "ai4science" in terms and "ai4science" in title:
        score += 90
    if "科学" in terms and "科学" in title:
        score += 25
    if role == "practice" and ("硬件" in text or "动手" in text):
        score += 35
    if role == "practice" and facet and "动手工作坊" in facet.get("experience_modes", []):
        score += 35
    official = parse_time_range(str(item.get("time", "")))
    if role == "practice" and official and official[1] - official[0] <= 150:
        score += 25
    if role == "practice" and ("教育" in terms or "科普" in terms or "科教" in terms) and ("课程" in text or "学习" in text):
        score += 20
    if role in {"deep_talk", "evening"} and ("太空" in text or "地外文明" in text or "宇宙" in text):
        score += 55
    if role == "evening" and ("太空" in text or "地外文明" in text):
        score += 35
    return score


def location_note(location: str) -> str:
    value = str(location or "").strip()
    if not value:
        return "地点待官方补充"
    if any(hint in value for hint in SPECIFIC_LOCATION_HINTS):
        return value
    return f"{value}（官方地点仅到总场馆，入场前复核厅/展位）"


def choose(
    activities: list[dict],
    facets: dict,
    *,
    date: str,
    terms: list[str],
    role: str,
    containers: set[str],
    exclude_ids: set[str],
) -> dict | None:
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
        score = score_item(item, facet, terms, role)
        if score <= 0:
            continue
        candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].get("time", ""), pair[1].get("title", "")))
    return candidates[0][1] if candidates else None


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


def overlaps(candidate: tuple[int, int], occupied: list[tuple[int, int]]) -> bool:
    start, end = candidate
    return any(start < other_end and other_start < end for other_start, other_end in occupied)


def build_plan(profile: str, date: str) -> dict:
    activities = load_json(REF / "activity_index.min.json")
    facets = load_json(REF / "activity_facets.json")
    terms = profile_terms(profile)
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
        item = choose(
            activities,
            facets,
            date=date,
            terms=terms,
            role=role,
            containers=containers,
            exclude_ids=exclude_ids,
        )
        if not item:
            continue
        window = planned_window(item, role, occupied)
        if overlaps(window, occupied):
            continue
        activity_id = str(item.get("activity_id"))
        facet = facets.get(activity_id, {})
        occupied.append(window)
        exclude_ids.add(activity_id)
        rows.append(
            {
                "label": label,
                "activity_id": activity_id,
                "title": item.get("title", ""),
                "container": item.get("container", ""),
                "date": item.get("date", ""),
                "official_time": item.get("time", ""),
                "suggested_window": f"{fmt(window[0])}-{fmt(window[1])}",
                "location": location_note(str(item.get("location", ""))),
                "reason": reason,
                "why_fit": facet.get("route_note") or item.get("summary", ""),
                "intensity": INTENSITY_LABELS.get(str(facet.get("intensity", "")), str(facet.get("intensity", "")) or "待判断"),
                "source": item.get("url", ""),
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
