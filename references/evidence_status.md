# 证据状态与加载规则

## 数据源口径

| 层级 | 文件 | 作用 | 可信口径 |
|---|---|---|---|
| 活动主表 | `activity_index.min.json`, `activity_index.full.json` | 推荐、时间、地点、活动 ID | 286 条活动全量纳入，作为推荐主事实 |
| 文章索引 | `articles_index.json` | 公众号文章标题、链接、发布时间 | 文章列表索引，不等于正文 |
| OCR/正文原料 | `article_ocr/*.md`, `article_ocr_index.json` | 原文片段、图片 OCR、公众号补充信息 | 可检索证据原料，非全量校验数据库 |
| 文章到活动映射 | `article_activity_crosswalk.json` | 公众号 part/节目/报告到活动 ID 的人工映射 | seed 层，已覆盖重点文章，不宣称全量 |
| 人工策展 | `manual/article_curation.md`, `manual/article_aliases.json` | OCR 不足、标题错位、别名和人工判断 | 推荐时可用，但必须回查活动主表 |

## 当前覆盖状态

- 活动主表: 286/286 纳入。
- 公众号文章索引: 77 篇纳入。
- OCR markdown: 82 份原料，其中 71 份达到可检索文本阈值。
- OCR 批处理摘要: 12/82 显示成功，1/82 失败，69/82 跳过。
- 优先补缺: 12 个短文本、失败或错位项已人工看过并补入 `manual/article_curation.md`。

## 使用规则

1. 普通推荐只用活动主表和人工推荐层，不向用户暴露 OCR 状态。
2. 用户问公众号文章、截图、节目单、生活指南时，再加载 OCR/文章层。
3. 如果 OCR 原料短、失败或标题错位，优先加载 `manual/article_curation.md`。
4. 别名查询先用 `manual/article_aliases.json` 找活动 ID，再回查 `activity_index.min.json`。
5. 文章人工策展只提供“匹配线索和推荐口径”，不当作全文引用。
6. 涉及文章内部 part 时，用 `article_activity_crosswalk.json`；没有匹配 ID 的 part 只能说“文章中出现过/需要进一步确认”。

## 重点边界

- `041.md` 标题指向 AI 芯片，正文主体是 YOLO/旅行/百城味道。回答时必须按用户问题选择标题级或正文级匹配，不可合并解释。
- `068-070`、`072/075`、`078-082` 一带存在 CSV 标题与 markdown 标题不完全同序。引用时优先看 markdown 标题和人工策展说明。
- `星空露营` 查询会命中容器活动，也可能命中地点在星空露营大草坪的其它活动；推荐时应说明是“露营活动”还是“地点相关”。
