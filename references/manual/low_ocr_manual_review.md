# 低 OCR 文章人工补录

## 使用口径

这份文件人工补录 `results/*.md` 中低文本量或批处理失败的文章。它不等于全文 OCR，只用于在推荐时弥补“标题/摘要可判断，但正文不可用”的信息缺口。

使用规则:

- 优先使用 `md_file` 和 markdown 标题，不要只依赖 `articles.csv` 行号；当前 `068-070`、`072/075`、`078-082` 一带存在 CSV 标题与 markdown 标题不完全同序的情况。
- 匹配活动时必须落到 `activity_id`，再从 `activity_index` 读取准确时间、地点、介绍。
- `confidence=high` 表示标题或摘要与活动标题/组织强匹配；`medium` 表示组织/主题匹配但正文不足；`low` 表示只可作为探索线索。
- 低 OCR 文章不应用于引用长段正文。

## 人工补录条目

### 009.md

- md 标题: 少数派的共创时代 | AI 时代，从想法到落地需要几步？
- 可用正文: 只有“分享一篇文章”级别，网页端当前也只抓到摘要卡片。
- 主匹配: `12358` 少数派的共创时代
- 相关: `12540` 少数派的造物者们
- 适合推荐给: 独立开发者、产品创造者、社区共创、从想法到落地的人。
- 主题标签: `community-co-creation`, `indie-maker`, `product-practice`, `ai-creation`
- 置信度: high for `12358`, medium for `12540`

### 023.md

- md 标题: 2050召集令 | 你想成为一名"国王"吗？"未来城邦"帮你实现！
- 可用正文: 科幻迷、未来城邦、赛博朋克/仿生人等摘要线索。
- 主匹配: `12363` 未来城邦：重新定义诗和远方
- 适合推荐给: 喜欢科幻、未来城市、社会规则设计、角色扮演式共创的人。
- 主题标签: `future-city`, `world-building`, `co-creation-game`, `science-fiction`, `social-imagination`
- 置信度: high

### 027.md

- md 标题: 流浪教研x2050课创黑客松板块｜规则说明&招募
- 可用正文: 流浪教研、一线教师、教育公益、课创黑客松。
- 主匹配: `12267` 课创黑客松
- 相关: `12266` 流浪课程展; `12268` 青少年导览; `12277` 好奇来信——如何提问; `12278` 照顾内在小孩
- 适合推荐给: 教师、教育产品/课程设计者、青少年教育、想把现场体验转成课程原型的人。
- 主题标签: `education`, `teacher-community`, `course-design`, `hackathon`, `youth-learning`
- 置信度: high for `12267`, medium for related activities

### 038.md

- md 标题: 所以，究竟什么是2050大会？
- 可用正文: 介绍 2050 不是传统意义上的大会。
- 主匹配: 无单一活动。
- 推荐用途: 作为 2050 背景解释和新用户 onboarding，不用于具体日程推荐。
- 主题标签: `2050-intro`, `orientation`, `human-reunion`, `non-conference`
- 置信度: high for background only

### 040.md

- md 标题: 汇聚热爱，「2050 大会」少数派线下活动邀请你来参与
- 可用正文: 少数派邀请参与 2050 线下活动，强调科技爱好者聚集。
- 主匹配: `12540` 少数派的造物者们; `12358` 少数派的共创时代
- 适合推荐给: 少数派读者、数字生活/效率工具爱好者、想和创作者面对面交流的人。
- 主题标签: `sspai`, `maker-community`, `product-practice`, `community-co-creation`
- 置信度: medium

### 041.md

- md 标题: 2050团聚 | 当硅基AI开始设计芯片，碳基人类还能做什么？4月24日杭州 AI芯片社
- 可用正文: 标题指向 AI 芯片社，但正文主体是 YOLO HAPPY、旅行文化探索、思想约会、百城味道。存在标题/正文主题冲突。
- 标题级匹配: `12220` 探索AI对芯片行业的影响，寻找志同道合的跨界伙伴
- 正文级匹配: `12224` 如果你热爱旅行和文化探索，一定来找我们呀; `12251` 舌尖上的团聚--分享“家乡味道”，让相聚更加美味; `12276` 百城味道
- 使用规则: 用户问 AI 芯片时用 `12220`；用户问 YOLO/旅行/家乡美食时用 `12224`, `12251`, `12276`。不要把 AI 芯片和 YOLO 美食内容合成同一活动解释。
- 主题标签: `ai-chip`, `hardware`, `travel-culture`, `food-potluck`, `community`
- 置信度: high for conflict detection; high for `12220` title-level; high for `12224/12251/12276` body-level

### 050.md

- md 标题: 别只盯着 AI 工具了，这 100 个名额能让你看见创造的另一种可能
- 可用正文: 少数派文章摘要，强调 AI 工具之外的创造可能。
- 主匹配: `12540` 少数派的造物者们
- 相关: `12358` 少数派的共创时代; `12588` Agent时代，人人都是创造者
- 适合推荐给: 想从“用 AI 工具”走向“做产品/作品/社区共创”的人。
- 主题标签: `maker`, `creative-practice`, `ai-creation`, `community`
- 置信度: medium

### 061.md

- md 标题: 少年有请 | 2050科技大会：做AI导演嘉宾，也做火星策展人
- 可用正文: 少年 AI 电影、AI 导演、火星策展等摘要。
- 主匹配: `12598` 未来导演请就位——少年AI电影展映＆沙龙
- 相关: `12700` 光影回响——10后导演的 AI 电影展
- 弱相关: `12326` 2050太空AI号启航仪式; `12312` 冷湖宇宙•科幻圆桌; `12338` 冷湖宇宙·揭开暗夜帷幕，解读宇宙的密信; `12339` 冷湖宇宙·春日限定的星辰之约
- 适合推荐给: 青少年、家长、AI 影像创作者、科幻/太空叙事爱好者。
- 主题标签: `youth-ai-film`, `children-creation`, `science-fiction`, `space-imagination`
- 置信度: high for `12598`, medium for `12700`, low for space-related items

### 063.md

- md 标题: 倒计时33天！2050@2026，WaytoAGI全员集合杭州云栖小镇
- 可用正文: WaytoAGI 社区集合、Agent、OpenClaw、社区实践等摘要。
- 主匹配: `12432` WaytoAGI 青年团聚; `12430` AI全链路：Agent、创作、硬件与社区共创; `12446` WaytoAGI社区特展
- 相关: `12588` Agent时代，人人都是创造者; `12444` WaytoAGI 三周年庆生; `12445` 离谱村音乐会：科技就像音乐
- 适合推荐给: WaytoAGI 社区成员、Agent/工具链实践者、AI 创作者、想从线上社群转线下见面的人。
- 主题标签: `waytoagi`, `agent`, `ai-community`, `openclaw`, `community-meetup`
- 置信度: medium to high

### 065.md

- md 标题: "不如见一面"2050召集令 | 壹木自然读书会
- 可用正文: 壹木自然读书会，自然博物、植物、分享。
- 主匹配: `12455` 和壹木一起刷山
- 适合推荐给: 自然观察、植物、博物、户外轻社交、读书会成员。
- 主题标签: `nature`, `plant`, `reading-club`, `outdoor-social`
- 置信度: high

### 066.md

- md 标题: 4.24-26 | 如果未来已经开始了，你会如何设计自己？
- 可用正文: Tianmeis World Academy, "If the Future Has Already Begun, How Would You Design Yourself?"
- 主匹配候选: `12424` 成为一人公司
- 相关候选: `12420` 金钱心理和投射 | Money Psychology & Projections; `12633` 别把AI当工具：创造你的数字分身与专属角色
- 使用规则: 正文不足，推荐时只能作为“自我设计/一人公司/金钱心理/数字身份”的候选线索；需要结合用户问题再确认。
- 主题标签: `self-design`, `one-person-company`, `future-self`, `money-psychology`, `digital-identity`
- 置信度: medium for `12424/12420`, low for `12633`

### 070.md

- md 标题: 2050@2026 年青人因科技而团聚！
- 注意: `articles.csv` 相邻行与 `results/070.md` 标题不一致；以 markdown 标题为准。
- 可用正文: 需要微信客户端打开；仅能确认 4/24-4/26 杭州云栖小镇见。
- 主匹配: 无单一活动。
- 推荐用途: 作为总入口/口号/日期地点背景，不用于具体活动推荐。
- 主题标签: `2050-intro`, `date-location`, `general-announcement`
- 置信度: high for date/location slogan only

## 人工补录后的剩余风险

- 这些条目没有完整 OCR 正文，不能当作全文知识库引用。
- `041.md` 主题冲突明显，推荐时必须按用户问题选择标题级或正文级匹配。
- `066.md` 只有摘要级线索，不能给出具体流程或分 part 说明。
- 后续若拿到原始截图或登录态全文，应优先重建 OCR，再替换本文件中的低置信度项。
