#!/usr/bin/env python3
"""Rebuild human-readable reference slices from packaged activity facts."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip() or "未分类"


def tags_for(activity: dict) -> list[str]:
    values = [activity.get("date", ""), activity.get("container", "")]
    values.extend(activity.get("topic_tags", []))
    values.extend(activity.get("format_tags", []))
    seen = set()
    result = []
    for value in values:
        value = str(value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def section(activity: dict, facets: dict[str, dict]) -> str:
    activity_id = str(activity.get("activity_id", ""))
    facet = facets.get(activity_id, {})
    note = facet.get("route_note") or activity.get("summary", "")
    tag_text = " ".join(f"`{tag}`" for tag in tags_for(activity))
    return "\n".join(
        [
            f"### {activity.get('time', '')} {activity.get('title', '')}",
            f"- 容器: {activity.get('container', '')}",
            f"- 地点: {activity.get('location', '')}",
            f"- 召集人: {activity.get('convener', '')}",
            f"- 标签: {tag_text}",
            f"- 这 part 是干嘛的: {note}",
            f"- 来源: {activity.get('url', '')}",
            "",
        ]
    )


def write_group(path: Path, title: str, rows: list[dict], facets: dict[str, dict], *, show_date_counts: bool = False) -> None:
    rows = sorted(rows, key=lambda item: (item.get("date", ""), item.get("time", ""), item.get("title", "")))
    lines = [f"# {title}", "", f"- 记录数: {len(rows)}", ""]
    if show_date_counts:
        for date, count in sorted(Counter(str(row.get("date", "")) for row in rows).items()):
            lines.append(f"- {date}: {count} 条")
        lines.append("")
    for row in rows:
        lines.append(section(row, facets))
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    activities = load_json(REF / "activity_index.min.json")
    facets = load_json(REF / "activity_facets.json")

    groups: dict[str, dict[str, list[dict]]] = {
        "by_date": defaultdict(list),
        "by_container": defaultdict(list),
        "by_location": defaultdict(list),
        "by_topic": defaultdict(list),
    }
    for activity in activities:
        groups["by_date"][str(activity.get("date", "未定"))].append(activity)
        groups["by_container"][str(activity.get("container", "未分类"))].append(activity)
        groups["by_location"][str(activity.get("location_zone", "地点待细分"))].append(activity)
        topics = activity.get("topic_tags") or ["general"]
        for topic in topics:
            groups["by_topic"][str(topic)].append(activity)

    for folder in groups:
        out = REF / folder
        out.mkdir(exist_ok=True)
        for existing in out.glob("*.md"):
            existing.unlink()

    for date, rows in groups["by_date"].items():
        write_group(REF / "by_date" / f"{slug(date)}.md", f"{date} 2050 日程", rows, facets)
    for container, rows in groups["by_container"].items():
        write_group(REF / "by_container" / f"{slug(container)}.md", container, rows, facets, show_date_counts=True)
    for location, rows in groups["by_location"].items():
        write_group(REF / "by_location" / f"{slug(location)}.md", f"地点：{location}", rows, facets)
    for topic, rows in groups["by_topic"].items():
        write_group(REF / "by_topic" / f"{slug(topic)}.md", f"主题：{topic}", rows, facets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
