# ask2050 信源台账

## 三个输入文件分别是什么

- `articles.csv`: 77 篇公众号文章索引，字段为标题、链接、发布时间。它只证明文章清单存在，不包含正文和图片。
- `activities.csv`: 286 条 2050 官网活动主表，字段包含活动 ID、标题、板块、时间、地点、召集人、简介和正文。推荐时的时间、地点、活动 ID 以它为主事实。
- `results.zip`: 82 份 markdown 结果和一个 `batch_summary.md`。zip 内没有 `.png/.jpg/.webp` 原图，只有 OCR/抓取后的文字结果，所以不能从这三个文件重新跑图片 OCR。

## OCR 与人工状态

- 结果 markdown: 82 份。
- `batch_summary.md` 显示: 12/82 成功，1/82 失败，69/82 skipped。
- 82 份 markdown 已全部映射回 77 篇 `articles.csv`；多出的 5 份来自重复、拆分或标题别名。
- 82 份 markdown 对应的文章发布时间均为 2026 年；默认推荐只使用 2026 年发布的文章和 2026-04-24 至 2026-04-26 的活动。
- 71/82 份达到 300 字以上的可检索文本阈值。
- 11/82 份低文本，需要人工补录。
- 当前人工已读并补入推荐线索: 33 份，包括低文本、失败、标题错位、重复拆分和重点集合文章。

## 使用口径

- 不要说“全部图片已 OCR”。正确说法是：已处理 82 份 markdown 结果，其中 12 份为批处理成功，69 份为跳过但已有文本结果，1 份失败；低覆盖和重点错位项已人工补录。
- 旧年份字样只作背景，不进入路线推荐。比如标题或正文里出现 2025，不代表推荐 2025 活动；默认只看 2050@2026。
- 问活动时间、地点、报名入口时，先回到 `activity_index.min.json`。
- 问公众号线索、外部召集文章、攻略、PASS、召集流程时，先查 `article_evidence_index.json`，再按其中的 `matched_activity_ids` 回查活动主表。
- `result_file` 是内部证据定位，不是用户可见链接；用户可见链接用 `article_url` 或活动 `url`。

## 重点人工补录范围

- 低文本: 少数派、未来城邦、流浪教研、2050 介绍、少数派线下、少年有请、WaytoAGI、壹木自然读书会、设计自己、2050 总入口。
- 批处理失败: `041.md`，标题是 AI 芯片，但正文是 YOLO/旅行/百城味道，必须按用户问题分开回答。
- 重点集合/错位: 夏山未来游乐场集合、开运太空专题、706 x WaytoAGI、DeskClaw、所言吉事、心理剧本杀、杭州场景妙妙屋、灵感交易所、热带雨林召集、2050PASS、罕见病黑客松、活动召集流程、三个愿望、流浪教研松松快闪。

## 机器可读索引

完整机器可读台账在 `article_evidence_index.json`:

- `counts`: 全局统计。
- `records[].batch_status`: `✅` / `❌` / `skipped`。
- `records[].review_tier`: `ocr_batch_success`、`text_extracted_ocr_not_confirmed`、`low_text_manual_required`、`ocr_failed_manual_required` 等。
- `records[].manual_reviewed`: 是否人工看过并补了推荐线索。
- `records[].matched_activity_ids`: 可以回查活动主表的候选活动 ID。
- `records[].search_terms`: 核心检索词，只放标题、人工摘要、别名和活动 ID；不放正文摘录。

## 原文层

- 安装后的 skill 不携带原始图片、raw OCR markdown 或公众号正文片段。
- 需要核对原文措辞时，使用 `article_url` 回到公众号文章，或回到生成工作区的 `data/incoming/results/results/*.md`。这属于最深层证据，不应默认加载。
