# 公众号文章人工策展

## 使用口径

本文件整理 OCR 不足、标题错位或只适合人工判断的文章线索。它不是全文 OCR，而是推荐时的人工策展层。

使用规则:

- 先按本文找到候选 `activity_id`。
- 再从 `activity_index.min.json` 读取准确时间、地点、简介。
- 不引用短文本或错位文章的长段正文。
- `confidence=high` 表示标题/摘要与活动强匹配；`medium` 表示主题可用但正文不足；`low` 只作探索线索。

## 条目

### 009.md 少数派的共创时代

- 主匹配: `12358` 少数派的共创时代
- 相关: `12540` 少数派的造物者们
- 适合: 独立开发者、产品创造者、社区共创、从想法到落地的人。
- 标签: `community-co-creation`, `indie-maker`, `product-practice`, `ai-creation`
- 置信度: high for `12358`, medium for `12540`

### 023.md 未来城邦

- 主匹配: `12363` 未来城邦：重新定义诗和远方
- 适合: 科幻、未来城市、社会规则设计、角色扮演式共创。
- 标签: `future-city`, `world-building`, `co-creation-game`, `science-fiction`
- 置信度: high

### 027.md 流浪教研 / 课创黑客松

- 主匹配: `12267` 课创黑客松
- 相关: `12266` 流浪课程展; `12268` 青少年导览; `12277` 好奇来信; `12278` 照顾内在小孩
- 适合: 教师、教育产品、课程设计、青少年教育、把现场体验转成课程原型。
- 标签: `education`, `teacher-community`, `course-design`, `hackathon`
- 置信度: high for `12267`, medium for related activities

### 038.md 什么是 2050

- 主匹配: 无单一活动。
- 用途: 2050 背景解释和新用户 onboarding，不用于具体日程推荐。
- 标签: `2050-intro`, `orientation`, `human-reunion`, `non-conference`
- 置信度: high for background only

### 040.md 少数派线下活动邀请

- 主匹配: `12540` 少数派的造物者们; `12358` 少数派的共创时代
- 适合: 少数派读者、数字生活/效率工具爱好者、创作者交流。
- 标签: `sspai`, `maker-community`, `product-practice`, `community-co-creation`
- 置信度: medium

### 041.md AI 芯片 / YOLO 冲突条目

- 标题级匹配: `12220` 探索AI对芯片行业的影响，寻找志同道合的跨界伙伴
- 正文级匹配: `12224` 如果你热爱旅行和文化探索，一定来找我们呀; `12251` 舌尖上的团聚; `12276` 百城味道
- 规则: 用户问 AI 芯片时用 `12220`；用户问 YOLO/旅行/家乡美食时用 `12224`, `12251`, `12276`。
- 禁止: 不要把 AI 芯片和 YOLO 美食内容合成同一活动。
- 置信度: high for conflict detection

### 050.md AI 工具之外的创造

- 主匹配: `12540` 少数派的造物者们
- 相关: `12358` 少数派的共创时代; `12588` Agent时代，人人都是创造者
- 适合: 想从“用 AI 工具”走向做产品、作品、社区共创的人。
- 标签: `maker`, `creative-practice`, `ai-creation`, `community`
- 置信度: medium

### 061.md 少年有请 / AI 导演 / 火星策展

- 主匹配: `12598` 未来导演请就位——少年AI电影展映＆沙龙
- 相关: `12700` 光影回响——10后导演的 AI 电影展
- 弱相关: `12326`, `12312`, `12338`, `12339`
- 适合: 青少年、家长、AI 影像创作者、科幻/太空叙事爱好者。
- 标签: `youth-ai-film`, `children-creation`, `science-fiction`, `space-imagination`
- 置信度: high for `12598`, medium for `12700`, low for space-related items

### 063.md WaytoAGI 集合

- 主匹配: `12432` WaytoAGI 青年团聚; `12430` AI全链路; `12446` WaytoAGI社区特展
- 相关: `12588` Agent时代; `12444` WaytoAGI 三周年庆生; `12445` 离谱村音乐会
- 适合: WaytoAGI 社区成员、Agent/工具链实践者、AI 创作者。
- 标签: `waytoagi`, `agent`, `ai-community`, `openclaw`, `community-meetup`
- 置信度: medium to high

### 065.md 壹木自然读书会

- 主匹配: `12455` 和壹木一起刷山
- 适合: 自然观察、植物、博物、户外轻社交、读书会成员。
- 标签: `nature`, `plant`, `reading-club`, `outdoor-social`
- 置信度: high

### 066.md 设计自己 / Tianmeis

- 主匹配候选: `12424` 成为一人公司
- 相关候选: `12420` 金钱心理和投射; `12633` 创造你的数字分身与专属角色
- 规则: 只能作为“自我设计/一人公司/金钱心理/数字身份”的候选线索，需要结合用户问题再确认。
- 标签: `self-design`, `one-person-company`, `future-self`, `money-psychology`, `digital-identity`
- 置信度: medium for `12424/12420`, low for `12633`

### 070.md 2050 总入口

- 主匹配: 无单一活动。
- 用途: 2050 总入口、日期地点背景、口号说明，不用于具体活动推荐。
- 标签: `2050-intro`, `date-location`, `general-announcement`
- 置信度: high for date/location slogan only

### 015.md / 045.md 杭州场景妙妙屋

- 主匹配: `12242` 杭州场景妙妙屋
- 文章线索: 4 月 25 日 09:00，云栖小镇国际会展中心；李智、冯红婷、陈特夫、王佳梨四场 15 分钟场景分享。
- 适合: 城市场景创新、线下商业、AI 安全治理、具身智能、杭州创新生态。
- 标签: `city-scene`, `ai-business`, `urban-innovation`, `forum`
- 置信度: high

### 017.md 360 乐园

- 主匹配: `12280` 360乐园
- 文章线索: 团聚之夜/云栖厅沉浸式未来游乐园，强调 360 度环屏、影像艺术和现场体验。
- 适合: 影像艺术、沉浸式体验、团聚之夜、想看大屏舞台的人。
- 标签: `immersive`, `youth-reunion`, `arts-media-design`, `performance`
- 置信度: high

### 020.md 夏山未来游乐场集合

- 主匹配集合: `12605` 我在进化，别打扰; `12446` WaytoAGI社区特展; `12752` 一起来养具身小龙虾; `12589` 罗振宇的透明14小时; `12261` 罕见病基因 AI 黑客松; `12507` 2050无障碍游戏厅; `12244` 非语言链接实验室; `12403` 传统教师如何真实转型; `12451` 肯道尔精选BoKC影像分享会; `12598` 未来导演请就位; `12333` 把AI装进硬件里; `12312`, `12338`, `12339` 冷湖宇宙系列; `12509` 冷湖宇宙创世纪; `12510` 钱学森读书会; `12701` AI极速影像工作坊; `12662` 女娲造AI人计划。
- 用途: 这是一篇“给孩子/家庭/AI学习者看的活动合集”，推荐时不要只返回单一活动，应按兴趣拆成亲子 AI、生命科学、具身硬件、身体工作坊、科幻影像等路线。
- 标签: `family-friendly`, `ai-education`, `health-medical`, `robotics-hardware`, `arts-media-design`, `rainforest`
- 置信度: medium to high；其中个别地点/日期应回查活动主表。

### 021.md 开运集团太空专题

- 主匹配: `12326`, `12623` 2050太空AI号启航仪式; `12260` 太空计算专题论坛; `12657` 星际公民登舰见习计划; `12654` 天上的事：太空时代正在到来; `12653` 太空时代开启，我们如何与地外文明对话？
- 适合: 航天、太空计算、太空生活方式、地外文明、沉浸式探索空间。
- 标签: `space`, `aerospace`, `future-life`, `explorer-space`, `mindnet`
- 置信度: high

### 028.md 706 青年空间 x WaytoAGI

- 主匹配: `12545` 社会青年派对; `12432` WaytoAGI 青年团聚; `12443` 星空之夜 Vol.1。
- 相关: `12430`, `12446`, `12588`, `12444`, `12445` 等 WaytoAGI 相关活动。
- 用途: 回答“706/Way2AGI/同行/社群偶遇/星空露营”时作为社群语境证据，不把它当成单一日程。
- 标签: `706`, `waytoagi`, `community`, `social-density`, `camping`
- 置信度: medium

### 034.md DeskClaw

- 主匹配: `12361` AI时代的新坐标：年轻创造者、Agent与未来工作方式
- 相关: `12258` Personal Agent 实验室; `12446` WaytoAGI社区特展
- 文章线索: 4 月 25 日 AI 论坛/圆桌；4 月 24 日 Personal Agent 实验室；4 月 24-26 日探索空间 AI 生意体验。
- 标签: `deskclaw`, `agent`, `future-work`, `business-ai`
- 置信度: high for `12361`, medium for related items

### 035.md 所言吉事

- 主匹配: `12199` 所言吉事的朋友们团聚·见面; `12367` 所言吉事团聚·教练茶话会; `12471` 所言吉事团聚·颂钵与催眠; `12473` 所言吉事团聚·探索流。
- 适合: 低强度社交、自我探索、身体/催眠/教练、连续三日熟人型团聚。
- 标签: `slow-social`, `coaching`, `body-mind`, `rainforest`
- 置信度: high

### 039.md 十字路口

- 主匹配: `12230` 《十字路口》——心理剧本杀+播客录制
- 适合: 心理议题、沉浸式剧本杀、播客录制、深度聊天。
- 标签: `psychology`, `role-play`, `podcast`, `deep-talk`
- 置信度: high

### 042.md 罕见病 / AI for Good

- 主匹配: `12261` 罕见病基因 AI 黑客松
- 相关: `12200` AI 向善; `12307` AI 医疗凑局相亲会; `12308` 年轻人的AI for Good公益孵化论坛; `12309` AI+医疗; `12368` 小众及出众。
- 适合: 医疗 AI、公益科技、患者需求、生命科学、黑客松。
- 标签: `rare-disease`, `ai-for-good`, `health-medical`, `hackathon`
- 置信度: high for `12261`, medium for related forum items

### 044.md 机器人脱口秀

- 主匹配: `12311` 机器人脱口秀大会
- 适合: 机器人、舞台表达、轻松技术展示、想看科技娱乐交叉的人。
- 标签: `robotics`, `performance`, `fun-tech`, `forum`
- 置信度: high

### 054.md / 057.md 灵感交易所

- 主匹配: `12206` 灵感交易所：奇思妙想的文创设计workshop
- 适合: AI 创作者、文创设计、工具包、共创工作坊、想把想法换成可执行作品的人。
- 标签: `inspiration-market`, `creative-workshop`, `ai-creator`, `design`
- 置信度: high

### 060.md 热带雨林召集

- 主匹配候选: `12363` 未来城邦; `12562` 生态链游戏体验; `12566` 一起来练八段锦; `12351` 自然疗愈; `12352` 舞动身心疗愈。
- 用途: 适合回答“热带雨林怎么玩/低强度/刷新活力值/新物种”这类路线问题；具体推荐必须回查热带雨林板块。
- 标签: `rainforest`, `low-energy`, `nature`, `body-mind`, `play`
- 置信度: medium

### 062.md / 077.md / 078.md 三个愿望

- 主匹配: `12207` 好奇游乐场; `12206` 灵感交易所; `12437` 2050好奇的朋友们; `12439` 凝聚好奇｜思想约会。
- 文章线索: 好奇游乐场、灵感交易所、奇人创作坊三条共创愿望；重点是寻找共同书写者，不只是参加者。
- 标签: `curiosity`, `co-creation`, `inspiration-market`, `mindnet`
- 置信度: medium

### 071.md 2050PASS 获取攻略

- 主匹配: 无单一活动。
- 用途: 通行证、实名认证、入场、补领、票据和常见问题说明。回答具体 PASS 操作时可引用为攻略线索，但不要用它推荐活动。
- 标签: `pass`, `ticket`, `logistics`, `entry`
- 置信度: high for logistics only

### 072.md 罕见病基因 AI 黑客松

- 主匹配: `12261` 罕见病基因 AI 黑客松
- 文章线索: 2026 年 4 月 24-26 日，杭州云栖小镇，48 小时攻坚，方向为罕见病基因诊断和 AI 技术。
- 适合: 医疗 AI、生命科学、开源社区、黑客松参赛团队、患者需求解决。
- 标签: `rare-disease`, `genomics`, `ai`, `hackathon`
- 置信度: high

### 073.md 3 月 2050 恳谈会

- 主匹配: 无大会三日活动。
- 用途: 2050 筹备机制、召集人预热、恳谈会背景；不用于 4 月 24-26 日路线推荐。
- 标签: `pre-event`, `organizer`, `orientation`
- 置信度: high for background only

### 074.md 活动召集流程指南

- 主匹配: 无单一活动。
- 用途: 解释 2050 的自愿发起、对焦、宣传、排期、发布机制。用户问“怎么发起活动/2050 为什么不像传统大会”时使用。
- 标签: `organizer-guide`, `unconference`, `volunteer`
- 置信度: high for process only

### 082.md 流浪教研松松快闪

- 主匹配: `12267` 课创黑客松
- 相关: `12266` 流浪课程展; `12268` 青少年导览; `12277` 好奇来信; `12278` 照顾内在小孩
- 文章线索: 课创黑客栈和青少年导览，把 2050 的硬核科技翻译成青少年可参与的学习体验。
- 标签: `education`, `course-design`, `youth-guide`, `teacher-community`
- 置信度: high
