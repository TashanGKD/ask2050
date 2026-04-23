# ask2050 核心提取模型

这个文件定义推荐前应提取的信息。它不是面向最终用户展示的清单，而是让模型在检索和分层加载时知道该看什么、怎么比。

## 活动层字段

每个活动至少整理成下面几类信息：

- `activity_id`: 活动唯一 ID，用于回查时间、地点和来源。
- `primary_topics`: 活动真正的核心主题。优先看标题、摘要和板块，不机械照搬原始 topic。
- `secondary_topics`: 可辅助匹配的旁支兴趣。
- `experience_modes`: 用户能直观理解的参与体验，如听报告、深聊、看展体验、动手工作坊、找同伴、放松恢复、夜间继续聊、户外身体活动、生活补给。
- `participation_style`: 推荐和排序用的动作标签，如 listen、browse、demo、hands-on、deep-talk、community-meetup、relax、camping、sports、logistics。
- `recommended_for`: 适合的人群或使用场景，如第一次来 2050、AI 应用开发者、教育工作者、硬件/机器人方向、创作者、想找同伴的人、低能量用户。
- `intensity`: low、medium、high。用于避免连续安排高强度内容。
- `social_density`: solo-friendly、small-group、crowd、deep-talk。用于判断用户是否需要开口、是否适合独自参加。
- `planning_role`: 活动在路线里的角色，如 main-anchor、buffer、social-anchor、hands-on-anchor、evening-anchor、logistics、wildcard。
- `time_pattern`: morning、daytime、evening、night、all-day。用于快速拼路线。
- `venue_context`: indoor、outdoor、camping、food、unknown。用于地图和体力成本判断。
- `route_note`: 给推荐时可直接改写的一句话，说明这个 part 是干嘛的。
- `source_level`: schedule、article-linked、manual-curated。用于说明证据层级。
- `search_terms`: 把别名、社区名、中文体验词和活动 ID 汇总成检索入口。

## 文章层字段

公众号文章、OCR 结果和人工补录整理成下面几类信息：

- `source_id`: 文章或结果文件 ID。
- `article_url`: 原文链接。
- `source_role`: schedule-update、program-guide、community-call、logistics-guide、map-guide、background、mixed。
- `linked_activity_ids`: 能回到官方活动主表的活动 ID。
- `communities_or_aliases`: 社群、伙伴、项目、别名。
- `extracted_topics`: 文章核心主题。
- `experience_modes`: 文章指向的参与体验。
- `route_use`: 文章在推荐中的用途，如补充项目语境、解释某个板块、补充后勤信息、提示路线风险。
- `confidence`: high、medium、low。低置信度只做线索，不做确定安排。

## 结构化日程补充层字段

从 `日程JSON(1).xlsx` 这类结构化工作簿抽取的记录，不进入官网主活动表，但要保留推荐和解释有用的列：

- `schedule_status`、`hidden`、`done`: 判断该条是否可作为推荐线索；隐藏或未搞定的项不能直接进入主推荐。
- `activity_detail_ids`、`legacy_detail_ids`、`hive_intent_id`: 用于后续和官网、蜂巢意向或历史明细交叉核对。
- `period_label`、`date_label`、`date_tags`、`time_text`: 保留原始时间表达；明确日期可用于过滤，多日项只能作为宽窗口线索。
- `board_title`、`container`、`venue_type`、`location_raw`: 用于判断板块、形式、换场成本和地点粒度。
- `hosts`、`segments`、`description`: 用于回答具体 part 是干嘛的、谁召集、适合什么人。

## 使用原则

先用活动事实层确认时间、地点和活动名，再用 facet 层判断适不适合用户。文章层只能增强语境和别名检索，不能覆盖官方活动事实。遇到晚近变化，优先建议重新安装 skill 获取最新整理版本。

地点和子日程必须做三源交叉：

- `activities.csv` / 官网 API 的活动 ID、标题、日期、时间是主键，不用公众号文章自己造活动。
- 官网 `location` 如果只有总场馆，继续检查官网 `content_text` 里的“地点 / Venue / Location / 论坛地点”。
- 公众号正文、图片 OCR 和人工看图只在能匹配到同一活动 ID、同一标题或同一时间窗时回填楼层、厅、展位和报告 part。
- 三源都只到总场馆时，保持“官方未细分厅/展位”的事实边界，不编厅号；但这类项必须进入复核清单，不能在路线规划里当作精确地点。
