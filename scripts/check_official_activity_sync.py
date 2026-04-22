#!/usr/bin/env python3
"""Check packaged activity IDs against the current 2050 official activity API."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_INDEX = ROOT / "references" / "activity_index.min.json"
OFFICIAL_API = "https://2050.org/api/containerActivity/getPage"


def official_activity_ids(year: int) -> set[str]:
    query = urllib.parse.urlencode({"current": 1, "size": 500, "year": year})
    request = urllib.request.Request(
        f"{OFFICIAL_API}?{query}",
        data=b"",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    records = (payload.get("data") or {}).get("records") or []
    return {str(record.get("id")) for record in records if record.get("id")}


def local_activity_ids() -> set[str]:
    activities = json.loads(ACTIVITY_INDEX.read_text(encoding="utf-8"))
    return {str(activity.get("activity_id")) for activity in activities if activity.get("activity_id")}


def main() -> int:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    official = official_activity_ids(year)
    local = local_activity_ids()
    only_official = sorted(official - local)
    only_local = sorted(local - official)
    result = {
        "year": year,
        "official_count": len(official),
        "local_count": len(local),
        "in_sync": not only_official and not only_local,
        "only_official": only_official,
        "only_local": only_local,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["in_sync"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
