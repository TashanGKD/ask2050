# 公众号文章到活动/小节映射状态

## 三个输入文件分别是什么

- `activities.csv`: 2050 活动主表。每行是一条官方活动记录，包含 `activity_id`、标题、板块、召集人、时间、地点、活动页 URL、正文等。当前纳入 286 行。
- `articles.csv`: 公众号文章索引。每行是一篇文章的标题、链接、发布时间。当前纳入 77 篇，但它本身没有文章正文。
- `results.zip`: 文章正文和图片 OCR 的批处理结果目录。它提供可检索原料，但不是已经清洗好的日程数据库，也没有自动完成“文章小节 -> 活动 ID / 报告 / 节目”的映射。

## 当前真实口径

- `activities.csv` 的 286 条活动已经全量纳入 ask2050。
- `articles.csv` 的 77 篇文章已经作为文章索引纳入。
- `results.zip` 中的 markdown/OCR 文本已经作为证据原料纳入。
- 还没有完成全量人工 crosswalk: 每篇公众号文章内部的 part、节目、报告、生活指南条目，需要逐项映射到 `activity_id`，或补成独立的知识条目。

## 为什么会出现“286 全，但文章 part 不全”

`activities.csv` 是活动级粒度；公众号文章和 OCR 图片经常是更细或不同粒度。

一条活动行可能包含多个报告、多个表演节目、多个圆桌环节；一篇公众号文章也可能包含场地、餐饮、交通、地图、生活指南等非活动信息。这些内容适合推荐和问答，但不一定在 `activities.csv` 中有独立 `activity_id`。

## 已核对的示例文章

### 热带雨林

- URL: `https://mp.weixin.qq.com/s/w1DwPt9yp_h1Cl1wgvJEuw`
- 文章标题: `热带雨林@2050@2026：别看活动表，看了你也会觉得“离谱”！`
- OCR/正文: `article_ocr/007.md`
- 活动主表: `热带雨林` 57 条
- 状态: 文章已纳入，板块活动已纳入；文章内部叙事和部分场景尚未逐项绑定到活动 ID。

### 青春舞台

- URL: `https://mp.weixin.qq.com/s/Uc4LIsFOWVQIm1qA1wqJfQ`
- 文章标题: `青春舞台@2050@2026：节目单新鲜出炉！`
- OCR/正文: `article_ocr/006.md`
- 活动主表: `青春舞台` 13 条
- 状态: 节目单大部分能对应到活动主表，但节目名、表演者、夜场和活动标题之间需要人工别名归一。

### 星空露营

- URL: `https://mp.weixin.qq.com/s/MaV0AlyUOu8ZmmaVeU5Y8A`
- 文章标题: `星空露营生活指南@2025@2026`
- OCR/正文: `article_ocr/004.md`
- 活动主表: `星空露营` 4 条
- 状态: 露营活动已纳入；坐标、配套、餐饮、注意事项、地图日程攻略应进入 logistics 层，不应只按活动表统计。

### 新生论坛

- URL: `https://mp.weixin.qq.com/s/0pk6F8FvoqjysXBApdrrdA`
- 文章标题: `新生论坛@2050@2026：500+脑暴席卷云栖，年青就要最大声分享！`
- OCR/正文: `article_ocr/008.md`
- 活动主表: `新生论坛` 96 条
- 状态: 文章已纳入，板块活动已纳入；文章内多个 part 和单个报告尚未完成逐项映射。
- 优先人工映射项:
  - 未来公园: 百集绿色生活与智慧妙想的活力赛场
  - 绘画的真理
  - 1000 天后的美术馆
  - 用 AI 逆袭记忆，解锁爷爷奶奶的《寻梦环游记》
  - 《南都画报》青年影像分享会
  - 当孩子成为导演，用 AI 画出会动的故事
  - 10 后导演 AI 电影节
  - 青年导演 X AI 共创未来影像
  - 让 AI 圈的“黑话”与话语权力
  - 青智助老进小班，志愿智暖银幕情
  - 未来编程：重新定义律师和远方
  - 童星未来：当创新基因注入可持续发展
  - 物品重生：记忆永生
  - 10 后创业，求支持
  - 在家学习夏令营
  - AI 时代的教育与社会科学

## 下一层应该补什么

建立 `article_activity_crosswalk.json`:

- `article_url`
- `article_title`
- `ocr_file`
- `section_title`
- `unit_type`: `activity` / `talk` / `performance` / `roundtable` / `logistics` / `map`
- `matched_activity_id`
- `date_tags`
- `time_range`
- `location`
- `topic_tags`
- `audience_tags`
- `confidence`
- `evidence_excerpt`

推荐时必须区分:

- 活动主表事实: 可直接按 `activity_id` 推荐。
- 文章/OCR 事实: 可作为解释、补充和问答证据。
- 未完成 crosswalk 的小节: 可以回答“文章里出现过”，但不能假装已经匹配到官方活动 ID。
