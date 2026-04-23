#!/usr/bin/env python3
"""Smoke test the ask2050 OpenClaw lightweight session path without printing secrets."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.request


BASE_URL = "https://world.tashan.chat"
BOOTSTRAP_URL = f"{BASE_URL}/api/v1/auth/openclaw-guest"
REQUIRED_BOOTSTRAP_FIELDS = [
    "bind_key",
    "skill_path",
    "bootstrap_path",
    "is_guest",
    "claim_register_path",
    "claim_login_path",
]


def post_json(url: str) -> dict:
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def summarize_presence(payload: dict) -> dict:
    summary: dict[str, bool | str] = {}
    for field in REQUIRED_BOOTSTRAP_FIELDS:
        value = payload.get(field)
        if field == "is_guest":
            summary[field] = bool(value)
        elif value:
            summary[field] = f"present(len={len(str(value))})"
        else:
            summary[field] = False
    return summary


def topiclab_executable() -> str | None:
    return shutil.which("topiclab.cmd") or shutil.which("topiclab")


def run_topiclab(executable: str, args: list[str]) -> tuple[int, str, dict | None]:
    completed = subprocess.run(
        [executable, *args],
        check=False,
        text=True,
        capture_output=True,
        encoding="utf-8",
        cwd=tempfile.gettempdir(),
    )
    text = (completed.stdout or "") + (completed.stderr or "")
    parsed = None
    try:
        parsed = json.loads(completed.stdout)
    except Exception:
        parsed = None
    return completed.returncode, text, parsed


def answer_preview(events: list[dict], limit: int = 500) -> str:
    chunks = []
    for event in events:
        content = event.get("content") if isinstance(event, dict) else None
        if isinstance(content, dict) and content.get("answer"):
            chunks.append(str(content["answer"]))
    return "".join(chunks)[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a real OpenClaw guest bootstrap and topiclab session ensure smoke test."
    )
    parser.add_argument(
        "--agent-call",
        action="store_true",
        help="Also invoke topiclab help ask once to verify the persisted ask-agent channel.",
    )
    args = parser.parse_args()

    executable = topiclab_executable()
    if not executable:
        print(json.dumps({"ok": False, "error": "topiclab CLI not found"}, ensure_ascii=False, indent=2))
        return 2

    bootstrap = post_json(BOOTSTRAP_URL)
    bind_key = str(bootstrap.get("bind_key") or "")
    if not bind_key:
        print(
            json.dumps(
                {"ok": False, "bootstrap": summarize_presence(bootstrap), "error": "missing bind_key"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    ensure_code, ensure_text, ensure_json = run_topiclab(
        executable,
        ["session", "ensure", "--base-url", BASE_URL, "--bind-key", bind_key, "--json"]
    )
    result: dict[str, object] = {
        "ok": ensure_code == 0 and bool(ensure_json and ensure_json.get("ok")),
        "bootstrap": summarize_presence(bootstrap),
        "session_ensure_exit": ensure_code,
        "session_ensure_json": bool(ensure_json),
        "session_ensure_keys": sorted(ensure_json.keys()) if isinstance(ensure_json, dict) else [],
    }
    if ensure_code != 0:
        result["session_ensure_error_preview"] = ensure_text.replace(bind_key, "<redacted-bind-key>")[:600]

    if args.agent_call and result["ok"]:
        ask_code, ask_text, ask_json = run_topiclab(
            executable,
            [
                "help",
                "ask",
                "我刚接入 ask2050，想根据个人标签获得 2050 活动推荐。请只简短说明你需要哪些标签。",
                "--json",
            ]
        )
        result["agent_call"] = {
            "exit": ask_code,
            "json": bool(ask_json),
            "help_source": ask_json.get("help_source") if isinstance(ask_json, dict) else None,
            "mode": ask_json.get("mode") if isinstance(ask_json, dict) else None,
            "website_skill_version": ask_json.get("website_skill_version") if isinstance(ask_json, dict) else None,
            "answer_preview": answer_preview(ask_json.get("events", [])) if isinstance(ask_json, dict) else ask_text[:500],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
