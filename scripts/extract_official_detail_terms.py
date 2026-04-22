#!/usr/bin/env python3
"""Extract compact official-detail search terms from 2050 activities.csv."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"

STOP_WORDS = {
    "活动",
    "活动内容",
    "活动背景",
    "活动标题",
    "活动介绍",
    "活动时间",
    "活动地点",
    "召集人",
    "介绍",
    "简介",
    "姓名",
    "时间",
    "地点",
    "标题",
    "环节",
    "分享",
    "主题",
    "更多详情",
    "Event",
    "Title",
    "Time",
    "Location",
    "Venue",
    "Organizer",
}

KEEP_PATTERNS = [
    re.compile(r"[A-Z][A-Za-z0-9+-]{2,}"),
    re.compile(r".*(AI|Agent|Open|Khub|Datawhale|WaytoAGI|OPC|FSHD|PASS).*", re.I),
]
NOISE_PREFIXES = (
    "为了",
    "我们",
    "一起",
    "欢迎",
    "通过",
    "举办",
    "以及",
    "还有",
    "感受",
    "轻松",
    "这是",
    "也是",
    "可以",
    "也可以",
    "我以",
    "我是",
    "辗转",
    "分钟",
)


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = value.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", value)


def candidate_terms(text: str) -> list[str]:
    raw_parts = re.split(r"[\n\r|｜。；;：:，,、（）()\[\]【】《》<>“”\"'！？!?•·\s]+", clean_text(text))
    terms = []
    for raw in raw_parts:
        term = raw.strip(" -_—")
        if not term or term in STOP_WORDS:
            continue
        if re.fullmatch(r"[\d:./-]+", term):
            continue
        if re.search(r"20(?:1\d|2[0-5])", term):
            continue
        if term.startswith(NOISE_PREFIXES) and not any(pattern.match(term) for pattern in KEEP_PATTERNS):
            continue
        keep = 4 <= len(term) <= 24 or any(pattern.match(term) for pattern in KEEP_PATTERNS)
        if not keep:
            continue
        if term.lower() in {"event", "title", "time", "location", "venue", "organizer"}:
            continue
        terms.append(term)
    return list(dict.fromkeys(terms))


def score_term(term: str) -> tuple[int, int]:
    score = 0
    if any(pattern.match(term) for pattern in KEEP_PATTERNS):
        score += 8
    if any(token in term for token in ["AI", "Agent", "开源", "社区", "教育", "医疗", "科学", "硬件", "艺术", "哲学", "罕见病"]):
        score += 5
    if re.search(r"论坛|圆桌|工作坊|黑客松|项目|产品|平台|系统|工具|课程|研究|实验|实践", term):
        score += 3
    return score, len(term)


def main() -> int:
    parser = argparse.ArgumentParser(description="从官网 activities.csv 正文抽取紧凑检索词")
    parser.add_argument("activities_csv", help="2050 官网导出的 activities.csv")
    parser.add_argument(
        "--output",
        default=str(REF / "official_detail_terms.json"),
        help="输出 JSON 路径",
    )
    parser.add_argument("--limit", type=int, default=8, help="每个活动最多保留多少正文词")
    args = parser.parse_args()

    records = {}
    with open(args.activities_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            activity_id = str(row.get("activity_id", "")).strip()
            if not activity_id:
                continue
            text = " ".join(
                [
                    row.get("content_text", ""),
                    row.get("convener_details", ""),
                ]
            )
            terms = candidate_terms(text)
            terms.sort(key=lambda term: score_term(term), reverse=True)
            records[activity_id] = {
                "detail_terms": terms[: args.limit],
                "content_text_chars": len(row.get("content_text", "") or ""),
            }

    output = {
        "schema_version": "0.1",
        "source": "2050 activities.csv content_text + convener_details",
        "activities": records,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote official detail terms for {len(records)} activities to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
