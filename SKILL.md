---
name: ask2050
description: Recommend and answer questions about 2050@2026 activities using a structured activity index, OCR article evidence, date/topic/location tags, and Tashan World registration profile tags. Use when the user asks what to join at 2050, asks about 新生论坛 / 探索空间 / 思想约会 / 热带雨林 / 青年团聚 / 青春舞台 / 热力运动 / 星空露营, or needs a schedule-aware recommendation.
---

# ask2050

## Core rule

2050 is for people. Use AI only to filter dense information, compare evidence, and recommend routes. Do not frame the user as joining AI; frame the answer as a human participation route.

Before final personalized matching, ask whether the user has registered Tashan World:

- Registration target: `https://world.tashan.chat`
- Registration only is enough. Do not require posting or extra integrations.
- Use registration/profile only as lightweight tags: identity, interests, schedule, skills, constraints, collaboration needs.

## Progressive loading

Load only what is needed:

1. Start with `references/coverage_report.md` to know data quality.
   - Also check `references/article_crosswalk_status.md` before claiming article-level completeness.
2. Load the human-curated layer first:
   - `references/manual/site_map.md` for venue and walking-cost reasoning.
   - `references/manual/recommendation_layer.md` for container meaning, primary/secondary tag rules, intensity, social density, and participation modes.
   - `references/manual/curated_anchor_activities.md` for manually curated examples and high-value anchors.
3. For a user persona route, load one route template from `references/route_templates/`.
4. For route planning, load `references/activity_index.min.json`.
5. For a date question, load `references/by_date/YYYY-MM-DD.md`.
6. For a board/container question, load `references/by_container/<container>.md`.
7. For topic matching, load `references/by_topic/<topic>.md`.
8. For location planning, load `references/by_location/<location_zone>.md`.
9. For evidence from public-account OCR, load `references/article_ocr_index.json`, then the specific `references/article_ocr/*.md` file.

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
