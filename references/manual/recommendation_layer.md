# ask2050 人工推荐层

这个文件是人工判断层，优先级高于机器关键词标签。`activity_index.*.json` 里的 `topic_tags` 只能作为候选，不应机械照搬。

## 板块画像

### 新生论坛

- 主要功能：系统性报告、主题论坛、议题集中学习。
- 适合人群：想快速了解一个领域、找观点和趋势、听行业/学术/社区案例的人。
- 推荐强度：中高到高。论坛通常信息密度大，连续听多个容易疲劳。
- 参与方式：listen, learn, ask-after-session, meet-speaker。
- 社交密度：中。适合会后找人，不一定适合现场深聊。
- 推荐标签：`forum`, `systematic-learning`, `trend-scan`, `speaker-led`。
- 推荐注意：不要把所有带 AI 字样的新生论坛都当作 AI 核心活动，要看标题和摘要是否真正围绕 AI。

### 探索空间

- 主要功能：展台、体验、项目展示、能看能玩、现场试用。
- 适合人群：硬件/机器人/产品/设计/教育工具/城市空间/AI 应用实践者；也适合第一次来 2050 的人破冰。
- 推荐强度：低到中。可以碎片化逛，也可以围绕一个项目深聊。
- 参与方式：browse, demo, hands-on, talk-to-builder。
- 社交密度：低到中。比论坛更容易自然开口。
- 推荐标签：`exhibition-demo`, `hands-on`, `builder-facing`, `roaming-friendly`。
- 推荐注意：探索空间适合作为论坛之间的缓冲，不应只当成“展览”。

### 思想约会

- 主要功能：圆桌、深聊、观点碰撞、哲学/社会/技术议题讨论。
- 适合人群：想和陌生人认真聊天、对 AI 与社会/教育/哲学/社区问题感兴趣的人。
- 推荐强度：中高。社交和认知投入都高。
- 参与方式：deep-talk, roundtable, debate, co-think。
- 社交密度：高。适合愿意开口的人，不适合完全低能量状态。
- 推荐标签：`roundtable`, `deep-talk`, `philosophy-mind`, `high-social-density`。
- 推荐注意：用户如果只想听报告，优先新生论坛；如果想参与讨论，再推荐思想约会。

### 热带雨林

- 主要功能：开放社交、兴趣相遇、轻量活动、工作坊、小型体验。
- 适合人群：第一次来、想认识人、想恢复能量、想从一个轻松入口进入 2050 的人。
- 推荐强度：低到中，部分工作坊会更高。
- 参与方式：meetup, casual-chat, light-workshop, serendipity。
- 社交密度：中到高，但压力通常低于思想约会。
- 推荐标签：`meetup`, `low-pressure-social`, `life-sports`, `serendipity`。

### 青年团聚

- 主要功能：社区团聚、主题社群连接、行业/兴趣圈层会面。
- 适合人群：有明确圈层或想找组织的人，如 AI+X、浙大人、青年浙商、研究者、创作者。
- 推荐强度：中，取决于具体团聚。
- 参与方式：community-meetup, find-collaborators, open-mic。
- 社交密度：中高。
- 推荐标签：`community-youth`, `meetup`, `collaboration`。

### 青春舞台

- 主要功能：演出、放松、晚间节目、情绪恢复。
- 适合人群：高强度论坛后需要缓冲的人，或带朋友感受 2050 氛围的人。
- 推荐强度：低。
- 参与方式：watch, relax, evening-social。
- 社交密度：低到中。
- 推荐标签：`performance`, `low-intensity`, `evening`。

### 热力运动

- 主要功能：篮球、足球、晨跑、助盲跑等运动参与。
- 适合人群：想通过身体活动社交、恢复状态或公益体验的人。
- 推荐强度：中到高，取决于项目。
- 参与方式：sports, team-up, outdoor。
- 社交密度：中。
- 推荐标签：`sports-camp`, `body-activity`, `outdoor`。

### 星空露营

- 主要功能：户外夜间活动、露营、晚间轻社交。
- 适合人群：想放松、想夜间继续交流但不想再听密集报告的人。
- 推荐强度：低到中。
- 参与方式：camping, night-talk, relax。
- 社交密度：中。
- 推荐标签：`camping`, `evening`, `low-pressure-social`。

## 人工主题判断规则

### primary_topic_tags

只给活动真正的核心主题。判断顺序：

1. 看标题。
2. 看“这 part 是干嘛的”摘要。
3. 看板块和参与方式。
4. 最后才参考机器 `topic_tags`。

示例：

- `AI+教育创新实践分享`: primary = `ai`, `education`; secondary = `workshop`, `privacy-safety`。
- `为什么你越会和AI聊天，越不会谈恋爱?`: primary = `relationship`, `community-youth`; secondary = `ai`。
- `把AI装进硬件里，把创造带进每间教室`: primary = `ai`, `education`, `robotics-hardware`; secondary = `hands-on`, `classroom`。
- `太空时代开启，我们如何与地外文明对话?`: primary = `space`, `philosophy-mind`; secondary = `camping`, `evening`。

### secondary_topic_tags

用于发现潜在兴趣，但不要主导推荐。例如活动里提到 AI，但核心是社交、艺术或恋爱议题，则 AI 应放 secondary。

## 体验标签

推荐回答中优先使用这些人类可理解标签，而不是只展示机器标签：

- `听报告`: 信息密度高，适合学习和趋势判断。
- `深聊`: 需要开口，适合观点碰撞。
- `看展体验`: 低门槛，适合碎片时间。
- `动手工作坊`: 需要投入，适合创造/实践。
- `找同伴`: 目标是认识人或找项目伙伴。
- `放松恢复`: 用于低强度路线。
- `夜间继续聊`: 晚上还想参与但不想高强度。
- `户外身体活动`: 运动、晨跑、露营相关。

## 强度与社交密度

### intensity

- `low`: 演出、露营、晨读、随逛展台、轻量社交。
- `medium`: 常规论坛、工作坊、团聚、探索空间深聊。
- `high`: 黑客松、长时段论坛、深度圆桌、高参与工作坊、运动竞赛。

### social_density

- `solo-friendly`: 一个人也能看/听/逛。
- `small-group`: 小组、圆桌、工作坊。
- `crowd`: 大论坛、舞台、集体活动。
- `deep-talk`: 思想约会类，需要观点表达。

## 推荐重排原则

1. 已注册他山世界：使用用户画像标签做最终匹配。
2. 未注册：仍给预览路线，但提醒注册后可保存轻量标签。
3. 日期优先于主题。用户只有一天时，不跨天推荐。
4. 地图成本优先于微弱主题匹配。相邻区域的 80 分活动通常优于远处的 85 分活动。
5. 每条路线至少包含一个缓冲点：热带雨林、探索空间、青春舞台、星空露营或餐饮/休息。
6. 不要连续安排三个高强度论坛。
7. 对“第一次来”用户，先给一个低门槛入口，再给高价值主活动。
