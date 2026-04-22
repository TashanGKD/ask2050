#!/usr/bin/env python3
"""Search ask2050 activity index by date/topic/container/free text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references" / "activity_index.min.json"
ARTICLE_ALIASES = ROOT / "references" / "manual" / "article_aliases.json"
CROSSWALK = ROOT / "references" / "article_activity_crosswalk.json"
ARTICLE_EVIDENCE = ROOT / "references" / "article_evidence_index.json"
ACTIVITY_FACETS = ROOT / "references" / "activity_facets.json"
ARTICLE_FACETS = ROOT / "references" / "article_facets.json"
KNOWN_CONTAINERS = [
    "新生论坛",
    "探索空间",
    "思想约会",
    "热带雨林",
    "青年团聚",
    "青春舞台",
    "星空露营",
    "热力运动",
]
INTENSITY_LABELS = {
    "low": "低强度",
    "medium": "中等强度",
    "high": "高强度",
}
SOCIAL_LABELS = {
    "solo-friendly": "独自友好",
    "small-group": "小范围交流",
    "crowd": "大场听看",
    "deep-talk": "深聊表达",
}
SOURCE_ROLE_LABELS = {
    "schedule-update": "日程更新",
    "program-guide": "活动说明",
    "community-call": "社群召集",
    "logistics-guide": "后勤攻略",
    "map-guide": "地图动线",
    "background": "背景说明",
    "mixed": "补充线索",
}


def display_source_title(title: str | None) -> str:
    value = str(title or "").strip()
    replacements = {
        "@2025@2026": "@2026",
        "2025@2026": "2026",
        "@2025": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.strip("｜| -")
QUERY_ALIASES = {
    "第一次来": ["第一次来2050的人", "低门槛", "新生论坛", "听报告", "热带雨林", "探索空间"],
    "第一次去": ["第一次来2050的人", "低门槛", "新生论坛", "听报告", "热带雨林", "探索空间"],
    "安排一天": ["新生论坛", "听报告", "系统学习者", "热带雨林", "探索空间", "找同伴"],
    "一天路线": ["新生论坛", "听报告", "系统学习者", "热带雨林", "探索空间", "找同伴"],
    "一天行程": ["新生论坛", "听报告", "系统学习者", "热带雨林", "探索空间", "找同伴"],
    "帮我安排": ["新生论坛", "听报告", "系统学习者", "热带雨林", "探索空间", "找同伴"],
    "找人合作": ["找同伴", "想找合作伙伴的人", "青年团聚", "热带雨林", "探索空间"],
    "找合作": ["找同伴", "想找合作伙伴的人", "青年团聚", "热带雨林", "探索空间"],
    "合作伙伴": ["找同伴", "想找合作伙伴的人", "青年团聚", "热带雨林", "探索空间"],
    "ai硬件": ["AI硬件", "硬件/机器人方向", "robotics-hardware", "探索空间", "动手工作坊"],
    "做ai硬件": ["AI硬件", "硬件/机器人方向", "robotics-hardware", "探索空间", "动手工作坊"],
    "不懂ai": ["非技术用户", "不懂AI也能参加的人", "低门槛"],
    "非技术": ["非技术用户", "不懂AI也能参加的人", "低门槛"],
    "不是开发": ["非技术用户", "不懂AI也能参加的人", "低门槛"],
    "轻松认识人": ["低社交压力", "找同伴", "小范围交流"],
    "认识人": ["找同伴", "社交入口"],
    "随便逛": ["看展体验", "低门槛"],
    "别太累": ["低强度", "放松"],
    "不想太累": ["低强度", "放松"],
    "晚上": ["夜间继续聊", "晚间活动"],
}
STOP_TERMS = {"我", "想", "要", "可以", "适合", "参加", "2050", "活动", "推荐", "一下", "看看"}


def is_itinerary_query(query: str) -> bool:
    q_lower = query.lower()
    return any(
        phrase in q_lower
        for phrase in ["安排一天", "一天路线", "一天行程", "帮我安排", "行程", "路线"]
    )


def wants_evening_buffer(query: str) -> bool:
    q_lower = query.lower()
    return any(phrase in q_lower for phrase in ["晚上", "夜间", "露营", "音乐", "放松", "收尾"])


def query_terms(query: str) -> list[str]:
    q_lower = query.lower().strip()
    raw_terms = [term for term in q_lower.replace("，", " ").replace(",", " ").split() if term]
    terms = [term for term in raw_terms if term not in STOP_TERMS]
    for phrase, aliases in QUERY_ALIASES.items():
        if phrase in q_lower:
            terms.extend(alias.lower() for alias in aliases)
    return list(dict.fromkeys(terms))


def matched_term_count(haystack: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term and term in haystack)


def query_matches(haystack: str, query: str, *, manual_match: bool = False) -> bool:
    if manual_match:
        return True
    q_lower = query.lower().strip()
    if not q_lower:
        return True
    if q_lower in haystack:
        return True
    terms = query_terms(query)
    if any(term in haystack and (any(char.isdigit() for char in term) or len(term) >= 6) for term in terms):
        return True
    if len(terms) > 1 and all(term in haystack for term in terms):
        return True
    if len(terms) >= 3 and matched_term_count(haystack, terms) >= 2:
        return True

    query_containers = [name for name in KNOWN_CONTAINERS if name.lower() in q_lower]
    if not query_containers:
        return False

    container_match = any(name.lower() in haystack for name in query_containers)
    if not container_match:
        return False

    remainder = q_lower
    for name in query_containers:
        remainder = remainder.replace(name.lower(), " ")
    terms = [term for term in remainder.split() if term]
    return all(term in haystack for term in terms)


def query_score(haystack: str, query: str, *, manual_match: bool = False) -> int:
    if manual_match:
        return 100
    q_lower = query.lower().strip()
    if not q_lower:
        return 1
    score = 0
    if q_lower in haystack:
        score += 20
    terms = query_terms(query)
    score += matched_term_count(haystack, terms) * 5
    for name in KNOWN_CONTAINERS:
        if name.lower() in q_lower and name.lower() in haystack:
            score += 8
    return score


def field_boost(item: dict, query: str) -> int:
    terms = query_terms(query)
    title = str(item.get("title", "")).lower()
    summary = str(item.get("summary", "")).lower()
    container = str(item.get("container", "")).lower()
    score = 0
    for term in terms:
        if term in title:
            score += 12
        if term in summary:
            score += 4
        if term in container:
            score += 6
    if is_itinerary_query(query):
        if "新生论坛" in container:
            score += 50
        elif "探索空间" in container:
            score += 24
        elif "热带雨林" in container or "青年团聚" in container:
            score += 18
    return score


def source_field_boost(record: dict, query: str) -> int:
    terms = query_terms(query)
    title = str(record.get("title", "")).lower()
    summary = str(record.get("manual_summary", "")).lower()
    score = 0
    for term in terms:
        if term in title:
            score += 12
        if term in summary:
            score += 4
    return score


def item_tags(item: dict) -> list[str]:
    tags = item.get("recommendation_tags")
    if tags:
        return [str(tag) for tag in tags]
    derived = []
    for value in [item.get("date"), item.get("container")]:
        if value:
            derived.append(str(value))
    derived.extend(str(tag) for tag in item.get("topic_tags", []))
    derived.extend(str(tag) for tag in item.get("format_tags", []))
    return sorted(set(derived))


def facet_terms(facet: dict | None) -> list[str]:
    if not facet:
        return []
    terms = []
    for key in [
        "primary_topics",
        "secondary_topics",
        "extracted_topics",
        "experience_modes",
        "participation_style",
        "recommended_for",
        "communities_or_aliases",
        "search_terms",
    ]:
        value = facet.get(key)
        if isinstance(value, list):
            terms.extend(str(item) for item in value)
    for key in [
        "intensity",
        "social_density",
        "planning_role",
        "time_pattern",
        "venue_context",
        "route_note",
        "source_level",
        "source_role",
        "route_use",
        "confidence",
    ]:
        if facet.get(key):
            terms.append(str(facet[key]))
    return terms


def source_activity_ids(record: dict, query: str) -> list[str]:
    q_lower = query.lower()
    weak_year_queries = {"2024", "2025", "2026"}
    if q_lower.strip() in weak_year_queries:
        return []
    for rule in record.get("query_activity_rules", []):
        keywords = [str(keyword).lower() for keyword in rule.get("keywords", [])]
        if any(keyword in q_lower for keyword in keywords):
            return [str(activity_id) for activity_id in rule.get("activity_ids", [])]
    return [str(activity_id) for activity_id in record.get("matched_activity_ids", [])]


def filter_activity_ids(
    activity_ids: list[str],
    activity_lookup: dict[str, dict],
    *,
    date: str | None = None,
    container: str | None = None,
) -> list[str]:
    filtered = []
    for activity_id in activity_ids:
        activity = activity_lookup.get(activity_id)
        if not activity:
            continue
        if date and date != activity.get("date"):
            continue
        if container and container not in activity.get("container", ""):
            continue
        filtered.append(activity_id)
    return filtered


def itinerary_reordered(results: list[tuple[int, dict]], query: str = "") -> list[tuple[int, dict]]:
    ordered = []
    seen = set()

    def take_first(predicate) -> None:
        for score, item in results:
            activity_id = str(item.get("activity_id", ""))
            if activity_id in seen:
                continue
            if predicate(str(item.get("container", ""))):
                seen.add(activity_id)
                ordered.append((score, item))
                return

    take_first(lambda container: "新生论坛" in container)
    if wants_evening_buffer(query):
        take_first(lambda container: "星空露营" in container or "青春舞台" in container)
    take_first(lambda container: "热带雨林" in container or "青年团聚" in container)
    take_first(lambda container: "探索空间" in container)
    take_first(lambda container: "思想约会" in container)

    for score, item in results:
        activity_id = str(item.get("activity_id", ""))
        if activity_id in seen:
            continue
        seen.add(activity_id)
        ordered.append((score, item))
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--topic", action="append", default=[])
    parser.add_argument("--container")
    parser.add_argument("--q", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    data = json.loads(INDEX.read_text(encoding="utf-8"))
    activity_facets = {}
    if ACTIVITY_FACETS.exists():
        activity_facets = json.loads(ACTIVITY_FACETS.read_text(encoding="utf-8"))
    article_facets = {}
    if ARTICLE_FACETS.exists():
        article_facets = json.loads(ARTICLE_FACETS.read_text(encoding="utf-8"))
    manual_ids = []
    if args.q and ARTICLE_ALIASES.exists():
        aliases = json.loads(ARTICLE_ALIASES.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        for alias, ids in aliases.items():
            if q_lower in alias.lower() or alias.lower() in q_lower:
                manual_ids.extend(str(activity_id) for activity_id in ids)

    results = []
    seen = set()
    for item in data:
        activity_id = str(item.get("activity_id", ""))
        haystack = " ".join([
            activity_id,
            item.get("title", ""),
            item.get("summary", ""),
            item.get("container", ""),
            item.get("location", ""),
            " ".join(item_tags(item)),
            " ".join(facet_terms(activity_facets.get(activity_id))),
        ]).lower()
        if args.date and args.date != item.get("date"):
            continue
        if args.container and args.container not in item.get("container", ""):
            continue
        tags = item_tags(item)
        if args.topic and not all(topic in tags for topic in args.topic):
            continue
        manual_match = activity_id in manual_ids
        score = query_score(haystack, args.q, manual_match=manual_match) + field_boost(item, args.q)
        if args.q and not query_matches(haystack, args.q, manual_match=manual_match):
            continue
        if activity_id in seen:
            continue
        seen.add(activity_id)
        results.append((score, item))

    activity_lookup = {str(item.get("activity_id")): item for item in data}

    results.sort(key=lambda pair: (-pair[0], pair[1].get("date", ""), pair[1].get("time", "")))
    if is_itinerary_query(args.q):
        results = itinerary_reordered(results, args.q)

    printed = 0
    for _, item in results[: args.limit]:
        print(f"{item['date']} {item['time']} | {item['container']} | {item['title']} | {item['location']}")
        print(f"  标签: {', '.join(item_tags(item))}")
        facet = activity_facets.get(str(item.get("activity_id")))
        if facet:
            intensity = INTENSITY_LABELS.get(facet.get("intensity"), facet.get("intensity"))
            social = SOCIAL_LABELS.get(facet.get("social_density"), facet.get("social_density"))
            print(f"  推荐画像: {', '.join(facet.get('experience_modes', []))} | {intensity} | {social}")
            if facet.get("recommended_for"):
                print(f"  适合: {', '.join(facet.get('recommended_for', [])[:4])}")
        print(f"  简介: {item['summary']}")
        print(f"  来源: {item['url']}")
        printed += 1

    unit_results = []
    if args.q and CROSSWALK.exists():
        crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        for record in crosswalk.get("records", []):
            if args.container and args.container not in record.get("container", ""):
                continue
            for unit in record.get("units", []):
                if args.date and args.date not in unit.get("date_tags", []):
                    continue
                unit_haystack = " ".join([
                    unit.get("section_title", ""),
                    unit.get("unit_type", ""),
                    unit.get("time_range", ""),
                    unit.get("location_hint", ""),
                    " ".join(unit.get("topic_tags", [])),
                    " ".join(
                        term
                        for activity_id in unit.get("matched_activity_ids", [])
                        for term in facet_terms(activity_facets.get(str(activity_id)))
                    ),
                ]).lower()
                if not query_matches(unit_haystack, args.q):
                    continue
                unit_results.append((record, unit))

    remaining = max(0, args.limit - printed)
    for record, unit in unit_results[:remaining]:
        ids = [str(activity_id) for activity_id in unit.get("matched_activity_ids", [])]
        time_range = unit.get("time_range") or "时间待确认"
        location_hint = unit.get("location_hint") or "地点待确认"
        print(f"文章小节 | {record.get('container')} | {unit.get('section_title')} | {time_range} | {location_hint}")
        print(f"  来源文章: {display_source_title(record.get('article_title'))}")
        print(f"  主题: {', '.join(unit.get('topic_tags', []))}")
        if ids:
            print(f"  关联活动: {', '.join(ids)}")
            for activity_id in ids:
                activity = activity_lookup.get(activity_id)
                if activity:
                    print(f"  来源: {activity['url']}")
        printed += 1

    source_results = []
    if args.q and ARTICLE_EVIDENCE.exists():
        evidence = json.loads(ARTICLE_EVIDENCE.read_text(encoding="utf-8"))
        q_lower = args.q.lower()
        old_year_only = q_lower.strip() in {"2024", "2025"}
        if not old_year_only:
            for record in evidence.get("records", []):
                source_haystack = " ".join([
                    record.get("title", ""),
                    record.get("article_csv_title") or "",
                    record.get("manual_summary", ""),
                    " ".join(str(term) for term in record.get("search_terms", [])),
                    " ".join(str(activity_id) for activity_id in source_activity_ids(record, args.q)),
                    " ".join(facet_terms(article_facets.get(str(record.get("result_file"))))),
                ]).lower()
                if not query_matches(source_haystack, args.q):
                    continue
                score = query_score(source_haystack, args.q) + source_field_boost(record, args.q)
                source_results.append((score, record))

    remaining = max(0, args.limit - printed)
    source_results.sort(key=lambda pair: -pair[0])
    for _, record in source_results[:remaining]:
        ids = filter_activity_ids(
            source_activity_ids(record, args.q),
            activity_lookup,
            date=args.date,
            container=args.container,
        )
        print(f"文章线索 | {display_source_title(record.get('title'))}")
        source_facet = article_facets.get(str(record.get("result_file")))
        if source_facet:
            role = SOURCE_ROLE_LABELS.get(source_facet.get("source_role"), source_facet.get("source_role"))
            print(f"  用途: {role} | {source_facet.get('route_use')}")
        if record.get("manual_summary"):
            print(f"  摘要: {record.get('manual_summary')}")
        if record.get("article_url"):
            print(f"  公众号: {record.get('article_url')}")
        if ids:
            print(f"  关联活动: {', '.join(ids)}")
            for activity_id in ids:
                activity = activity_lookup.get(activity_id)
                if activity:
                    print(f"  来源: {activity['url']}")

    if args.debug:
        print(f"matched={len(results)} matched_units={len(unit_results)} matched_sources={len(source_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
