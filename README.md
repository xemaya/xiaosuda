# Hi, Soda! · 小苏打英语情景剧工程

少儿英语情景剧《Hi, Soda!》的制作工程：剧本、角色设定、分镜、原生视频配方、字幕与合成流水线。角色为毛绒玩具风 Q 版：阿拉斯加幼犬 Soda（35cm）、小鸡哥哥 Jacky（42cm）、绵羊姐姐 Angela（48cm）、龙妈妈 Mom、牛爸爸 Dad，以及 Mimi、栗子。

## 现在有什么

| 位置 | 内容 |
|---|---|
| `AGENTS.md` | 工程规则与最新决策（接手先读） |
| `docs/agent-handoff.md` | 交接入口：能力边界、执行顺序、易退化约束 |
| `docs/series-bible.md` | 系列统一口径（命名、关系、镜头与包装） |
| `characters.md` | 角色档案、视觉锚点、嗓音配方 |
| `WORKFLOW.md` | 制作流程总览 |
| `scripts/editorial/` | 用户原始《少儿英语大纲.docx》归档与逐集拆分（S1E01–S1E06） |
| `episodes/` | 逐集制作资料：剧本、对白、设定、分镜、采用记录 |
| `recipes/` | 可复用配方与只读校验脚本（v14 原生接法、S1E01/S1E02 定稿、黄山篇） |
| `workbench/` | FastAPI 制片工作台：项目/版本/素材/任务队列、写手与 4090 生成通道 |
| `releases/` | 已验收成片的正式入口（`current.json` + 清单） |
| `sheets/` | 角色卡（工程身份基线） |
| `firstframes/` | 首批场景首帧 |

已验收：`releases/s1e01`、`releases/s1e02`、`releases/huangshan`。S1E03《荡秋千》在 `episodes/s1e03/`，制作中未验收。

## 这个仓库不含什么

成片、关键帧、任务证据包、音频与字体体积很大，不随代码入库：

- `jobs/`（逐任务输入、回执、原片、截图）
- `workbench/evidence/`（部署与验收证据包）
- `assets/`、`references/`
- 各类 `*.mp4 / *.png / *.wav / *.ttf`

它们在制作机 4090 上、按任务 ID 保存；`recipes/*/verify.py` 的哈希校验需要这些素材在本机才能完整跑通。仓库定位是**代码 + 文档 + 角色卡 + 配方脚本**。

## 跑校验（需要本地素材）

```bash
python3 recipes/plush-dialogue-v14/verify.py
python3 recipes/s1e01-keyframes-bgm-v1/verify.py
python3 recipes/s1e02-fluffy-quadruped-v1/verify.py
```

## 工作台本机开发

```bash
SODA_DATA=/tmp/soda-dev SODA_AUTH=off SODA_WORKER=off python3 -m uvicorn workbench.app:app --host 127.0.0.1 --port 3214
python3 -m pytest workbench/tests -q
node --check workbench/web/app.js
```

生产入口：`https://soda.buplayground.cn/`（独立服务与数据库，改动不涉及 Short Video 旧站）。

## 约定

- 一集一个知识点，情景剧形式，含包装不超过 5 分钟
- 同一连续机位用同一张主图；跨段只传实际保留画面的末 22 帧，不传旧音频
- 逐句核对说话者与听者口型；生成成功不等于验收通过
- 未获用户认可的候选不覆盖已验收基线
