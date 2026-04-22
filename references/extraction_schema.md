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

## 使用原则

先用活动事实层确认时间、地点和活动名，再用 facet 层判断适不适合用户。文章层只能增强语境和别名检索，不能覆盖官方活动事实。遇到晚近变化，优先建议重新安装 skill 获取最新整理版本。
