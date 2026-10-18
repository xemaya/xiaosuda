# S1E01 自我介绍：已定稿配方

**2026-10-17 用户确认「这个定稿，配方全部落盘」。** 正式成片为46.333333秒、1112帧、1080×1932、CFR24，SHA256：`37a9f1403bdc7918d60bac7787ccccbec80ac02d0e835ce321c758687b06c6d0`。

- 正式文件：`../../releases/s1e01/2026-10-17/Hi-Soda_S1E01_Self-Introduction.mp4`。
- 正式入口：`../../releases/s1e01/current.json`。
- 工作台定稿：`https://soda.buplayground.cn/api/media/a_f9326941a16b4c4d`。
- 旧How are you?的v14配方和`releases/ep01/current.json`继续保留；本配方记录新情景剧S1E01的制作、关键帧与后期，不改旧冻结文件。

## 开始前校验

```bash
python3 recipes/plush-dialogue-v14/verify.py
python3 recipes/s1e01-keyframes-bgm-v1/verify.py
```

只读校验本配方全部文件、图依赖、镜头长度和正式成片哈希，不联网、不调用配音、不占GPU。

## 已冻结内容

`recipe.json`是索引，路径均相对本配方目录。

| 目录 | 内容 |
|---|---|
| `accepted/` | 用户验收记录、设定/分镜/采用状态快照、全部素材来源链、字幕ASS/SRT、原人声及音效PCM、最终混音PCM、混音验收 |
| `assets/takes/`、`assets/scenes/`、`assets/audio/` | 实际采用素材及必要来源；按哈希去重，不依赖旧SQLite |
| `generation/`、`inputs/` | 每份原生生成的实际图、原始图、输入映射、提示词、seed、prompt_id、回执/历史；重生成所需实际图像和载体 |
| `keyframes/` | 姐姐段干净首帧/转正抬爪，结尾放书释放/全身走近关键帧，生图提示词和来源清单 |
| `edits/fast-run/` | 原速快跑及删除静音等待的依据；S03由原S03前72帧＋原S04前120帧构成，1倍速，不补帧 |
| `music/` | 原创编配、全部音符、系统乐器离线渲染脚本、原始BGM与最终轻声底轨、字幕和后期脚本 |
| `runtime/` | 实际后端/Comfy相关源码快照及v14参数；权重不重复打包，按模型完整文件名复用自部署模型 |
| `context/` | 命名、角色关系、剧本及制作规则的归档上下文 |

整个包不包含API密钥，不要求将视频发往第三方。系统乐器采样库不重新分发；已保存无损BGM母版和乐谱，离线重组成片无需重新渲染乐器。

## 本集固定做法

1. **原生渲染**：H3 Ref2VA FP8＋turbo 4step LoRA，4 steps，euler/beta，768×1376，24fps，长度对齐17k+5；完整模型名在`recipe.json`。当前片段对白载体384×688，只含本段原配音。
2. **关键帧先正确再生成**：姐姐段原首帧已有蓝色布，必须同时替换图片参考与静态载体。S07第48帧加转正抬爪图；S08第67帧约2.79秒加书已放稳且双手释放图，第144帧6秒加全身走近图。用独立LoadImage和AddGuide串联，不把同一首帧反复钉在中间。实际完整图和种子为准。
3. **表演与口型**：本集只由Soda说八句原对白，Jacky和Angela闭嘴听；保留转身、抬爪、挥手、翻页、放书、空手下来、绕桌走近和结尾。首帧问题不逐帧涂改，生成仍不稳则改机位或有动作承接的切镜。
4. **剪辑**：实际顺序S02/S03/S05/S06/S07/S08/S09；前置2秒OP。下拉揭幕重叠8帧，仅用静音缓冲。原速雪地快跑保留，不再慢放，不留起跑前2秒等待。
5. **字幕**：Alibaba PuHuiTi，768×1376排版坐标，英文46/中文42，安全宽620，左右64、底部121；最终随画面缩放到1080×1932。ASS包含已经验证的换行，原文、时间轴和八句声线不变。
6. **BGM**：《Soda Sunny Steps》，90 BPM、C大调、尼龙吉他/稀疏木琴/轻低音，无歌词和重鼓点。最终底轨约-39 LUFS，0.8秒淡入、末尾约2.73秒淡出；人声增益1。音乐侧链threshold0.04、ratio2、attack50ms、release700ms、knee4。有效对白下实测音乐低14.65dB，混音峰值-13.61dBFS、无削波。只加BGM时复制画面码流，不重新编码表演。

## 离线重组成片

```bash
# 只列出计划，不渲染
python3 recipes/s1e01-keyframes-bgm-v1/rebuild.py --out /tmp/soda-s1e01-rebuilt.mp4 --dry-run

# 真正离线重组；需要ffmpeg/libass和ffprobe，使用全新输出名
python3 recipes/s1e01-keyframes-bgm-v1/rebuild.py --out /tmp/soda-s1e01-rebuilt.mp4
```

重组直接读取冻结镜头、原始完整人声/音效PCM、字幕和已淡入淡出的轻声BGM，不调用GPU/TTS，不修改工作台，不覆盖正式文件。程序验证1112帧/CFR24。跨ffmpeg或模型运行时不保证编码文件逐字节相同；正式交付以冻结成片SHA256为准。

## 重生成候选

先从`accepted/asset-provenance.json`找到目标原生asset_id，再准备对应图和所有输入：

```bash
python3 recipes/s1e01-keyframes-bgm-v1/prepare_graph.py a_96a0d7c86d014c4a --comfy-input /tmp/soda-comfy-input --out /tmp/soda-s07-replay.json
```

这一步**只复制输入并导出图，不提交GPU**。实际提交前确认模型和节点兼容、共享队列空闲，使用独立输出前缀和新prompt_id，持久化回执，未知状态不盲目重投。原生采样存在随机性，重生成必须重新逐句验口型、完整动作、关键帧前后连续性，候选不自动成为本定稿。

## 后续项目的图片来源与毛型

本集中归档的部分修复图历史上来自内置imagegen，这是已确认成片的来源记录；**不是今后默认选型**。后续出图、改图优先4090已有Qwen-Image-2.1，逐张记录真实模型、参考、seed、prompt_id。小苏打遵守当前AGENTS中的顺贴圆润毛型要求，先单张审核；黄山或其他新毛型候选不因本集定稿而自动覆盖本集或角色卡。
