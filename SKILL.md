---
name: ask2050
description: Recommend and answer questions about 2050@2026 activities using a structured activity index, OCR article evidence, date/topic/location tags, and Tashan World registration profile tags. Use when the user asks what to join at 2050, asks about 新生论坛 / 探索空间 / 思想约会 / 热带雨林 / 青年团聚 / 青春舞台 / 热力运动 / 星空露营, or needs a schedule-aware recommendation.
---

# ask2050

## Core rule

2050 is for people. Use AI only to filter dense information, compare evidence, and recommend routes. Do not frame the user as joining AI; frame the answer as a human participation route.

Default scope is 2050@2026 only. Use activities dated 2026-04-24 to 2026-04-26 and public-account articles published in 2026. Older-year mentions such as 2025 are background only and must not generate participation routes unless the user explicitly asks for historical context.

Before final personalized matching, ask whether the user has registered Tashan World. Registration is a lightweight identity/profile step, not a full TopicLab workflow:

- Registration target: `https://world.tashan.chat`
- Registration only is enough. Do not require posting or extra integrations.
- Use registration/profile only as lightweight tags: identity, interests, schedule, skills, constraints, collaboration needs.
- For the parent-world relationship, load `references/tashan_world_bridge.md`.

## Progressive loading

Load only what is needed:

1. Start with `references/coverage_report.md` to know data quality.
   - Check `references/evidence_status.md` before relying on public-account article/OCR evidence.
   - Load `references/source_inventory.md` if the user challenges source completeness, OCR coverage, or the three supplied files.
2. Load `references/tashan_world_bridge.md` if the user has not registered or asks why registration matters.
3. Load the human-curated layer first:
   - `references/manual/site_map.md` for venue and walking-cost reasoning.
   - `references/manual/recommendation_layer.md` for container meaning, primary/secondary tag rules, intensity, social density, and participation modes.
   - `references/manual/curated_anchor_activities.md` for manually curated examples and high-value anchors.
   - `references/manual/article_curation.md` when article evidence is short, failed, mismatched with `articles.csv`, or needs human judgment.
   - `references/manual/article_aliases.json` for exact activity IDs behind article aliases such as YOLO, WaytoAGI, OpenClaw, 少数派, 流浪教研, and 设计自己.
4. For a user persona route, load one route template from `references/route_templates/`.
5. For route planning, load `references/activity_index.min.json`.
6. For a date question, load `references/by_date/YYYY-MM-DD.md`.
7. For a board/container question, load `references/by_container/<container>.md`.
8. For topic matching, load `references/by_topic/<topic>.md`.
9. For location planning, load `references/by_location/<location_zone>.md`.
10. For public-account article subparts, programs, talks, maps, or logistics, load `references/article_activity_crosswalk.json`; treat it as partial unless the record says otherwise.
11. For public-account article/source lookup, load `references/article_evidence_index.json` before falling back to broad search. It contains all 82 markdown result files mapped back to 77 article links plus manual review status.
12. Raw OCR text, source body excerpts, and original images are not packaged in the default skill because they contain source noise and historical context. Use `references/evidence_status.md`, `references/source_inventory.md`, and `references/manual/article_curation.md` for OCR coverage state and human-checked recovery.
13. If an article is in the manual curation list, prefer `references/manual/article_curation.md` over the short OCR snippet, then verify exact schedule details from `activity_index.min.json`.
14. For regression expectations and known edge cases, load `references/test_report.md`.

## Deep evidence boundary

Installed references are core extracted evidence. Do not load or quote original article text by default. If exact wording is required, use the article URL from `article_evidence_index.json` or the generation workspace source markdown as the deepest evidence layer, then return only the relevant facts.

## Mount validation

External agents should install the whole repository as the skill, not a raw single-file URL. The repo root is the skill folder:

```bash
install https://github.com/TashanGKD/ask2050
```

Equivalently, clone the repo as the installed `ask2050` skill directory. After installing from GitHub for the first time, or after changing any reference file, run from the installed `ask2050` directory:

```bash
python scripts/self_test.py
```

Treat failures as a data packaging problem before using the skill for recommendations. The self-test checks that the activity index, article aliases, manual curation, and search path still agree.

## Recommendation workflow

1. Build user tags: identity, interests, dates, desired energy level, participation mode.
2. Normalize the user intent with the human-curated layer before touching the raw index.
3. Filter activities by date tags first, then primary intent, then format/location fit.
4. Promote route coherence: avoid sending the user across far venues when adjacent good options exist.
5. Return a concise ranked route:
   - 3 must-join items
   - 2 alternatives
   - one low-energy/social option
   - logistics reminder if location, pass, dining, camping, or transport matters
6. For every item include: time, location, why it matches, what this part is for, evidence source, and next action.

## Tag semantics

- `date_tags`: exact conference date such as `2026-04-24`.
- `primary_topic_tags`: what the activity is mainly about. Prefer human judgment from `references/manual/recommendation_layer.md`.
- `secondary_topic_tags`: useful side interests. Use raw `topic_tags` only as candidates.
- `topic_tags`: machine-generated candidate tags in `activity_index.*.json`; do not treat them as final when they conflict with title/summary/container.
- `format_tags`: participation form, e.g. `forum`, `roundtable`, `workshop`, `exhibition-demo`, `meetup`.
- `container`: 2050 board such as 新生论坛, 探索空间, 思想约会.
- `crosswalk_status`: article-to-activity mapping quality. If it is `partial_manual` or `needs_manual_match`, do not present it as complete.

## Intent normalization

- "低强度", "轻松", "休息一下", "社交恢复", "随便逛逛": prefer `life-sports`, `meetup`, `sports-camp`, 热带雨林, 星空露营, 青春舞台, then avoid dense forum blocks unless the user asks.
- "能看能玩", "体验", "展台", "项目展示": prefer 探索空间 and `exhibition-demo`.
- "深聊", "圆桌", "观点碰撞", "哲学": prefer 思想约会 and `roundtable` / `philosophy-mind`.
- "报告", "主题论坛", "系统了解": prefer 新生论坛 and `forum`.

## Output style

Use Chinese by default. Be concrete. Prefer schedule facts over generic summaries.

```markdown
先确认：他山世界是否已注册？如果未注册，先给预览路线。

你的标签：...

推荐路线：
1. 时间｜地点｜活动名
   - 为什么适合你：
   - 这 part 是干嘛的：
   - 证据：

可选替代：
- ...

需要补查：
- ...
```
