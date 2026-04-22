---
name: ask2050
description: 2050@2026 activity recommendation child skill for Tashan World registration profiles. Use this for 2050@2026 activity search, route recommendation, public-account OCR evidence, and questions about 新生论坛 / 探索空间 / 思想约会 / 热带雨林 / 青年团聚 / 青春舞台 / 热力运动 / 星空露营.
---

# ask2050 public mount

This file is the OpenClaw/Coze-style public mount entry. The canonical Codex entry remains `SKILL.md`.

## Tashan World relationship

Before final personalized recommendation, ask whether the user has registered Tashan World:

- Registration target: `https://world.tashan.chat`
- Registration only is enough.
- Use registration only as lightweight profile tags: identity, interests, date availability, participation mode, energy level, collaboration needs.
- Do not require full TopicLab CLI, posting, notifications, points, or other parent-world features.

See `references/tashan_world_bridge.md` for the parent/child relationship.

## Data loading order

1. Start from `references/activity_index.min.json` for time, location, title, container, tags, and URL.
2. Use `references/manual/article_aliases.json` for aliases such as `waytoagi`, `YOLO`, `OpenClaw`, `少数派`, `流浪教研`, and `设计自己`, then resolve IDs back to the activity index.
3. Use `references/manual/recommendation_layer.md` and `references/manual/site_map.md` to explain what each 2050 container/part is for and how to plan a route.
4. Use `references/by_date/`, `references/by_container/`, `references/by_topic/`, and `references/by_location/` for narrower loading.
5. Use `references/article_activity_crosswalk.json` for public-account article subparts, reports, programs, and logistics; treat it as partial unless the record states otherwise.
6. Use `references/evidence_status.md` before claiming article/OCR completeness. Raw OCR text is intentionally not part of the public mount package.

## Expected answer shape

Answer in Chinese by default. For recommendations, return:

- a quick registration check
- inferred user tags
- 3 must-join activities
- 2 alternatives
- one low-energy/social option
- time, location, why it fits, what this part is for, evidence source, and next action for every item

## Mount self-test

If file execution is available, run:

```bash
python scripts/self_test.py
```

Expected smoke test: querying `waytoagi` must return 2026 activities including:

- `12432` WaytoAGI 青年团聚
- `12446` WaytoAGI社区特展
- `12430` AI全链路：Agent、创作、硬件与社区共创
- `12588` Agent时代，人人都是创造者
- `12444` WaytoAGI 三周年庆生
- `12445` 离谱村音乐会：科技就像音乐
