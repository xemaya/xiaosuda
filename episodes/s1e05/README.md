# S1E05 · 学会分享 · Sharing Is Caring!

编辑原稿 `scripts/editorial/s1e05-original.txt` 的制作入口。四部分 41 句，按用户决定删掉结尾 d41「All Together 三人齐说」，实拍 40 句，结尾改无台词欢呼。

| 文件 | 内容 |
|---|---|
| `script.md` | 制作稿：改动说明、四个部分、五机位、逐句对白、硬约束 |
| `dialogue.json` | 40 句对白（说话者、英文、译文、表情、语速） |
| `setting-v1.json` | 五个场景设定卡，已获用户确认 |
| `board-v1.json` | 第一版执行分镜（含 9 处续接） |
| `board-v2.json` | 续接改直接剪接（S03/S05/S07/S09） |
| `board-v3.json` | **当前执行版**：20 段全部直接剪接，3495 帧 / 145.625 秒 |
| `board-plan-v1.md` | 分镜说明与验收重点 |
| `voices-v1.json` | 40 句原声与 Mimi 声线 |
| `takes-v1.json` | 20 段采用记录与合成结果 |
| `source.json` | 原稿出处、规范化清单、状态与未决问题 |

## 当前状态（2026-10-18 已验收）

用户说**“通过，归档”**。成片 `releases/s1e05/current.json`：3495 帧 / 145.625 秒 / 1080×1932 / CFR24 / SHA-256 `fae10af8…`。复核 `python3 recipes/s1e05-sharing-v1/verify.py`。

## 已知偏差

1. **全部 20 段是直接剪接**：本工程 22 帧续接会把上一段末尾放进本段开头（接缝差 42–51）并截掉段末约 0.9 秒语音，详见 `recipes/s1e05-sharing-v1/README.md` 与 AGENTS.md。
2. 结尾 S19/S20 复用开场全景主图，红球在 Soda 手里重新出现。
3. S10 等段落存在缓慢推近。
4. 逐句口型是每句窗口内采样帧核对，非 40 句逐帧。
