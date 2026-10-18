# 毛绒动物对白：v14 已验收配方

2026-10-15 用户观看第一集 v14 后确认「这版牛逼了，非常丝滑」，并要求落盘供下次复用。
当前默认执行本配方。v12、v13 和旧流程仅作为历史排查记录，不再覆盖此处规则。

## 复用入口

```bash
# 从 xiaosuda/ 运行：只读检查，不上传、不使用 GPU
python3 recipes/plush-dialogue-v14/verify.py

# 导出包含两个连续镜头的示例 ComfyUI API 图，不会提交渲染
python3 recipes/plush-dialogue-v14/continuity.py --out /tmp/new-episode.graph.json
```

- `recipe.json`：已验收的模型、分辨率、采样、声线、载体与交付参数。
- `continuity.py`：构造新镜头或追加纯画面运动续接，保持与成功图相同的节点接法。
- `assets/`：已认可的高清场景图、第一集载体/音轨、原字幕、本地字幕样式及官方字体。
- `accepted/`：第一集真实成功的三份 API 图、提示词、任务回执和交付证据。
- `runtime/`：成功运行时的 H3 原生节点和 Motion Context 源码。
- `frozen-files.json`：冻结文件哈希；已认可成片也单独校验 SHA-256。

已认可成片：`../../jobs/1015-v14-native-continuity/xiaosuda-how-are-you-v14-review.mp4`。
第一集完整后期脚本和验收画面在该 job 目录内。

## 每次制作按这个顺序

1. 确认台词、说话人、情绪，使用 `characters.md` 的已认可声线；先做当集音轨，再定每段窗口。
2. 为一个连续机位选一张高清场景主图。角色、背景、大小、光照始终由它控制。换场才换主图。
3. 优先用项目自部署写手，附高清主图，给足逐句台词、实际音频时刻、动作起落和段首状态。
4. 能在约 10 秒内演完的连续表演一次生成；超过时按下述画面续接规则拆分。
5. 载体只包含高清主图的静态循环和**当前段**对白，缩为 384×688、24fps。
6. 在同一个 ComfyUI API 图内生成相邻片段，直接传未压缩的画面张量；不要把上一段 MP4 再当身份/材质参考。
7. 先裁掉续接头，再按计划保留实际使用帧数。下一段必须继承真正被保留的末尾，不能继承已裁掉的多余尾巴。
8. 后期保持 CFR24，声音使用完整当集音轨；检查说话人与口型后再封片。本地烧字幕、确定性缩放到 1080×1932。
9. 看完整片及每个接点前后；指标和抽帧只辅助，不代替用户观看验收。

## 固定参数

H3 Ref2VA FP8；ref2v turbo 4step LoRA，强度 1；4 steps；euler / beta；768×1376、24fps。
完整权重文件名、CLIP、vision、双 VAE 名称见 `recipe.json`，不要依赖服务器默认值。

萌鸡：speech-02-hd，`chunzhen_xuedi`，pitch +1。小苏打：`Cute_Elf`，pitch 0。
角色新台词的语速和情绪按当集表演设置，首句音频完成后先实测时长。第一集原音频已冻结，复现时直接使用。

## 帧数和声音排布

设计划保留 N 帧，上下文 O=0（独立镜头）或 22（续接）：

```
原生采样长度 L = 向上对齐到 17k+5 的 (N+O)
载体时长 = L/24 秒
续接载体 = O/24 秒静音 + 当前段音轨 + 必要的短静音尾巴
交付画面 = 去掉头部 O 帧，再保留前 N 帧
```

22 帧约 0.9167 秒。目标 10 秒受网格影响可能得到 243 帧，即 10.125 秒；续接的原生长度还包含将裁去的上下文开销。
不要改变对白速度来凑整数秒，也不要复制静帧凑时长。

第一集已验证：独立 243 帧；续接原生 209 帧→裁头 22 帧→保留 178 帧。
出题镜原生 192 帧→保留 184 帧，在第 183 帧锚定同一张主图，并立即切入相同主图的下一镜，不加停帧。
这些是第一集的具体排布，下一集按自己的音轨排 N，不照抄秒数。

## 纯画面运动续接的准确接线

```
上一镜 VAEDecode
  → 上一镜 MotionContextTrim
  → ImageFromBatch(只保留最终使用的帧)
  → 下一镜 MiniMaxH3MotionContext.context_frames

下一镜：高清主图 + 本段配音载体 → MiniMaxH3ReferenceToVideo
  → MiniMaxH3MotionContext → sampler → decode → MotionContextTrim
```

续接节点不连接 `context_audio`、`context_latent` 或上下文 `audio_vae`。
`audio_context_length=0` 的实际语义是跟随画面长度，不是关闭旧声音；不能靠这个参数禁用音频。
`continuity.append_take()` 会保持上述接线，并返回 `visible_images`，下一镜直接继承它。

第一镜可用 `first_anchor=True`。带运动上下文的镜头不要再用静态首帧覆盖其头部。
使用 `roles_from_v14()` 可绑定已冻结的第一集图，追加新段而保留既有节点 ID 和缓存。
`SaveVideo` 保存裁过上下文但尚未裁多余尾巴的片段，便于审查；后期仍应遵守返回的 `keep_frames`。

## 提交与复用边界

导出的 API 图要按 `LoadImage` / `LoadVideo` 名称上传对应文件，再提交到现有 ComfyUI `/prompt`。
成功任务与完整请求示例在 `accepted/*render-history.json`；第一集原请求还保留在源 job 的 `*submission.json`。
提交前查队列；新 job 使用独立输出前缀，写下返回的 prompt_id，断线后查同一个任务，不盲目重投。
`gen.sh` 的普通分段接法不等于这里的纯画面上下文图，续接应使用 `continuity.py` 或已冻结的 API 图。
不需要修改共享节点、重启实例或训练模型。

## 已知失败和验收

- 不同机位/背景透视的关键帧塞进同一镜，模型会在镜内换构图。
- 只比较首尾相似度，可能漏掉镜头内部的跳变。
- 复制末帧补 0.5 秒，会产生可见静帧。
- AV latent 同时携带旧音频，可能复述上段对白。
- 续接上一段未被采用的额外尾巴，会接错姿态和时刻。
- ffmpeg concat 后重新设置时间戳可能丢帧率标记；xfade 前最后显式设 `fps=24`，交付再核对 r_frame_rate/avg_frame_rate。

字幕默认走本地 libass；普惠体文件和已校准样式已保留，不再依赖云端字幕服务。
新视频上传第三方云服务需要另有授权，本配方和离线检查不会上传。
复杂运镜、大幅位移、多人抢话等场景不在本次已验证范围内。
