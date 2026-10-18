# 第一集 v12：已认可的制作配方

用户定位：经过 12 版从约 40 分调整到约 70 分，先固定成果，再优化接缝。
本目录冻结现有画面、配音、台词、字幕和后期参数。后续实验另开 job，保留原成片作为对照。

## 已落地的材料

- `manifest.json`：输入、原始输出、节点图、脚本的 SHA-256，以及模型、seed、帧数、镜头来源和后期参数。
- `assets/`：3 张高清关键帧、练习镜首帧、4 个配音载体、16 条原始 TTS、v12 字幕与当时的角色档案。
- `assets/prompts-v12.txt`：可直接提交给现有 `gen.sh` 的四镜参数与原提示词。
- `graphs/`：从 ComfyUI 已成功任务回收的四份完整 API 节点图，包含原提示词。
- `runtime/`：实际服务器的 `h3run.py`、`h3batch.py`、回执工具与原生 H3 节点实现快照。
- `evidence/`：原任务成功回执、输出哈希、恢复的历史命令与本次重建验证。

本地 `../server/bin/h3run.py` 已同步服务器上 v12 使用过的尾帧补丁；未向服务器部署新代码。

## 四镜来源：以实际任务为准

| 镜头 | seed | 实际帧数 / 24fps | 图像约束 | 成片来源 |
|---|---:|---:|---|---|
| 出题 quiz | 1954216863 | 226 | ref K1 + AddGuide K2，frame_idx=-1 | `shot1-pin.mp4` |
| 点评 verdict | 871602711 | 124 | ref K2 + AddGuide K3，frame_idx=-1 | `shot2-pin.mp4`，随后静帧延长 0.5 秒 |
| 教学 teach | 909285593 | 243 | ref K3，无尾帧 guide | `shot3.mp4` |
| 练习 practice | 1481111183 | 243 | ref 原练习首帧，无尾帧 guide | `../out/prompts-1014-233816/03_s1481111183_00001_.mp4` |

原视频仍在 `jobs/1015-v11-keychain/` 和上表的 `out/` 目录，由 manifest 的哈希校验。
四镜全部使用 Ref2VA FP8 + ref2v turbo LoRA（强度 1）+ 4 steps + euler/beta。
生成分辨率 768×1376；VAE、CLIP 与 vision 模型名均保存在原节点图内。
请求秒数 9/5/10/10 会按 17k+5 对齐成 226/124/243/243 帧，不能拿整数秒替换实际时长。

v12 只有前两个镜头钉尾帧。四镜均没有单独的第 0 帧硬锚定。
`@ref` 负责外观参考，不能据此声称首帧像素被锁定。

## 声口和载体配方

现有 MiniMax speech-02-hd 配音：萌鸡 `chunzhen_xuedi`、pitch +1；小苏打 `Cute_Elf`、pitch 0。
按角色、语速和 emotion 制作单句 TTS，再去首尾静音，具体历史请求见 `evidence/tts-source-commands.json`。
其中出题句未做相同的去静音处理，emotion 写在 voice_setting 内；其他保留的历史请求将 emotion 写在请求顶层。
这里记录实际请求，不能据此断言所有 emotion 参数都被服务端采用。
已认可的音频文件是复现依据，本次不重新请求 TTS。

| 载体 | 静态画面 | 延迟（毫秒，按台词顺序） | 长度 |
|---|---|---|---:|
| carrier1 | K1 | 500 / 5780 | 9.0s |
| carrier2 | K2 | 500 / 2820 | 5.2s |
| carrier3 | K3 | 250 / 1900 / 3840 / 5680 / 7560 / 8680 | 10.2s |
| practice-carrier | 原练习首帧 | 560 / 2280 / 3480 / 4960 / 6480 / 7200 | 10.2s |

画面用高清图循环后缩到 384×688；禁止用上镜 MP4 抽帧替换高清图。
前三个载体为 yuv420p，历史练习载体为 yuv444p，重建时保留这一差别。
混音用 `amix normalize=0`；视频模型同时读取载体画面和当镜台词音轨。
禁止继承上镜的对白、MP4 或 motion context 来接台词镜。

## 可直接运行的复现

从 `xiaosuda/` 运行；只用 Python 标准库和本地 ffmpeg/ffprobe，不上传、不生成新台词。

```bash
python3 recipes/ep01-v12/replay.py verify
python3 recipes/ep01-v12/replay.py carriers --out /tmp/xiaosuda-v12-carriers-new
python3 recipes/ep01-v12/replay.py assemble --out /tmp/xiaosuda-v12-edit-new
```

输出目录中的同名文件不会覆盖。`carriers` 检查四个载体重建结果；`assemble` 从原四镜重建无字幕片并比对 SHA-256。
本机已验证：四个载体全部逐字节一致；无字幕片全部逐字节一致。
完整验证结果与 ffmpeg 版本见 `evidence/replay-verification.json`。

需要重跑 GPU 时，在 `4090/` 运行以下命令。它会上传冻结输入、创建新批次并使用 GPU；本次没有重跑整集。

```bash
./gen.sh xiaosuda/recipes/ep01-v12/assets/prompts-v12.txt --dry-run
./gen.sh xiaosuda/recipes/ep01-v12/assets/prompts-v12.txt
```

注意现有 `gen.sh --dry-run` 仍会创建远端批次并上传输入，只是不提交渲染。
恢复到新服务器时，先使用 `runtime/` 中的已归档脚本和相同模型；不要依赖未经核对的机器默认配置。
完整节点图可用于核对，而不是重新手写一套近似参数。

## 后期保持原版

1. 点评镜以 `tpad=stop_mode=clone:stop_duration=0.5` 延长画面，音频补到 5.6667s。
2. 前三镜分别 concat 视频和音频；到练习镜用 slideup 0.5s，原 offset 为 24.7084s，音频 acrossfade 0.5s。
3. libx264 CRF 18、yuv420p、AAC，得到 `v12-nosub.mp4`。
4. 烧原 `v12.srt`，字体 ali_puhui、38px；超分参数 scene=aigc、resolution=1080p、bitrate-level=high。每次新云任务使用唯一 client-token。

本轮未重跑字幕和云端超分，原字幕片及 1080×1932 成片的哈希已冻结。
无字幕片与载体的逐字节重建不等于 GPU 推理或云端超分也能逐字节复现。

## 下一步只优化接缝

用户提供的讨论：[AI短剧续接方案](https://chatgpt.com/c/6ad07992-4ebc-83e8-84d7-60c587411805)。
先测试同一份高清图在相邻镜头的尾部与头部各自锚定；只改变一个条件，保留原 seed、台词和载体。
字幕、知识点、剧情、声音和系列扩展暂不调整。
检查整个镜头内的身份、毛绒纹理、背景构图及对白，而不只检查拼接边界。
原 v12 在约 5.7s、12.17s 的镜内构图突变也列入接续检查，避免把突变从接缝搬到镜头内部。
实验、原图和结果均放在 `jobs/1015-v13-continuity-experiment/`，通过对照后再决定是否形成新配方。
