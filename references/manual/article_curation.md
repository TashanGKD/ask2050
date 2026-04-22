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
