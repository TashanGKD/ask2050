#!/usr/bin/env python3
"""Build recommendation facets from ask2050 schedule and article evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


CONTAINER_DEFAULTS = {
    "新生论坛": {
        "experience_modes": ["听报告"],
        "participation_style": ["listen", "ask-after-session", "meet-speaker"],
        "recommended_for": ["系统学习者", "趋势观察者", "想快速了解一个领域的人"],
        "intensity": "medium",
        "social_density": "crowd",
        "planning_role": "main-anchor",
    },
    "探索空间": {
        "experience_modes": ["看展体验"],
        "participation_style": ["browse", "demo", "talk-to-builder"],
        "recommended_for": ["第一次来2050的人", "产品/项目实践者", "想看现场 demo 的人"],
        "intensity": "low",
        "social_density": "solo-friendly",
        "planning_role": "buffer",
    },
    "思想约会": {
        "experience_modes": ["深聊"],
        "participation_style": ["deep-talk", "roundtable", "co-think"],
        "recommended_for": ["愿意表达观点的人", "想认真聊天的人", "喜欢观点碰撞的人"],
        "intensity": "high",
        "social_density": "deep-talk",
        "planning_role": "main-anchor",
    },
    "热带雨林": {
        "experience_modes": ["找同伴", "放松恢复"],
        "participation_style": ["meetup", "casual-chat", "serendipity"],
        "recommended_for": ["第一次来2050的人", "想认识人但不想太紧绷的人", "低能量用户"],
        "intensity": "low",
        "social_density": "small-group",
        "planning_role": "social-anchor",
    },
    "青年团聚": {
        "experience_modes": ["找同伴"],
        "participation_style": ["community-meetup", "find-collaborators"],
        "recommended_for": ["想找组织的人", "社区参与者", "想找合作伙伴的人"],
        "intensity": "medium",
        "social_density": "small-group",
        "planning_role": "social-anchor",
    },
    "青春舞台": {
        "experience_modes": ["放松恢复", "夜间继续聊"],
        "participation_style": ["watch", "relax", "evening-social"],
        "recommended_for": ["想感受2050氛围的人", "高强度活动后的恢复用户", "结伴参会的人"],
        "intensity": "low",
        "social_density": "crowd",
        "planning_role": "evening-anchor",
    },
    "热力运动": {
        "experience_modes": ["户外身体活动"],
        "participation_style": ["sports", "team-up", "outdoor"],
        "recommended_for": ["想用身体活动社交的人", "运动爱好者", "想恢复状态的人"],
        "intensity": "high",
        "social_density": "small-group",
        "planning_role": "hands-on-anchor",
    },
    "星空露营": {
        "experience_modes": ["夜间继续聊", "放松恢复"],
        "participation_style": ["camping", "night-talk", "relax"],
        "recommended_for": ["想夜间继续交流的人", "不想再听密集报告的人", "露营和户外爱好者"],
        "intensity": "low",
        "social_density": "small-group",
        "planning_role": "evening-anchor",
    },
}

TOPIC_KEYWORDS = [
    ("ai", ["AI", "Agent", "智能体", "大模型", "人工智能", "OpenClaw", "Claw"]),
    ("education", ["教育", "学习", "学校", "课堂", "教师", "老师", "青少年", "儿童", "课程"]),
    ("health-medical", ["医疗", "健康", "生命", "基因", "罕见病", "医生", "患者", "科研"]),
    ("robotics-hardware", ["机器人", "硬件", "芯片", "具身", "GPU", "车载", "物理外挂", "制造", "工厂"]),
    ("arts-media-design", ["艺术", "影像", "电影", "设计", "手工艺", "音乐", "创作", "导演", "美学"]),
    ("opensource-tech", ["开源", "技术", "编程", "开发", "数据", "安全", "模型", "工具"]),
    ("startup-product", ["创业", "产品", "商业", "品牌", "一人公司", "增长", "生意"]),
    ("community-youth", ["社区", "团聚", "青年", "年青人", "伙伴", "同伴", "社群", "共创"]),
    ("philosophy-mind", ["哲学", "思想", "未来", "关系", "人生", "社会", "文明", "意义", "故事"]),
    ("life-sports", ["露营", "运动", "晨读", "美食", "咖啡", "八段锦", "旅行", "自然", "生活", "放松"]),
    ("social-impact", ["公益", "乡村", "城市", "无障碍", "社会", "可持续", "公共", "未来城邦"]),
]

MODE_KEYWORDS = [
    ("动手工作坊", "hands-on", ["工作坊", "黑客松", "动手", "共创", "实验", "训练营"]),
    ("看展体验", "demo", ["展示", "体验", "展台", "特展", "装置"]),
    ("深聊", "deep-talk", ["圆桌", "思想", "讨论", "对话", "聊天", "沙龙"]),
    ("找同伴", "community-meetup", ["团聚", "社群", "社区", "伙伴", "同伴", "找人", "合作"]),
    ("放松恢复", "relax", ["露营", "音乐", "舞台", "晨读", "咖啡", "美食", "自然", "八段锦"]),
    ("户外身体活动", "sports", ["运动", "篮球", "足球", "跑", "户外", "八段锦"]),
    ("生活补给", "logistics", ["交通", "餐饮", "PASS", "通行证", "攻略", "地图", "停车"]),
]

INTENSITY_LABELS = {
    "low": ["低强度", "轻松", "低能量", "放松"],
    "medium": ["中等强度", "适中"],
    "high": ["高强度", "投入", "烧脑"],
}

SOCIAL_LABELS = {
    "solo-friendly": ["一个人也能参加", "独自友好", "低社交压力"],
    "small-group": ["小组", "小范围交流", "轻社交"],
    "crowd": ["大场", "人多", "听众"],
    "deep-talk": ["深聊", "需要开口", "高社交密度"],
}

ROLE_LABELS = {
    "main-anchor": ["主线活动", "重点安排"],
    "buffer": ["缓冲点", "穿插活动"],
    "social-anchor": ["社交入口", "找同伴"],
    "hands-on-anchor": ["动手实践", "项目体验"],
    "evening-anchor": ["晚间活动", "晚上继续"],
    "logistics": ["后勤信息", "到场准备"],
    "wildcard": ["备选惊喜"],
}


def uniq(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def text_for(item: dict, *, include_location: bool = True) -> str:
    parts = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("container", ""),
        item.get("convener", ""),
    ]
    if include_location:
        parts.append(item.get("location", ""))
    return " ".join(
        str(part) for part in parts
    )


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text.lower() for needle in needles)


def infer_topics(item: dict) -> tuple[list[str], list[str]]:
    text = text_for(item)
    semantic_text = text_for(item, include_location=False)
    primary = []
    secondary = []
    for tag, needles in TOPIC_KEYWORDS:
        if contains_any(text, needles):
            primary.append(tag)
    if not primary:
        primary.extend(str(tag) for tag in item.get("topic_tags", [])[:2])
    for tag in item.get("topic_tags", []):
        if tag not in primary:
            secondary.append(str(tag))
    return uniq(primary[:4]), uniq(secondary[:8])


def infer_time_pattern(time_range: str) -> str:
    match = re.search(r"(\d{1,2}):(\d{2})", time_range or "")
    if not match:
        return "all-day"
    hour = int(match.group(1))
    if hour < 9:
        return "morning"
    if hour < 18:
        return "daytime"
    if hour < 22:
        return "evening"
    return "night"


def infer_venue_context(item: dict) -> str:
    text = text_for(item)
    if contains_any(text, ["露营", "帐篷", "草坪"]):
        return "camping"
    if contains_any(text, ["户外", "大草坪", "云栖之眼", "跑", "篮球", "足球"]):
        return "outdoor"
    if contains_any(text, ["餐饮", "美食", "咖啡", "百城味道"]):
        return "food"
    if contains_any(text, ["国际会展中心", "厅", "展台", "一楼", "二楼"]):
        return "indoor"
    return "unknown"


def adjust_intensity(base: str, text: str, time_range: str) -> str:
    if contains_any(text, ["黑客松", "竞赛", "比赛", "高强度", "深度", "圆桌"]):
        return "high"
    if contains_any(text, ["露营", "晨读", "咖啡", "美食", "舞台", "音乐", "随逛"]):
        return "low"
    if re.search(r"09:00-15:30|14:00-23:55", time_range or "") and base == "low":
        return "medium"
    return base


def infer_activity_facet(item: dict, article_linked_ids: set[str]) -> dict:
    defaults = CONTAINER_DEFAULTS.get(item.get("container"), CONTAINER_DEFAULTS["热带雨林"])
    text = text_for(item)
    semantic_text = text_for(item, include_location=False)
    primary, secondary = infer_topics(item)
    modes = list(defaults["experience_modes"])
    styles = list(defaults["participation_style"])
    recommended_for = list(defaults["recommended_for"])
    planning_role = defaults["planning_role"]

    for mode, style, needles in MODE_KEYWORDS:
        if contains_any(semantic_text, needles):
            modes.append(mode)
            styles.append(style)

    if contains_any(semantic_text, ["AI", "Agent", "智能体", "大模型", "OpenClaw", "Claw"]):
        recommended_for.append("AI 应用开发者")
    if contains_any(semantic_text, ["教育", "学习", "学校", "教师", "课堂"]):
        recommended_for.append("教育工作者")
    if contains_any(semantic_text, ["硬件", "机器人", "芯片", "具身", "车载"]):
        recommended_for.append("硬件/机器人方向")
    if contains_any(semantic_text, ["艺术", "设计", "影像", "电影", "音乐", "创作"]):
        recommended_for.append("创作者")
    if contains_any(semantic_text, ["创业", "产品", "商业", "品牌"]):
        recommended_for.append("产品和创业者")
    if contains_any(semantic_text, ["社群", "团聚", "伙伴", "同伴", "合作"]):
        recommended_for.append("想找同伴的人")

    if "动手工作坊" in modes:
        planning_role = "hands-on-anchor"
    if "生活补给" in modes:
        planning_role = "logistics"
    if "放松恢复" in modes and item.get("container") in {"青春舞台", "星空露营", "热带雨林"}:
        planning_role = "buffer" if item.get("container") == "热带雨林" else "evening-anchor"

    intensity = adjust_intensity(defaults["intensity"], semantic_text, item.get("time", ""))
    if intensity == "high":
        modes = [mode for mode in modes if mode != "放松恢复"]
        styles = [style for style in styles if style != "relax"]
        recommended_for = [
            person
            for person in recommended_for
            if person not in {"低能量用户", "想认识人但不想太紧绷的人"}
        ]
        if planning_role == "buffer":
            planning_role = "hands-on-anchor" if "动手工作坊" in modes else "main-anchor"
    social_density = defaults["social_density"]
    if contains_any(semantic_text, ["圆桌", "深聊", "思想约会", "聊天"]):
        social_density = "deep-talk"
    elif contains_any(semantic_text, ["工作坊", "小组", "晨读", "咖啡"]):
        social_density = "small-group"
    elif contains_any(semantic_text, ["论坛", "舞台", "大会", "音乐会"]):
        social_density = "crowd"

    source_level = "article-linked" if str(item.get("activity_id")) in article_linked_ids else "schedule"
    route_note = item.get("summary") or f"{item.get('container')}中的{item.get('title')}"

    search_terms = [
        str(item.get("activity_id", "")),
        item.get("title", ""),
        item.get("container", ""),
        item.get("convener", ""),
        item.get("location", ""),
        *INTENSITY_LABELS.get(intensity, []),
        *SOCIAL_LABELS.get(social_density, []),
        *ROLE_LABELS.get(planning_role, []),
        *primary,
        *secondary,
        *modes,
        *styles,
        *recommended_for,
    ]

    return {
        "activity_id": str(item.get("activity_id")),
        "primary_topics": primary,
        "secondary_topics": secondary,
        "experience_modes": uniq(modes),
        "participation_style": uniq(styles),
        "recommended_for": uniq(recommended_for),
        "intensity": intensity,
        "social_density": social_density,
        "planning_role": planning_role,
        "time_pattern": infer_time_pattern(item.get("time", "")),
        "venue_context": infer_venue_context(item),
        "route_note": route_note,
        "source_level": source_level,
        "search_terms": uniq([str(term) for term in search_terms if term]),
    }


def infer_source_role(record: dict) -> str:
    text = " ".join(
        str(part)
        for part in [record.get("title", ""), record.get("manual_summary", ""), " ".join(record.get("search_terms", []))]
    )
    if contains_any(text, ["交通", "餐饮", "PASS", "通行证", "攻略", "地图", "停车"]):
        return "logistics-guide"
    if contains_any(text, ["日程", "活动全整理", "节目单", "三日活动"]):
        return "schedule-update"
    if contains_any(text, ["召集", "招募", "报名", "来找我们", "邀你"]):
        return "community-call"
    if contains_any(text, ["为什么", "逻辑", "背景", "倒计时"]):
        return "background"
    if record.get("matched_activity_ids"):
        return "program-guide"
    return "mixed"


def infer_article_facet(record: dict) -> dict:
    text = {
        "title": record.get("title", ""),
        "summary": record.get("manual_summary", ""),
        "container": "",
        "location": "",
        "convener": "",
        "topic_tags": [],
    }
    primary, secondary = infer_topics(text)
    role = infer_source_role(record)
    modes = []
    styles = []
    combined = " ".join([record.get("title", ""), record.get("manual_summary", "")])
    for mode, style, needles in MODE_KEYWORDS:
        if contains_any(combined, needles):
            modes.append(mode)
            styles.append(style)
    aliases = [
        term
        for term in record.get("search_terms", [])
        if term and not str(term).isdigit() and len(str(term)) <= 40
    ][:12]
    confidence = "high" if record.get("matched_activity_ids") else "medium"
    if role in {"background", "mixed"} and not record.get("matched_activity_ids"):
        confidence = "low"
    return {
        "source_id": record.get("result_file"),
        "article_url": record.get("article_url"),
        "source_role": role,
        "linked_activity_ids": [str(activity_id) for activity_id in record.get("matched_activity_ids", [])],
        "communities_or_aliases": uniq([str(term) for term in aliases]),
        "extracted_topics": uniq(primary + secondary[:4]),
        "experience_modes": uniq(modes),
        "participation_style": uniq(styles),
        "route_use": route_use_for_role(role),
        "confidence": confidence,
        "search_terms": uniq([record.get("title", ""), record.get("manual_summary", ""), *aliases]),
    }


def route_use_for_role(role: str) -> str:
    return {
        "schedule-update": "补充活动安排和跨日路线线索",
        "program-guide": "解释某个活动或板块的具体内容",
        "community-call": "补充社群、伙伴和招募语境",
        "logistics-guide": "补充到场、交通、通行证、餐饮或地图信息",
        "map-guide": "补充地点和动线信息",
        "background": "解释2050机制或文章背景，不直接替代活动安排",
        "mixed": "作为补充线索，推荐前需回查活动主表",
    }.get(role, "作为补充线索")


def main() -> int:
    activities = json.loads((REF / "activity_index.min.json").read_text(encoding="utf-8"))
    evidence = json.loads((REF / "article_evidence_index.json").read_text(encoding="utf-8"))

    article_linked_ids = {
        str(activity_id)
        for record in evidence.get("records", [])
        for activity_id in record.get("matched_activity_ids", [])
    }

    activity_facets = {
        str(item.get("activity_id")): infer_activity_facet(item, article_linked_ids)
        for item in activities
    }
    article_facets = {
        str(record.get("result_file")): infer_article_facet(record)
        for record in evidence.get("records", [])
    }

    (REF / "activity_facets.json").write_text(
        json.dumps(activity_facets, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (REF / "article_facets.json").write_text(
        json.dumps(article_facets, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(activity_facets)} activity facets and {len(article_facets)} article facets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
