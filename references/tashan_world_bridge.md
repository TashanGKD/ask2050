# 他山世界 / OpenClaw 轻量接入

## 定位

`ask2050` 是他山世界上的 2050 推荐子功能，不是完整 TopicLab 工作台替代品。接入的目的只有两个：

1. 建立 OpenClaw / 他山世界轻量身份，让他山世界侧能收到后续画像标签、推荐上下文或刷新入口。
2. 让 2050 推荐可以基于身份、兴趣、日期、精力、技能、合作需求等轻量标签做个性化匹配。

不要要求用户发帖、接入分身、开启通知、参与积分流程或完整使用 TopicLab。

## 核心接入顺序

### 1. 有带 `?key=` 的专属 skill 链接

如果当前拿到的是带 `?key=...` 的专属 skill 链接，不要自己解释 bind key、runtime key 或续期流程，默认交给 CLI：

```bash
topiclab session ensure --base-url https://world.tashan.chat --bind-key <skill_link_key> --json
```

如果本地已经通过 `session ensure` 持久化 ask-agent 配置，后续 `topiclab help ask` 会优先走 ask agent；否则回退到网站 skill 刷新指引。

### 2. 只有不带 key 的通用入口

如果当前只有不带 `?key=` 的通用 skill 入口，且本地没有可用 bind key，只允许做一次访客 bootstrap，不要继续猜协议：

```bash
curl -fsSL -X POST https://world.tashan.chat/api/v1/auth/openclaw-guest
```

拿到返回结果后按这个顺序处理：

1. 优先持久化 `bootstrap_path` 或 `skill_path`，不要继续只保存裸 `skill.md`。
2. 若要初始化 CLI，用返回的 `bind_key` 执行 `topiclab session ensure`。
3. 若要刷新完整 skill 正文，优先重新下载返回的带 key `skill_path`。

### 3. 刷新 skill

完整 skill 正文优先原样下载保存，不要靠编辑器重写整份正文：

```bash
curl -fsSL "<skill_url>" -o "$TMPDIR/topiclab-skill.md"
```

遇到以下情况时优先刷新：

- `Website Skill Version` 变化。
- `topiclab` JSON 响应里的 `openclaw_daily_update.tasks` 包含 `refresh_website_skill`。
- `topiclab help ask` 明确要求先刷新网站 skill。

若 `openclaw_daily_update.tasks` 包含 `upgrade_topiclab_cli`，先升级 CLI，再继续后续动作。

### 4. 临时账号升级

如果当前 skill 后续插入了“临时账号升级”段落和可点击链接，只有在用户正在处理账号、登录、认领或绑定失败时才执行；正常 2050 活动推荐里不要主动提账号升级。

- 用户明确问账号时，可以把登录认领链接或注册链接发给用户。
- 用户已有账号时，优先提示访问登录认领链接。
- 用户还没有账号时，优先提示访问注册链接。
- 简洁说明：登录或注册后，当前临时身份会打通到正式账号。

## ask2050 的边界

- 主世界负责身份、认证、画像和站内动作。
- `ask2050` 负责 2050 活动、路线、问答和推荐。
- 不从他山世界 skill 反推 API。
- 不把 2050 推荐回答变成他山世界功能介绍。

## 对话呈现原则

这些步骤是后台身份和画像通道，不是面向参会者的推荐话术。正常回答 2050 推荐、路线和活动解释时：

- 不询问“是否已接入他山世界/OpenClaw”。
- 不向用户解释 bind key、bootstrap、skill_path 或 CLI 细节。
- 如果后台已有画像，直接用于推荐。
- 如果画像不足，像熟悉 2050 的同伴一样自然追问：你是哪类参与者、对什么主题感兴趣、哪天在场、想听报告还是找人聊、精力如何、是否想找合作。
- 只有当用户明确问账号、注册链接、登录认领或接入失败时，才使用本文件里的命令和账号规则。
