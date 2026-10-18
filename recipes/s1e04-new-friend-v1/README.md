# S1E04：新角色首次登场与三人同框对白

**2026-10-18 用户确认「通过，归档」。** 正式入口 `../../releases/s1e04/current.json`：1026 帧 / 42.75 秒 / 1080×1932 / CFR24，SHA-256 `b76f9220f641c90d93bd76b5a11fcc734c2803a1ca826bca35f3c572a09d482b`。

基础生成参数沿用 `../plush-dialogue-v14/recipe.json`，本配方不改 v14、S1E01、S1E02、S1E03 的冻结内容。

## 验证

```bash
python3 recipes/s1e04-new-friend-v1/verify.py
```

只读校验：本配方文件哈希、三张已采用主图、六段采用素材、11 句原声、认可成片的帧数与时基，不调用 GPU/TTS、不写工作台。

## 本集新东西（可复用的经验）

1. **新角色首次进入生产线**（Mimi）：角色卡 `sheets/xiaomi-mimi.png` 是三视图+表情+动作的多面板卡，直接整张喂给 Qwen 会把面板排版带进画面。做法是裁出**单角色面板**（`refs/mimi-front.png`）当 image3，只作身份/花色/眼色/项圈权威，并明确写“不要复制白色面板底、不要让她直立”。
2. **三档身高是三条独立约束**：Jacky 42 > Soda 35 > Mimi 33。提示词里写成三档排序 + “最小者头顶（不含耳尖）必须明显低于 puppy 头顶”，并同时给出“不要放大谁、不要缩小谁”的反向句子；审核时逐帧量三者的头顶像素。
3. **保持同一地面水平**：Mimi 坐在**草地**上、花坛石沿在她身后，不上沿、不上台阶——坐高不是身材，抬高就会破坏 33/35 的比较基准（S1E03 的秋千座板已经踩过一次）。
4. **角色多了会画出重复角色**：全景第一版直接画出两只小鸡。修法不是重写整段，而是在 BRIEF 顶部加一条 `COUNT IS A HARD RULE: exactly THREE actors … never a second chick, never a second hoodie`，并在 NEG 里列 `two chicks, duplicate chick, second hoodie, clone`。
5. **续接语法不变**：S02→S03 仍是同机位 22 帧纯画面续接（`match_tail`），接缝用末帧/首帧像素差核对（本集 mean diff 3.74，仅噪点级）。换景别（S03→S04）与换回同一机位重拍（S04→S05、S05→S06）一律直接剪接。
6. **新声线先试听再配音**：Mimi 用 `lovely_girl` pitch +2、对白 speed 1.05（四选一）。定稿写进 `workbench/catalog.py` 后必须重启 `soda-workbench` 才会进人物库，重启前 TTS 会报“声线尚未定稿”。
7. **设定版本与已认可样图的冲突要留派生记录**：样图出图后只改了 Mimi 四句 speed（不影响画面），当前设定版本因此变化；没有伪造版本号，而是把同一份字节新登记为主图，记 `derived_from_asset` / `derived_from_setting_version`，再按当前版本采用（见 `accepted/sample-approval.json` 与 `jobs/1018-s1e04-new-friend-v1/approve_sample.py`）。
8. **合成沿用 S1E03 的坑**：`fps_mode` 只有 FFmpeg 9 支持，服务 PATH 是 4.4；合成必须在自己的进程里设 `SODA_FFMPEG=/home/huanghaibin/envs/web/bin/ffmpeg` 再跑（`run_assemble.py`）。队列里那条任务会先被服务 worker 抓去失败一次，错误留在 job 的 `error.txt`，随后由进程内重跑覆盖成 succeeded。

## 时长构成

| 段 | 机位 | 帧 | 秒 | 对白 |
|---|---|---:|---:|---|
| S01 | `park-path-wide` | 153 | 6.375 | d1 Soda / d2 Jacky |
| S02 | `park-meet-medium` | 200 | 8.333 | d3 Soda / d4 Mimi |
| S03 | `park-meet-medium`（22 帧续接） | 201 | 8.375 | d5 Jacky / d6 Mimi |
| S04 | `park-friends-close` | 190 | 7.917 | d7 Soda / d8 Mimi |
| S05 | `park-meet-medium` | 126 | 5.25 | d9 Jacky / d10 Soda |
| S06 | `park-path-wide` | 108 | 4.5 | d11 Mimi |
| OP | — | 48 | 2.0 | — |

11 句实测 33.658 秒（Mimi 四句 3.0–4.7 秒，是本集比 S1E02/S1E03 长的原因），加段首 0.4 秒与句间 0.35 秒后成片 42.75 秒。

## 包装与声音

- 2 秒 `Hi, Soda!` 片头、中英大字幕（EN 46 / ZH 42，安全宽 620，按本集真实文字重新换行计时），烧录进画面。
- 轻声 BGM `Soda Sunny Steps` 复用已认可底轨，8.0/2.5 秒淡入淡出、侧链避让人声；实测比人声低 20.21 dB，峰值 −9.22 dBFS，无削波，加 BGM 时画面码流按哈希校验未变。

## 已知偏差（不当作通过的理由）

1. **S06 结尾**：三人一起转身走开，不是分镜写的“停住大笑收住”。用户验收时接受该收法；要改只能重拍 S06（其余五段不受影响）。
2. **S05**：Mimi 未按分镜从坐姿起身，全程坐着。
3. 全景主图下方空地偏多（主图构图如此，不是机位漂移）。

## 素材位置

- 制作工程：`../../jobs/1018-s1e04-new-friend-v1/`（脚本、候选、contact sheet、`final/`）。
- 粗粒度证据：`evidence/episode-evidence.json`（逐镜 prompt/seed/audio turns、主图与后期哈希）、`evidence/captions/`（SRT/ASS/合成清单/BGM 结果）。
- 用户确认原话：`accepted/` 与 `../../jobs/1018-s1e04-new-friend-v1/README.md`。
- 成片与字幕：`../../releases/s1e04/2026-10-18/`（媒体不入 git）。
