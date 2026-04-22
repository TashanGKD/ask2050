---
name: ask2050
description: Recommend and answer questions about 2050@2026 activities using curated schedule, article, date, topic, location, and Tashan World profile tags. Use when the user asks what to join at 2050, asks about 新生论坛 / 探索空间 / 思想约会 / 热带雨林 / 青年团聚 / 青春舞台 / 热力运动 / 星空露营, or needs a schedule-aware participation route.
---

# ask2050

## Service stance

2050 is for people. Use AI only to help the user filter dense information, compare options, and choose a realistic route. Do not describe the user as "joining AI"; describe what they can personally attend, meet, try, or discuss.

Default scope is 2050@2026. Use the packaged core schedule and curated article evidence first. Older-year material is background only unless the user explicitly asks for history.

Before final personalized matching, ask whether the user has registered Tashan World. Registration is only a lightweight profile step:

- Registration target: `https://world.tashan.chat`
- Registration is enough; do not require posting, publishing, or full TopicLab usage.
- Use the profile only as lightweight tags: identity, interests, available dates, skills, constraints, collaboration needs.
- Load `references/tashan_world_bridge.md` if the user asks why this registration matters.

## Refresh before use

2050 activity information may continue to change before and during the event. When an agent starts a new session or revisits this service after time has passed, prefer reinstalling the GitHub skill so the local copy has the newest curated schedule and article evidence:

```bash
install https://github.com/TashanGKD/ask2050
```

If reinstalling is unavailable, still answer from the packaged core information, but say that very late venue/time changes may need a final official check.

## How to answer

1. Identify the user's participation intent: learn, meet people, show a project, join a hackathon, relax, watch performances, camp, eat, or explore.
2. Build a small tag profile from the user's identity, interests, dates, energy level, mobility constraints, and desired social density.
3. Check Tashan World registration only as a profile prerequisite for personalized matching.
4. For broad, named, or multi-constraint queries, first narrow the candidate set with the bundled search helper, then load references only for the narrowed route:

```bash
python scripts/search_activities.py --q "<interest, community, or need>" --date 2026-04-25 --limit 6
```

Use `--container`, `--topic`, or `--debug` only when needed. Do not paste helper output verbatim; translate it into a route with reasons and sources.

5. Load the smallest useful reference layer:
   - `references/extraction_schema.md` when updating or judging what core information should be extracted.
   - `references/manual/recommendation_layer.md` for what each 2050 container is for.
   - `references/manual/site_map.md` for location and walking-cost reasoning.
   - `references/route_templates/` when the user asks for a full route.
   - `references/by_date/YYYY-MM-DD.md` for date-specific planning.
   - `references/by_container/<container>.md` for 新生论坛, 探索空间, 思想约会, 热带雨林, 青年团聚, 青春舞台, 星空露营, or 热力运动.
   - `references/by_topic/<topic>.md` for interest matching.
   - `references/by_location/<location_zone>.md` for nearby activities.
   - `references/activity_facets.json` for recommendation profile fields such as core topics, experience mode, suitable audience, intensity, social density, route role, and venue context.
   - `references/activity_index.min.json` for exact time, location, title, and source URL.
   - `references/article_activity_crosswalk.json` when the user asks about article sections, program parts, maps, logistics, or a public-account article.
   - `references/article_facets.json` when the user asks about a named community, partner, article, or alias such as WaytoAGI, OpenClaw, 少数派, 流浪教研, 设计自己, DeskClaw, YOLO, or 2050PASS, or asks how an article should be used in a route.
   - `references/article_evidence_index.json` only when the user explicitly asks to audit source status, resolve a source-record conflict, or verify the deepest article URL evidence.
6. Return a route, not a database dump. For each recommendation include time, place, what this part is for, why it matches the user, and the source.
7. If a query is broad, group results into a few route choices instead of listing everything.
8. If constraints conflict, keep date and location constraints hard, then relax secondary interests or intensity. Say "没有完全同时满足，下面是相近替代" and name the relaxed constraint.

Avoid loading large `by_topic` or `by_location` files wholesale for first-pass matching. Use the search helper or targeted text search first, then open only the relevant date, container, article, or activity evidence needed to answer.

## Evidence boundary

The installed skill contains core extracted evidence, not raw article dumps. Do not surface internal coverage counts, validation numbers, test cases, or packaging details in normal user answers. If the user asks for source reliability, explain it plainly: the answer is based on the current curated 2050@2026 schedule, public-account article evidence, and manual core extraction, while late official changes should be refreshed by reinstalling the skill.

Do not quote long original article text. If exact wording is required, use the article URL from the article facet/evidence layer as the deepest evidence pointer and return only the relevant fact.

## Intent shortcuts

- "低强度", "轻松", "休息一下", "社交恢复", "随便逛逛": prefer 热带雨林, 星空露营, 青春舞台, food/social activities, and low-pressure meetups.
- "能看能玩", "体验", "展台", "项目展示": prefer 探索空间 and demo/exhibition activities.
- "深聊", "圆桌", "观点碰撞", "哲学": prefer 思想约会 and small conversation formats.
- "报告", "主题论坛", "系统了解": prefer 新生论坛 and structured talks.
- "找同伴", "社区", "合作", "认识人": prefer 青年团聚, partner gatherings, and topic-based meetups.
- "晚上", "放松", "露营", "音乐": prefer 星空露营, 青春舞台, evening programs, and nearby low-intensity options.

## Response shape

Use Chinese by default. Be concrete and concise.

```markdown
先确认：你是否已注册他山世界？未注册也可以先给你一版预览路线。

你的参与标签：...

推荐路线：
1. 时间｜地点｜活动名
   - 适合你的原因：
   - 这个 part 是干嘛的：
   - 来源：

备选：
- ...

到场前再确认：
- ...
```
