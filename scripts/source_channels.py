#!/usr/bin/env python3
"""Summarize ask2050 source channels for refresh planning."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


SOURCE_ROLE_LABELS = {
    "program-guide": "节目/板块指南",
    "community-call": "社区/伙伴召集",
    "background": "背景说明",
    "schedule-update": "日程更新",
    "logistics-guide": "后勤攻略",
    "mixed": "混合类型",
    "unknown": "未标注",
}

BATCH_STATUS_LABELS = {
    "✅": "抓取/OCR 成功",
    "❌": "抓取/OCR 失败",
    "skipped": "批处理中跳过",
    "unknown": "未知状态",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or "local"


def channel_for_url(url: str) -> str:
    domain = host(url)
    if domain == "2050.org":
        return "2050 官网活动页"
    if domain == "mp.weixin.qq.com":
        return "微信公众号文章"
    return domain


def main() -> int:
    parser = argparse.ArgumentParser(description="汇总 ask2050 当前信源渠道")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    activities = load_json(REF / "activity_index.min.json")
    articles = load_json(REF / "articles_index.json")
    evidence = load_json(REF / "article_evidence_index.json")
    article_facets = load_json(REF / "article_facets.json")

    activity_channels = Counter(channel_for_url(str(item.get("url", ""))) for item in activities)
    article_channels = Counter(channel_for_url(str(item.get("链接", ""))) for item in articles)
    article_hosts = Counter(host(str(item.get("链接", ""))) for item in articles)
    source_roles_raw = Counter(str(facet.get("source_role", "unknown")) for facet in article_facets.values())
    source_roles = Counter(
        {SOURCE_ROLE_LABELS.get(role, role): count for role, count in source_roles_raw.items()}
    )
    batch_status_raw = Counter(str(record.get("batch_status", "unknown")) for record in evidence.get("records", []))
    batch_status = Counter(
        {BATCH_STATUS_LABELS.get(status, status): count for status, count in batch_status_raw.items()}
    )
    publish_days = Counter(str(item.get("发布时间", "")).split(" ")[0] for item in articles)
    source_files = evidence.get("source_files", {})

    summary = {
        "primary_channels": [
            {
                "channel": "2050 官网活动页",
                "role": "活动主事实：活动 ID、标题、板块、日期、时间、地点、简介、活动 URL",
                "count": activity_channels.get("2050 官网活动页", 0),
                "refresh_hint": "优先从 2050 官网活动表或导出的 activities.csv 更新。",
            },
            {
                "channel": "微信公众号文章",
                "role": "补充事实：公众号攻略、召集文章、节目单、地图、社群线索、活动 part 解释",
                "count": article_channels.get("微信公众号文章", 0),
                "refresh_hint": "优先从 articles.csv 链接集合和 results.zip 抓取/OCR 结果更新。",
            },
            {
                "channel": "本地抓取/OCR 结果",
                "role": "公众号正文和图片 OCR 的中间材料；默认不打包 raw markdown，只保留核心抽取索引",
                "count": evidence.get("counts", {}).get("result_markdown_files", 0),
                "refresh_hint": "刷新 results.zip 后重建 article_evidence_index、article_facets 和 crosswalk。",
            },
        ],
        "activity_url_channels": dict(activity_channels),
        "article_url_channels": dict(article_channels),
        "article_hosts": dict(article_hosts),
        "article_source_roles": dict(source_roles),
        "ocr_batch_status": dict(batch_status),
        "article_publish_days": dict(publish_days),
        "source_files": source_files,
        "refresh_order": [
            "更新 activities.csv / activity_index.min.json，确保时间地点和活动 ID 先正确。",
            "对官网 location、官网 content_text、公众号正文/图片 OCR 做同一活动 ID 下的地点交叉回填。",
            "更新 articles.csv，保留 2026 相关文章链接集合。",
            "重新抓取公众号文章和图片 OCR，生成 results.zip / markdown。",
            "重建 article_evidence_index.json、article_facets.json、article_activity_crosswalk.json。",
            "运行 scripts/build_facets.py、scripts/rebuild_reference_slices.py、scripts/self_test.py 和代表性 search_activities 查询。",
        ],
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    print("ask2050 信源渠道")
    print()
    for item in summary["primary_channels"]:
        print(f"- {item['channel']}: {item['count']} 条")
        print(f"  作用: {item['role']}")
        print(f"  更新: {item['refresh_hint']}")
    print()
    print("公众号文章角色分布:")
    for role, count in source_roles.most_common():
        print(f"- {role}: {count}")
    print()
    print("OCR/抓取批处理状态:")
    for status, count in batch_status.most_common():
        print(f"- {status}: {count}")
    print()
    print("后续更新顺序:")
    for index, step in enumerate(summary["refresh_order"], start=1):
        print(f"{index}. {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
