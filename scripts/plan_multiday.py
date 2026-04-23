#!/usr/bin/env python3
"""Plan a compact multi-day ask2050 route by composing daily plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plan_itinerary  # noqa: E402


DEFAULT_DATES = ["2026-04-24", "2026-04-25", "2026-04-26"]


def theme_for_day(plan: dict) -> str:
    titles = " ".join(str(item.get("title", "")) for item in plan.get("items", []))
    containers = [str(item.get("container", "")) for item in plan.get("items", [])]
    if any(term in titles for term in ["AI4Science", "AGI4Science", "科研", "科学"]):
        return "科研与 AI 主线"
    if any(term in titles for term in ["创业", "一人", "产品", "项目", "CEO"]):
        return "产品、创业与个人项目"
    if any(term in titles for term in ["教育", "学习", "课程", "科普"]):
        return "教育、科普与学习社区"
    if any(term in titles for term in ["硬件", "机器人", "具身", "芯片"]):
        return "硬件、机器人与动手体验"
    if "青年团聚" in containers or "热带雨林" in containers:
        return "找人、社群与现场连接"
    if plan.get("items"):
        return "精选主线与低压力探索"
    return "不强排行程"


def energy_note(plan: dict) -> str:
    count = len(plan.get("items", []))
    if count == 0:
        return "这天不强排，保留休息或现场临时选择。"
    if count <= 2:
        return "轻到中等强度，适合保留现场弹性。"
    if count <= 4:
        return "中等强度，需要按换场提示取舍。"
    return "高强度，只适合明确想多参加的人；任何一站太赶就降为备选。"


def compact_item(item: dict) -> dict:
    return {
        "window": item.get("suggested_window", ""),
        "official_time": item.get("official_time", ""),
        "container": item.get("container", ""),
        "title": item.get("title", ""),
        "location": item.get("location", ""),
        "role": item.get("route_role") or item.get("label", ""),
        "matched_profile": item.get("matched_profile", []),
        "why": item.get("why_fit", ""),
        "fallback": item.get("fallback_note", ""),
        "source": item.get("source", ""),
    }


def build_multiday(profile: str, dates: list[str]) -> dict:
    daily = []
    used_titles: set[str] = set()
    for date in dates:
        plan = plan_itinerary.build_plan(profile, date)
        items = []
        repeated = []
        for item in plan.get("items", []):
            title_key = str(item.get("title", "")).split("（", 1)[0]
            compact = compact_item(item)
            if title_key in used_titles:
                repeated.append(compact)
                continue
            used_titles.add(title_key)
            items.append(compact)
        daily.append(
            {
                "date": date,
                "theme": theme_for_day({"items": items}),
                "energy_note": energy_note({"items": items}),
                "main_route": items,
                "repeated_or_backup": repeated,
                "advice": plan.get("advice", []),
            }
        )
    return {
        "profile": profile,
        "dates": dates,
        "daily": daily,
        "cross_day_notes": [
            "每天只保留一个清楚主题，不把同类论坛三天重复塞满。",
            "长窗口活动按进入窗口安排；现场发现必须全程参加时，后续同窗活动降为备选。",
            "多日路线默认保留体力余量，晚上活动只有用户明确想继续时才进入主线。",
        ],
    }


def print_markdown(plan: dict) -> None:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()

    print("2050 多日路线")
    print()
    for day in plan["daily"]:
        print(f"## {day['date']}｜{day['theme']}")
        print()
        print(day["energy_note"])
        print()
        if not day["main_route"]:
            for advice in day.get("advice") or ["这天没有生成强相关主线，建议作为休息或现场机动日。"]:
                print(f"- {advice}")
            print()
            continue
        print("| 窗口 | 板块 | 活动 | 地点 | 角色 | 太赶时 |")
        print("|---|---|---|---|---|---|")
        for item in day["main_route"]:
            print(
                "| "
                + " | ".join(
                    cell(item.get(key, ""))
                    for key in ["window", "container", "title", "location", "role", "fallback"]
                )
                + " |"
            )
        if day.get("advice"):
            print()
            for advice in day["advice"]:
                print(f"- {advice}")
        print()
    print("跨日取舍：")
    for note in plan["cross_day_notes"]:
        print(f"- {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成按天分层的 ask2050 多日路线")
    parser.add_argument("--profile", required=True, help="用户画像和偏好")
    parser.add_argument("--dates", default=",".join(DEFAULT_DATES), help="逗号分隔日期")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    dates = [date.strip() for date in args.dates.split(",") if date.strip()]
    plan = build_multiday(args.profile, dates)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_markdown(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
