# S1E04 · 认识新朋友 · Let’s Make a New Friend!

编辑原稿 `scripts/editorial/s1e04-original.txt` 的制作入口。剧情、11 句英语与译文保留，只按 series-bible 规范人名（Baking Soda→Soda、Chick→Jacky、Kitty→Mimi）。

| 文件 | 内容 |
|---|---|
| `script.md` | 制作稿：改动说明、知识点、三机位、逐句对白、硬约束、实测时长 |
| `dialogue.json` | 11 句对白（说话者、英文、译文、表情、语速） |
| `setting-v1.json` | 三个场景设定卡（`park-path-wide` 全景 / `park-meet-medium` 中景 / `park-friends-close` 近景），已获用户确认 |
| `board-v1.json` | 执行分镜：六段、1026 帧 / 42.75 秒（含 2 秒 OP），已获用户认可并开拍 |
| `board-plan-v1.md` | 分镜说明与逐镜验收重点 |
| `voices-v1.json` | 11 句原声（asset / 说话者 / 秒数）+ Mimi 声线定稿信息 |
| `takes-v1.json` | 六段采用记录、逐镜审核结论、合成结果与已知偏差 |
| `source.json` | 原稿出处、规范化清单、状态与未决问题 |

## 当前状态（2026-10-18 已验收）

- 剧本、设定、主图、原声、分镜均已确认；六段拍摄全部采用；用户 2026-10-18 说**“通过，归档”**。
- 正式入口：`releases/s1e04/current.json`；成片 `releases/s1e04/2026-10-18/Hi-Soda_S1E04_Lets-Make-a-New-Friend.mp4`，1026 帧 / 42.75 秒 / 1080×1932 / CFR24 / SHA-256 `b76f9220…`。
- 复核：`python3 recipes/s1e04-new-friend-v1/verify.py`；经验与偏差记录在 `recipes/s1e04-new-friend-v1/README.md`。

## 已知偏差（如实记录）

1. **S06 结尾**：三人一起转身走开（Soda、Jacky 背对镜头），不是分镜写的“停住大笑收住”。可作为“一起跑去玩”读，但要不要只重拍这一镜由用户决定。
2. **S05**：Mimi 没有按分镜从坐姿起身，全程坐着；次要偏差，未重拍。
3. 全景主图（v3）下方空地偏多，是主图构图如此，不是拍摄漂移。
4. 轻声 BGM 实测比人声低 20.21 dB（S1E03 同法 20.07 dB，S1E02 规格 17.5 dB）；如需更明显可整体 +2.5 dB。

## Mimi 声线（本集首次定稿）

`lovely_girl`（萌萌女童），pitch `+2`，对白 `speed 1.05`。四选一试听在 `jobs/1018-s1e04-new-friend-v1/voice-audition/`（A/B/C/D，用户选 A）。已同步 `characters.md`、`docs/series-bible.md`、`workbench/catalog.py` 与工作台人物库。
