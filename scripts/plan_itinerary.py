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
JSON_CACHE: dict[str, object] = {}
PLAN_CACHE: dict[tuple[str, str], dict] = {}

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
    "晨型": ["早起", "晨读", "上午"],
    "早起": ["晨型", "晨读", "上午"],
    "早睡": ["不安排晚间", "晚上回酒店"],
    "行动不便": ["少走路", "不跨区", "同区"],
    "不想跨区": ["少走路", "同区"],
    "创业者": ["创业", "产品", "startup", "找合作"],
    "产品经理": ["产品", "创业", "用户", "商业"],
    "找合作": ["合作", "社区", "同伴", "找同伴"],
    "效率": ["高密度", "最多", "效率优先"],
    "高密度": ["效率优先", "参加最多", "尽量多"],
    "最多": ["高密度", "效率优先"],
    "半天": ["半天", "只排半天"],
    "睡觉": ["休息", "不想参加", "低意愿"],
    "躺平": ["休息", "不想参加", "低意愿"],
    "新生论坛": ["新生论坛"],
    "探索空间": ["探索空间", "展台", "展区"],
    "思想约会": ["思想约会"],
    "青年团聚": ["青年团聚", "团聚"],
    "热带雨林": ["热带雨林"],
}

INTENT_KEYWORDS = {
    "research_science": ["ai4s", "ai4science", "科研", "博士", "天文学", "科学研究", "物理"],
    "space_astronomy": ["天文学", "太空", "宇宙", "地外文明", "星空", "露营", "银河", "科幻"],
    "education": ["教育", "科普", "科教", "课程", "学习", "老师", "学校", "教研"],
    "hardware": ["硬件", "机器人", "芯片", "具身", "制造", "robotics-hardware"],
    "philosophy": ["哲学", "思想", "人文", "深聊", "观点", "社会科学"],
    "community": ["社区", "社群", "运营", "找同伴", "小团体", "合作"],
    "startup_product": ["创业", "产品", "一人公司", "独立开发", "少数派", "产品共创", "独立开发者", "超级个体"],
    "arts": ["艺术", "创作", "音乐", "表演", "影像", "设计"],
    "low_energy": ["低能量", "轻松", "放松", "不想太累", "随便逛"],
    "no_participation": ["睡觉", "躺平", "不想参加", "只想休息", "不想出门"],
    "mobility_limited": ["行动不便", "不想跨区", "少走路", "同区", "轮椅"],
    "max_density": ["效率优先", "参加最多", "高密度", "尽量多", "最多"],
    "morning_person": ["晨型", "早起", "上午优先", "晨读"],
    "early_sleep": ["早睡", "晚上回酒店", "不想太晚", "不熬夜"],
    "half_day": ["半天", "只排半天", "半日"],
    "morning_only": ["上午优先", "只排上午", "上午可参加", "上午半天"],
    "afternoon_only": ["下午优先", "只排下午", "下午可参加", "下午半天"],
}

ZONE_ORDER = {"D区": 0, "C区": 1, "B区": 2, "A区": 3, "户外": 4, "未知": 5}
EVENING_TERMS = ["晚上", "夜间", "露营", "音乐", "舞台", "放松收尾", "晚间"]
HARDWARE_TERMS = ["硬件", "机器人", "芯片", "具身", "制造", "openclaw", "物理外挂", "maker"]
COMMUNITY_TERMS = ["社区", "社群", "共创", "合作", "waytoagi", "builder", "开源", "找同伴"]
STRONG_COMMUNITY_TERMS = ["社区", "社群", "合作伙伴", "共建", "waytoagi", "builder", "开源", "找同伴"]
STARTUP_TERMS = ["创业", "产品", "一人公司", "独立开发", "少数派", "共创", "超级个体", "ncc", "opc"]
STARTUP_FORUM_TERMS = STARTUP_TERMS + ["企业家", "ceo", "科创", "商业", "公司", "项目", "孵化", "pitch"]
EDUCATION_CONNECTION_TERMS = ["教育", "科普", "科教", "课程", "学习", "学校", "教研", "青少年", "社区", "社群", "青年", "同伴", "伙伴", "教练", "对话"]
SPACE_TERMS = ["天文", "太空", "宇宙", "地外", "星空", "银河", "露营", "科幻", "冷湖"]
ROMANCE_TERMS = ["说媒", "相亲", "恋爱", "婚恋"]


def load_json(path: Path):
    cache_key = str(path.resolve())
    if cache_key not in JSON_CACHE:
        with open(path, "r", encoding="utf-8") as handle:
            JSON_CACHE[cache_key] = json.load(handle)
    return JSON_CACHE[cache_key]


def clone_json(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


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


def overlap_window(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


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


def has_explicit_evening_preference(profile: str, terms: list[str]) -> bool:
    text = f"{profile.lower()} {' '.join(terms)}"
    return contains_any(text, EVENING_TERMS)


def has_forum_anchor(plan: dict) -> bool:
    return any(item.get("container") == "新生论坛" for item in plan.get("items", []))


def forum_anchor_is_optional(profile: str, date: str, intents: set[str]) -> bool:
    if date != "2026-04-24":
        return False
    if not ({"low_energy", "early_sleep", "morning_person", "half_day", "morning_only", "afternoon_only"} & intents):
        return False
    activities = load_json(REF / "activity_index.min.json")
    forum_windows = [
        parse_time_range(str(item.get("time", "")))
        for item in activities
        if item.get("date") == date and item.get("container") == "新生论坛"
    ]
    forum_windows = [window for window in forum_windows if window]
    return bool(forum_windows) and all(window[0] >= 19 * 60 for window in forum_windows)


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def location_zone(location: str) -> str:
    value = str(location or "")
    for zone in ["A区", "B区", "C区", "D区"]:
        if zone in value:
            return zone
    if any(term in value for term in ["户外", "草坪", "星空露营", "云栖之眼", "帐篷", "绿地"]):
        return "户外"
    return "未知"


def zone_distance(left: str, right: str) -> int:
    if left == "未知" or right == "未知":
        return 1
    return abs(ZONE_ORDER.get(left, 5) - ZONE_ORDER.get(right, 5))


def transition_note(previous: dict | None, current: dict) -> str:
    if not previous:
        return "首站，建议提前到场找入口。"
    prev_zone = location_zone(str(previous.get("location", "")))
    curr_zone = location_zone(str(current.get("location", "")))
    distance = zone_distance(prev_zone, curr_zone)
    if distance == 0:
        minutes_needed = "5-10"
    elif distance == 1:
        minutes_needed = "10-20"
    elif "户外" in {prev_zone, curr_zone}:
        minutes_needed = "20-30"
    else:
        minutes_needed = "15-25"
    prev_window = str(previous.get("suggested_window", ""))
    curr_window = str(current.get("suggested_window", ""))
    try:
        prev_end = minutes(prev_window.split("-")[-1])
        curr_start = minutes(curr_window.split("-")[0])
    except Exception:
        prev_end = curr_start = 0
    if curr_start - prev_end >= 45:
        return f"中间有 {curr_start - prev_end} 分钟缓冲，可休息、吃饭或提前找入口。"
    if 0 <= curr_start - prev_end < 10:
        return "两站衔接很紧，建议上一站提前 5-10 分钟离场；做不到就把后一站作为备选。"
    depart = prev_window.split("-")[-1] if "-" in prev_window else "上一站结束后"
    return f"从上一站约 {minutes_needed} 分钟；建议 {depart} 左右出发。"


INTENT_LABELS = {
    "research_science": "科研/科学",
    "space_astronomy": "太空/天文",
    "education": "教育/科普",
    "hardware": "硬件/机器人",
    "philosophy": "哲学/深聊",
    "community": "社区/找同伴",
    "startup_product": "产品/创业",
    "arts": "艺术/创作",
    "low_energy": "低能量",
    "mobility_limited": "少走路",
    "max_density": "高密度",
}

ROLE_LABELS = {
    "晨间入口": "低压力进入现场",
    "午间桥接": "填补同主题短窗口",
    "论坛延展": "补一个不重叠的主题输入",
    "认知主线": "建立当天判断框架",
    "实践体验": "把主题落到项目或体验",
    "补充体验": "增加可执行的同主题停留点",
    "深聊/社群": "找人聊、找组织或形成连接",
    "晚间收尾": "低压力收束和继续交流",
}


def matched_profile_labels(intents: set[str], text: str) -> list[str]:
    labels = []
    lower_text = text.lower()
    for intent, label in INTENT_LABELS.items():
        if intent not in intents:
            continue
        if intent in {"low_energy", "mobility_limited", "max_density"}:
            labels.append(label)
            continue
        if intent == "hardware" and contains_any(lower_text, HARDWARE_TERMS):
            labels.append(label)
        elif intent == "community" and contains_any(lower_text, COMMUNITY_TERMS):
            labels.append(label)
        elif intent == "startup_product" and contains_any(lower_text, STARTUP_FORUM_TERMS):
            labels.append(label)
        elif intent == "education" and contains_any(lower_text, EDUCATION_CONNECTION_TERMS):
            labels.append(label)
        elif intent == "space_astronomy" and contains_any(lower_text, SPACE_TERMS):
            labels.append(label)
        elif intent == "philosophy" and contains_any(lower_text, ["哲学", "思想", "人文", "深聊", "观点"]):
            labels.append(label)
        elif intent == "research_science" and contains_any(lower_text, ["科研", "科学", "ai4science", "物理", "数学"]):
            labels.append(label)
        elif intent == "arts" and contains_any(lower_text, ["艺术", "创作", "影像", "音乐", "设计"]):
            labels.append(label)
    return list(dict.fromkeys(labels))


def service_reason(label: str, route_item: dict, facet: dict, intents: set[str]) -> tuple[list[str], str, str]:
    text = " ".join(
        str(route_item.get(key, ""))
        for key in ["title", "summary", "container", "location"]
    )
    matched = matched_profile_labels(intents, text)
    role = ROLE_LABELS.get(label, label)
    summary = str(route_item.get("summary") or facet.get("route_note") or "").strip()
    if matched:
        reason = f"匹配你的{ '、'.join(matched[:3]) }取向；这一站用于{role}。{summary}"
    else:
        reason = f"这一站用于{role}。{summary}"
    fallback = "如果现场太赶，把这一站降为备选，优先保留前后更贴近画像的主线。"
    if label == "认知主线":
        fallback = "如果只能短暂停留，建议听开头或最相关的一段，把后续同窗活动作为备选。"
    elif label in {"实践体验", "补充体验", "午间桥接"}:
        fallback = "如果换场太紧，保留论坛主线，把这一站改成路过看展或备选。"
    elif label in {"深聊/社群", "晚间收尾"}:
        fallback = "如果当时精力不够，直接跳过，不影响白天主线。"
    return matched, reason, fallback


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
    semantic_text = " ".join([title, str(item.get("summary", "")).lower(), container.lower()])
    score = 0
    for term in terms:
        if term in title:
            score += 18
        if term in text:
            score += 7
    if role == "forum" and container == "新生论坛":
        score += 70
    if role == "practice" and container in {"探索空间", "热带雨林"}:
        score += 25
    if role == "practice" and "探索空间" in terms and container == "探索空间":
        score += 140
    if role == "practice" and "探索空间" in terms and container != "探索空间":
        score -= 320
    if role == "deep_talk" and "思想约会" in terms and container == "思想约会":
        score += 120
    if role == "social" and any(term in terms for term in ["青年团聚", "团聚"]) and container == "青年团聚":
        score += 120
    if role == "bridge" and container in {"探索空间", "热带雨林"}:
        score += 22
    if role == "deep_talk" and container in {"思想约会", "星空露营"}:
        score += 25
    if role == "social" and container in {"青年团聚", "热带雨林", "探索空间"}:
        score += 18
    if role == "evening" and container in {"星空露营", "青春舞台"}:
        score += 30
    if role == "practice" and facet and "动手工作坊" in facet.get("experience_modes", []):
        score += 14
    if role == "bridge" and facet:
        if "动手工作坊" in facet.get("experience_modes", []):
            score += 18
        if facet.get("intensity") == "low":
            score += 10
    explicit_ai4science = any(term in terms for term in ["ai4s", "ai4science", "agi4science"])
    if role == "forum" and ("ai4science" in text or "agi4science" in text):
        if explicit_ai4science:
            score += 240
        elif "research_science" in intents:
            score += 80
        else:
            score -= 25
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
    if role == "forum" and "startup_product" in intents and contains_any(text, STARTUP_TERMS):
        score += 60
        if contains_any(title, STARTUP_TERMS):
            score += 35
    if role == "forum" and "startup_product" in intents:
        if contains_any(semantic_text, STARTUP_FORUM_TERMS):
            score += 45
            if contains_any(title, ["创业", "企业家", "ceo", "科创", "一人公司", "项目", "孵化"]):
                score += 45
        else:
            score -= 100
    if role == "forum" and any(term in terms for term in ["太空", "宇宙", "地外文明", "物理"]) and (
        "太空" in text or "宇宙" in text or "地外文明" in text or "物理" in text
    ):
        score += 35
    if "space_astronomy" in intents and contains_any(semantic_text, SPACE_TERMS):
        score += 140
        if contains_any(title, SPACE_TERMS):
            score += 70
    if explicit_ai4science and ("ai4science" in text or "agi4science" in text):
        score += 160
    if "科学" in terms and "科学" in title:
        score += 25
    if role == "practice" and ("硬件" in text or "动手" in text):
        score += 35
    if role == "bridge" and ("硬件" in text or "动手" in text or "demo" in text or "展示" in text):
        score += 28
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
    if role in {"practice", "bridge", "deep_talk", "social"} and "startup_product" in intents and contains_any(text, STARTUP_TERMS):
        score += 70
        if contains_any(title, STARTUP_TERMS):
            score += 40
    if role == "practice" and "arts" not in intents and contains_any(title, ["音乐", "舞蹈", "混音", "声音橡皮泥"]):
        score -= 85
    if contains_any(title, ROMANCE_TERMS) and not contains_any(" ".join(terms), ROMANCE_TERMS + ["找对象", "情感"]):
        score -= 180
    if "no_participation" in intents:
        if facet and facet.get("intensity") == "low":
            score += 25
        if role in {"forum", "practice", "deep_talk"}:
            score -= 140
        if role == "evening":
            score -= 60
        if contains_any(text, ["休息", "放松", "低强度", "草坪", "散步"]):
            score += 45
    if "mobility_limited" in intents:
        if location_zone(str(item.get("location", ""))) != "未知":
            score += 25
        if "户外" == location_zone(str(item.get("location", ""))):
            score -= 35
        if facet and facet.get("intensity") == "high":
            score -= 170
        official = parse_time_range(str(item.get("time", "")))
        if official and official[1] - official[0] > 180 and role != "forum":
            score -= 80
    if "morning_person" in intents and role == "social":
        if contains_any(text, ["晨读", "早晨", "上午", "07:00", "08:00"]):
            score += 90
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
    if official and "morning_person" in intents and role == "social" and official[0] < 9 * 60:
        score += 100
    if official and "early_sleep" in intents and official[0] >= 19 * 60:
        score -= 220
    if official and "max_density" in intents:
        duration = official[1] - official[0]
        if duration <= 90:
            score += 35
        elif duration > 180 and role != "forum":
            score -= 25
    if role == "evening" and official:
        if 19 * 60 <= official[0] <= 21 * 60:
            score += 35
        if official[0] >= 23 * 60 and "arts" not in intents and "夜间" not in terms and "深夜" not in terms:
            score -= 250
    if role == "practice" and official and official[1] - official[0] <= 150:
        score += 25
    if role == "practice" and ("教育" in terms or "科普" in terms or "科教" in terms) and ("课程" in text or "学习" in text):
        score += 20
    if role == "bridge" and official:
        duration = official[1] - official[0]
        if duration <= 90:
            score += 35
        elif duration > 180:
            score += 12
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
    semantic_text = " ".join([title, str(session.get("summary", "")).lower(), str(session.get("container", "")).lower()])
    score = 0
    for term in terms:
        if term in title:
            score += 20
        if term in text:
            score += 8
    if role == "forum":
        score += 35
    explicit_ai4science = any(term in terms for term in ["ai4s", "ai4science", "agi4science"])
    if "ai4science" in text or "agi4science" in text:
        if explicit_ai4science:
            score += 220
        elif "research_science" in intents:
            score += 80
        else:
            score -= 20
    if explicit_ai4science and ("ai4science" in text or "agi4science" in text):
        score += 120
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
    if role == "forum" and "startup_product" in intents and contains_any(text, STARTUP_TERMS):
        score += 65
    if role == "forum" and "startup_product" in intents:
        if contains_any(semantic_text, STARTUP_FORUM_TERMS):
            score += 45
            if contains_any(title, ["创业", "企业家", "ceo", "科创", "一人公司", "项目", "孵化"]):
                score += 45
        else:
            score -= 100
    if role == "forum" and "space_astronomy" in intents and contains_any(semantic_text, SPACE_TERMS):
        score += 140
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


def scored_choices(
    activities: list[dict],
    facets: dict,
    *,
    date: str,
    terms: list[str],
    role: str,
    containers: set[str],
    exclude_ids: set[str],
    intents: set[str] | None = None,
) -> list[tuple[int, dict]]:
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
    return candidates


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
    candidates = scored_choices(
        activities,
        facets,
        date=date,
        terms=terms,
        role=role,
        containers=containers,
        exclude_ids=exclude_ids,
        intents=intents,
    )
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


def planned_window(
    item: dict,
    role: str,
    occupied: list[tuple[int, int]],
    *,
    compact: bool = False,
) -> tuple[int, int]:
    official = parse_time_range(str(item.get("time", "")))
    if not official:
        raise ValueError(f"activity without parseable time: {item.get('activity_id')}")
    start, end = official
    duration = end - start
    if (item.get("container") in LONG_WINDOW_CONTAINERS and duration > 90) or duration > 180:
        forum_primary = 90 if compact else 120
        forum_secondary = 150 if compact else 180
        role_windows = {
            "forum": [(start, min(start + forum_primary, end)), (start + 60, min(start + forum_secondary, end))],
            "bridge": [(max(start, 11 * 60), min(max(start, 11 * 60) + 45, end)), (max(start, 12 * 60), min(max(start, 12 * 60) + 45, end))],
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


def build_plan(profile: str, date: str, requested_window: tuple[int, int] | None = None) -> dict:
    cache_key = (profile, date, requested_window or ("", ""))
    if cache_key in PLAN_CACHE:
        return clone_json(PLAN_CACHE[cache_key])
    activities = load_json(REF / "activity_index.min.json")
    facets = load_json(REF / "activity_facets.json")
    terms = profile_terms(profile)
    intents = profile_intents(profile, terms)
    wants_evening = has_explicit_evening_preference(profile, terms)
    exclude_ids: set[str] = set()
    occupied: list[tuple[int, int]] = []
    rows = []
    anchor_zone = ""
    compact_windows = bool(requested_window) or "half_day" in intents

    if "no_participation" in intents:
        plan = {
            "date": date,
            "profile": profile,
            "intents": sorted(intents),
            "items": [],
            "advice": [
                "你明确表达了不想参加活动，路线规划应尊重这个约束，不强行推荐论坛或展台。",
                "如果只是想保留一个低压力备选，现场可临时选择热带雨林、草坪休息、餐饮补给或晚间轻松节目。",
                "恢复后再重新给出兴趣、日期和精力，我再按低强度路线重新排。",
            ],
        }
        PLAN_CACHE[cache_key] = plan
        return clone_json(plan)
    else:
        slots = [
            ("晨间入口", "social", {"热带雨林"}, "晨型或早起用户可用低压力活动进入状态。"),
            ("认知主线", "forum", {"新生论坛"}, "先建立当天主题骨架；不要再并排安排另一个上午长时段活动。"),
            ("实践体验", "practice", {"探索空间", "热带雨林"}, "把论坛里的概念落到项目、硬件或课程原型上。"),
            ("深聊/社群", "deep_talk", {"思想约会", "青年团聚", "热带雨林"}, "选择一个讨论或社群入口，不和实践体验并行。"),
            ("晚间收尾", "evening", {"星空露营", "青春舞台"}, "用低压力场景收束当天，也适合继续聊。"),
        ]
        if "morning_person" not in intents:
            slots = [slot for slot in slots if slot[0] != "晨间入口"]
        if "early_sleep" in intents:
            slots = [slot for slot in slots if slot[1] != "evening"]
        if "low_energy" in intents and not wants_evening:
            slots = [slot for slot in slots if slot[1] != "evening"]
        if "half_day" in intents and not wants_evening:
            slots = [slot for slot in slots if slot[1] != "evening"]
        if "max_density" in intents:
            if {"startup_product", "community"} & intents:
                slots.insert(1, ("论坛延展", "forum", {"新生论坛"}, "高密度且主题相关时，可以接第二个不重叠的新生论坛或项目 pitch。"))
            slots.insert(1, ("午间桥接", "bridge", {"探索空间", "热带雨林"}, "效率优先时用短窗口补一个同主题项目，避免上午主线后空档过长。"))
            slots.insert(3, ("补充体验", "practice", {"探索空间", "热带雨林", "青年团聚"}, "效率优先时增加一个不重叠的短窗口。"))
        max_items = 6 if "max_density" in intents else 2 if "mobility_limited" in intents else 4
        if "half_day" in intents:
            max_items = min(max_items, 3)
        if "low_energy" in intents:
            max_items = min(max_items, 3)
        if requested_window and requested_window[1] - requested_window[0] <= 300:
            max_items = min(max_items, 2)
    for label, role, containers, reason in slots:
        if len(rows) >= max_items:
            break
        selected = None
        viable = []
        for base_score, item in scored_choices(
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
            route_zone = location_zone(str(route_item.get("location", "")))
            if "mobility_limited" in intents and anchor_zone and route_zone != "未知" and zone_distance(anchor_zone, route_zone) > 0:
                continue
            window = planned_window(route_item, role, occupied, compact=compact_windows)
            if overlaps(window, occupied):
                continue
            if requested_window and not overlap_window(window, requested_window):
                continue
            if window[0] < 9 * 60 and "morning_person" not in intents:
                continue
            if label == "晨间入口" and window[0] >= 9 * 60:
                continue
            if "morning_only" in intents and window[0] >= 13 * 60:
                continue
            if "afternoon_only" in intents and window[1] <= 12 * 60:
                continue
            if "afternoon_only" in intents and window[0] < 13 * 60:
                base_score -= 90
            if role == "evening" and window[0] < 18 * 60:
                continue
            if "half_day" in intents and window[0] >= 18 * 60 and not wants_evening:
                continue
            if window[1] > 19 * 60 and not wants_evening and not (role == "forum" and date == "2026-04-24"):
                continue
            if "half_day" in intents and occupied:
                first_start = min(start for start, _ in occupied)
                if window[0] - first_start > 240 or window[1] - first_start > 300:
                    continue
            adjusted_score = base_score
            if session:
                adjusted_score += 8
            if occupied:
                last_end = max(end for _, end in occupied)
                gap = max(0, window[0] - last_end)
                if "max_density" in intents:
                    adjusted_score -= gap * 2
                    if gap <= 30:
                        adjusted_score += 80
                    elif gap <= 90:
                        adjusted_score += 40
                if "mobility_limited" in intents:
                    adjusted_score -= max(0, gap - 90)
            if "morning_person" in intents and label != "晨间入口" and window[0] < 9 * 60:
                adjusted_score -= 220
            if "early_sleep" in intents and window[0] >= 19 * 60:
                adjusted_score -= 500
            candidate_text = haystack(route_item, facets.get(str(item.get("activity_id")), {}))
            direct_text = " ".join(
                str(route_item.get(key, ""))
                for key in ["title", "summary", "container", "location"]
            ).lower()
            semantic_direct_text = " ".join(
                str(route_item.get(key, ""))
                for key in ["title", "summary", "container"]
            ).lower()
            facet = facets.get(str(item.get("activity_id")), {})
            if "low_energy" in intents:
                if facet.get("intensity") == "high":
                    adjusted_score -= 260
                if role == "deep_talk" and facet.get("social_density") == "deep-talk":
                    adjusted_score -= 140
                if window[0] >= 19 * 60 and not wants_evening:
                    adjusted_score -= 320
            if "mobility_limited" in intents:
                if facet.get("intensity") == "high":
                    adjusted_score -= 260
                if role == "practice" and str(item.get("time", "")).endswith("15:30"):
                    adjusted_score -= 120
            if "hardware" in intents and role in {"bridge", "practice"} and not contains_any(
                direct_text,
                HARDWARE_TERMS,
            ):
                adjusted_score -= 320
            if "hardware" in intents and role == "deep_talk" and not contains_any(
                direct_text,
                HARDWARE_TERMS + STRONG_COMMUNITY_TERMS,
            ):
                adjusted_score = -1
            if "community" in intents and role == "deep_talk" and not contains_any(
                direct_text,
                COMMUNITY_TERMS,
            ):
                adjusted_score -= 220
            if "community" in intents and role == "practice" and "hardware" not in intents and not contains_any(
                direct_text,
                COMMUNITY_TERMS + ["互助", "志愿", "青年", "团聚", "对话"],
            ):
                adjusted_score -= 220
            if label != "晨间入口" and "education" in intents and role in {"practice", "deep_talk", "social"} and not contains_any(
                semantic_direct_text,
                EDUCATION_CONNECTION_TERMS,
            ):
                adjusted_score -= 260
            if "startup_product" in intents and role in {"practice", "bridge", "deep_talk", "social"} and not contains_any(
                direct_text,
                STARTUP_TERMS + COMMUNITY_TERMS,
            ):
                adjusted_score -= 320
            if "startup_product" in intents and role == "forum" and not contains_any(
                semantic_direct_text,
                STARTUP_FORUM_TERMS,
            ):
                adjusted_score -= 320
            if "space_astronomy" in intents and role in {"practice", "bridge", "deep_talk", "social"} and not contains_any(
                semantic_direct_text,
                SPACE_TERMS + ["社区", "深聊", "哲学"],
            ):
                adjusted_score -= 300
            if "max_density" in intents and role == "evening" and not contains_any(
                direct_text,
                HARDWARE_TERMS + COMMUNITY_TERMS + ["音乐", "露营"],
            ):
                adjusted_score -= 180
            if role == "evening" and window[0] >= 21 * 60 and not wants_evening:
                adjusted_score -= 260
            if role == "evening" and not wants_evening:
                adjusted_score -= 260
            if adjusted_score <= 0:
                continue
            viable.append((adjusted_score, base_score, item, route_item, session, window))
        if viable:
            viable.sort(key=lambda pair: (-pair[0], -pair[1], pair[5][0], pair[2].get("title", "")))
            _, _, item, route_item, session, window = viable[0]
            selected = (item, route_item, session, window)
        if not selected:
            continue
        item, route_item, session, window = selected
        activity_id = str(item.get("activity_id"))
        facet = facets.get(activity_id, {})
        occupied.append(window)
        exclude_ids.add(activity_id)
        if not anchor_zone:
            candidate_zone = location_zone(str(route_item.get("location", "")))
            if candidate_zone != "未知":
                anchor_zone = candidate_zone
        matched_labels, fit_reason, fallback_note = service_reason(label, route_item, facet, intents)
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
                "route_role": ROLE_LABELS.get(label, label),
                "matched_profile": matched_labels,
                "why_fit": fit_reason,
                "fallback_note": fallback_note,
                "intensity": INTENSITY_LABELS.get(str(facet.get("intensity", "")), str(facet.get("intensity", "")) or "待判断"),
                "source": route_item.get("source") or item.get("url", ""),
            }
        )
    rows.sort(key=lambda row: minutes(row["suggested_window"].split("-")[0]))
    previous = None
    for row in rows:
        row["move_note"] = transition_note(previous, row)
        if row["move_note"].startswith("两站衔接很紧"):
            row["fallback_note"] = row["move_note"]
        previous = row
    advice = []
    if not rows and "no_participation" not in intents:
        advice.append("当前日期和画像约束下没有合适主线；建议放宽到下午/晚上、减少主题限制，或换到 4/25、4/26 再排。")
    if requested_window:
        advice.append(f"这次已按 {fmt(requested_window[0])}-{fmt(requested_window[1])} 的在场窗口收缩候选；如果现场时间放宽，再补排其余时段。")
    if "探索空间" in profile and not any(row.get("container") == "探索空间" for row in rows):
        advice.append("你点名想看探索空间，但这个时段里和主论坛不冲突的合适停留窗口不多；如果愿意把论坛缩短到 60-75 分钟，或把到场时间提前到 14:30 前，可以再补一个展台停留。")
    if rows and not any(row.get("container") == "新生论坛" for row in rows) and forum_anchor_is_optional(profile, date, intents):
        constraints = []
        if "low_energy" in intents:
            constraints.append("低强度")
        if "half_day" in intents or requested_window:
            constraints.append("短时段")
        if "early_sleep" in intents:
            constraints.append("早睡")
        if constraints:
            reason_text = "、".join(constraints)
            advice.append(f"这一天可用的新生论坛主线在晚间；你这次更偏{reason_text}，所以先不硬塞，若晚上仍有精力可把 AI 小酒馆作为备选。")
        else:
            advice.append("这一天可用的新生论坛主线在晚间；当前先保留白天更顺路的活动，若晚上仍有精力可把 AI 小酒馆作为备选。")
    if "half_day" in intents:
        advice.append("你说只能半天参加，主线会控制在相邻时间段内；晚间和跨度过大的活动默认不进主线。")
    plan = {"date": date, "profile": profile, "intents": sorted(intents), "items": rows}
    if advice:
        plan["advice"] = advice
    PLAN_CACHE[cache_key] = plan
    return clone_json(plan)


def validate_plan(plan: dict) -> list[str]:
    errors = []
    intents = set(plan.get("intents", []))
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
    if "no_participation" not in intents and not has_forum_anchor(plan) and not forum_anchor_is_optional(
        str(plan.get("profile", "")),
        str(plan.get("date", "")),
        intents,
    ):
        errors.append("缺少新生论坛认知主线")
    return errors


def print_markdown(plan: dict) -> None:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()

    print(f"推荐路线（{plan['date']}）")
    print()
    if not plan.get("items"):
        for line in plan.get("advice", ["没有生成活动路线。"]):
            print(f"- {line}")
        return
    print("说明：下面是可执行的停留顺序。官方长时段活动只安排一个进入窗口，不代表需要全程占用；同一时间只保留一个去处。")
    print()
    print("| 建议窗口 | 官方时段 | 板块 | 活动 | 地点 | 换场 | 为什么适合 | 太赶时 |")
    print("|---|---|---|---|---|---|---|---|")
    for item in plan["items"]:
        print(
            "| "
            + " | ".join(
                cell(item.get(key, ""))
                for key in ["suggested_window", "official_time", "container", "title", "location", "move_note", "why_fit", "fallback_note"]
            )
            + " |"
        )
    print()
    if plan.get("advice"):
        print("补充说明：")
        for line in plan.get("advice", []):
            print(f"- {line}")
        print()
    print("备选规则：如果现场确认某个 09:00-15:30 长时段活动必须全程参加，就不要再把同一时段的思想约会或探索空间排进主线，只能改成备选。")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成带时间冲突校验的 ask2050 示例日程")
    parser.add_argument("--profile", required=True, help="用户画像和偏好")
    parser.add_argument("--date", default="2026-04-25", help="日期，例如 2026-04-25")
    parser.add_argument("--time-window", help="在场时段，例如 13:00-18:00")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    requested_window = parse_time_range(args.time_window) if args.time_window else None
    if args.time_window and not requested_window:
        raise SystemExit("FAIL: 无法解析 --time-window，请使用 13:00-18:00 这样的格式")
    plan = build_plan(args.profile, args.date, requested_window=requested_window)
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
