# 小苏打宇宙 · 出片流程

**当前执行基线：第一集 v12，用户评价约 70 分。先保住并落地已经过 12 版调整的配方，再优化镜头接续；字幕、文案、剧情、声线暂不调整。**
可执行配方、冻结输入、四镜原始节点图与复现证据见 [第一集 v12 配方](recipes/ep01-v12/README.md)。下文保留历史探索记录；具体参数以该配方为准。

**2026-10-15 接续优化验收修正：用户否决 v13 对照片，约 10 秒内仍有三处跳变及可见静帧。**
新实验中，能在一次生成内完成的连续表演应整段生成；不再把多个短镜拼成约 10 秒的测试段。
不得以 `tpad=clone`、循环末帧或提示词中的长定格来补接缝。旧 v12 的 0.5 秒静帧仅作为已冻结历史配方保留，不沿用到新候选。
缩图像素差下降、首尾帧接近均不能作为通过验收的依据：必须检查整段的镜内切换、静帧、角色/背景漂移及对白口型。
当前原生连续镜头实验见 `jobs/1015-v14-native-continuity/`；v12 仍是已认可基线。

角色卡 → 干净首帧单图 → 写手提示词 → 视频 → （可选）字幕/转场拼接。
这条链路已在「小苏打客厅片」和「英语三幕对话片 v2」上验证通过
（批次 `prompts-1014-091543`、`prompts-1014-124431`，角色全程不跑样，台词逐句命中）。

**核心原则：角色卡只能当"参考"，绝不能直接当视频首帧。**
视频模型把首帧当成画面的第一帧来演，素材卡上有几十个姿势+文字排版，
直接喂进去模型只能自己脑补一只狗。角色一致性靠「干净首帧图」锁。

**铁律：任何镜头，第一帧和最后一帧必须是生图模型生出来的图，基于此编排。**
首尾帧都不允许用视频抽帧（抽帧被编码压过，进模型质感塌一档，v8r2 教训）。
编排按「关键帧链条」设计：关键帧 1 →(镜 1)→ 关键帧 2 →(镜 2)→ 关键帧 3…
上镜的尾帧图就是下镜的首帧图。
**落地（v12 起）：ref2v 也能钉尾帧**——`MiniMaxH3ReferenceToVideo` 节点本身没有
last_frame 输入，但官方 `MiniMaxH3AddGuide` 节点可把任意图片钉到任意帧
（`frame_idx=-1` 即末帧），串在 ref2v conditioning 后面即可，声口注入不受影响。
h3run.py 已打补丁：ref/refvideo 分支的 `--last` 走 AddGuide（备份 h3run.py.bak-1015）。
钉尾帧后同机位接缝硬切基本无缝：构图/姿势/毛绒质感连续，但允许**轻微光照与
细节漂移**（AddGuide 是软约束不是逐像素拷贝，v12 用户验收确认此 trade-off 可接受）。
提示词末拍要写明对准的尾帧姿势。
**定型验证批次：v12（`xiaosuda/jobs/1015-v11-keychain`，备份 `out/prompts-1015-122648`）**——
出题镜钉 K2 尾帧、点评镜钉 K3 尾帧；教学镜沿用未钉尾帧的原片，前三镜硬切，练习镜沿用 v7 原片并用 slideup 接入。
四镜均以参考图控制外观，**v12 没有在第 0 帧另接 AddGuide 硬锚定**。
34.9s 竖屏 1080x1932，ASR 全片逐字命中。以后台词片默认按此配方执行。

## 目录约定

```
xiaosuda/
  sheets/        原始角色卡（只读，别改）
  characters.md  角色档案：视觉锚点、性格、同框比例
  firstframes/   首帧图库：<角色>-<场景>.png，可反复复用
  prompts/       视频提示词模板块（可选，攒常用动作编排）
  jobs/          每次出片一个目录：jobs/<日期>-<标题>/prompts.txt + 首帧图
```

## 第一步：角色卡 → 首帧单图

每个角色、每个新场景，先出一张干净单图。用 webui 出图管道（或 studio MCP
的 `studio_gen_image`），把角色卡当参考图（refs），提示词模板：

```
<image1> 是一张Q版<物种>角色设定卡。严格按卡片中的角色形象，生成一张干净的
单角色渲染图：<从 characters.md 抄该角色的视觉锚点>。场景：<目标场景描述>。
<角色>全身入镜，<构图姿势>。画面里只有这一个角色，不要任何文字、不要排版
分格、不要边框、不要设定卡里的其他元素。
```

验收：出图后对照角色卡逐条查比例/配色/标志性部件（呆毛、花发饰、角、卫衣…），
不对就改词重出，别将就——首帧是什么样，视频就是什么样。

产物命名 `firstframes/<角色>-<场景>.png`，记入 characters.md 的已有首帧清单。

### 首帧质感配方（v2 最佳实践的归因，2026-10-14 定）

v2（`prompts-1014-154305`）是画风标杆：毛线针织感强、声口一致好。v6 毛线感变弱，
排查后**不是超分的锅**（超分前后逐帧对比几乎无差），根因全在首帧：

1. **提示词用中文 + 写死"3D毛绒玩偶质感、毛线针织纹理、可见毛线纤维"**。
   v6 用英文 "3D plush-toy film still / soft realistic fur"，出来偏光滑皮克斯渲染；
   v2 中文"毛绒玩偶质感"配合设定卡 refs，出来是毛线感。
2. **主体占画面高度 ≥70%**。v2 角色占 80%+，毛线纹理有足够的像素承载；
   v6 竖屏全身只占 ~45%，纹理直接糊没。竖屏对话场景用中近景（半身/七分身），
   别为了"全身"把角色缩成小不点。
3. **减少编辑轮次**。每过一轮图像编辑（垫高补画、加配饰）微纹理就软一档。
   竖屏构图一次性写进提示词（ refs 会被改图模式拉回参考图比例：把垫到 9:16 的
   画布当 ref 可以锁竖版），配饰在首轮就画上，不追加第三轮。

## 第二步：写 prompts.txt

**正文优先让写手写**：`studio_write(preset=h3_video, text=brief, images=[首帧图])`。
brief 里给足：角色锚点+性格关键词（性格会被编成动作表情）、剧情+逐句台词（注明语言、
**正常语速**、一次一个角色开口）、丝滑要求（完整 initiation-travel-accent-brake-release
力链）、镜头和定格要求。写手产出惯例：台词 `<d>[EN] …</d>` 标记、按秒时间轴、
结尾 CAMERA HARD LOCK。v2 实测写手版动作丝滑度显著好于手写套模板。

写手排障：安全拒答（chibi 角色+"一岁"）就把角色写成"成年卡通吉祥物/毛绒玩偶"、
生日写"宠物狗一岁生日"；工作台 read timeout 直接重试。

在 `jobs/<日期>-<标题>/` 下建 `prompts.txt`，把要用的首帧图复制到同目录
（gen.sh 只认提示词文件同目录的引用文件）。写手产出里的 `@first first_frame.png`
占位符替换成真实文件名，`<Picture 1>` 在纯首帧模式下替换成 "the first frame"。结构：

```
---
@sec 10
@nsfw off
@size 992x1056
@first xiaosuda-living-room.png
The first frame is the SOLE visual authority for the character...
integrated_multimodal_description:
[Shot 1] <场景+角色+起始姿态>
[beats 1-2 | 0.00-1.00] INITIATION/TRAVEL/ACCENT/BRAKE/RELEASE 节拍描述 + CAMERA
...
overall_soundscape: ...
non_diegetic_music: ...
RULES: no text, no overlays, keep chibi proportions consistent with the first frame...
```

参数红线：

- `@size` **必须显式写**，和首帧图比例一致且两边都是 32 的倍数
  （992x1056、768x1344 都行）。gen.sh 直跑没有 webui 管道的比例自动保护，
  不写就按默认 768x1344 把图压扁。
- `@first` 写同目录文件名。`@ref image.png` 这类占位写法会被管道静默剥掉，
  等于没写——这是第一次出片翻车的根因。
- 一条 `---` 一个任务；多条会多卡并行。
- 超过 10 秒自动拆段接续拼接；`@chain on` 首尾接续、`@concat on` 拼成成片。

## 第三步：提交

```bash
./gen.sh xiaosuda/jobs/<日期>-<标题>/prompts.txt          # 提交并跟日志，跑完自动拉回 out/
./gen.sh xiaosuda/jobs/<日期>-<标题>/prompts.txt --dry-run # 只解析不跑，先确认参数
./gen.sh --pull <批次名>                                   # 断线后补拉成片
```

单条 10 秒约 11-12 分钟（fl2va 8 步 turbo）。成片在 `out/<批次名>/`。

## 第四步：验收

```bash
ffmpeg -i out/<批次>/01_*.mp4 -vf "select='not(mod(n,36))',scale=480:-1" -vsync vfr /tmp/frames/f%02d.jpg
```

抽帧逐张看：角色比例/配色/标志部件有没有跑偏、动作节拍对不对、有无文字水印。
有台词的片用 `bl speech recognize --model fun-asr --language en` 转写核对台词
（fun-asr 带句子级时间戳，qwen3-asr-flash 没有时间戳）。
角色跑了就改首帧图，动作跑了就改 beats 描述，别在同一条上反复赌 seed。

## 第五步：后期（字幕/拼接，mediakit 本地能力免 key）

### 台词片走"TTS 换音轨"分支（v3 起标准做法）

模型原声整条丢弃。嗓音配方见 characters.md（MiniMax speech-02-hd，端点必须
api.minimaxi.com，minimax.io 报 2049；output_format=hex）。重要知识点语速 0.85，
其余 1.0。链路：全台词 TTS → ffprobe 拿精确时长 → 排时间窗 → 写手按窗口写口型 →
出片 → `ffmpeg adelay|amix normalize=0,apad + -c:v copy -shortest` 换轨 →
SRT 由自排时间轴直出（不靠 ASR 反推）。

**口型窗口必须落地校准**：写手给的窗口模型只会"大致"执行（v6 实测纠偏两句整体
晚了 1.4s，思考拍被音频抢拍）。出片后抽 0.25s 密度脸部网格图
（`select='not(mod(n,6))',crop=<脸部带>,tile=5x4`）实测每句实际起止，
把 TTS delay 和 SRT 改到实测窗口再出终版。幕内淡融用
`xfade=fade:0.5s + acrossfade`；**幕间转场也用 ffmpeg xfade 自己做**
（slideup/fadewhite 等），别再用 mediakit 圆形交替转场——圆形几何在 9:16
竖屏被拉成椭圆，很丑（v7 翻车，v8 起改）。

### 原生语音路线（v7/v8 验证通过，台词片主路线）

`@refvideo` 会把参考视频的原声作音频条件（h3run.py 的 ref_video_audios），
模型**连内容带音色一起复制**载体音轨。正确用法：载体音轨=当集台词 emotion TTS
混音（带表演情绪，比换轨的平板配音自然得多）→ 静态首帧+表演轨混成载体 mp4 →
`@ref 首帧 + @refvideo 载体` 出片 → 口型音色一步到位，无需换轨。

要点（v7/v8 实战）：

- 载体视频降采样到 384x688 再上传，防显存 OOM；OOM 就换卡/再降采样重试。
- **载体的画面帧也进条件（ref_videos），会直接影响成片质感**：载体必须用
  高清图（首帧/高清关键帧）循环来拼，绝不用视频里抽出来的压缩帧——压缩帧的
  糊感会被模型继承放大（v8r2 点评镜塌毛根的根因）。
- 同机位拆镜接缝**直接硬切**（concat），不要融幕；动作小就只是一点点跳变，
  融幕反而出重影。换机位/换景才用 xfade。
- 口型跟随注入音频而非提示词文本，时间轴由载体 adelay 决定。
- refvideo 模式不能用 `@first`，角色一致性靠 `@ref` 图。
- **台词总长超 10s 就拆镜**（v8 幕一拆成"出题+回答"9s + "点评"5.5s 两镜），
  别硬挤间距，思考拍被抢拍比多跑一镜更伤。
- **拆镜接续 = 关键帧链条 + 钉尾帧**（见顶部铁律）：每镜 `@ref` 首帧图 +
  `--last` 尾帧图（=下一镜首帧），接缝硬切即无缝。关键帧用同一配方同一批
  生图产出（refs 只用角色卡），**锁死景别**——"保持构图"不够，要写清
  "角色在画面中的大小/位置/裁切与参考完全一致、不要拉远"。
  若上镜有推拉运镜，尾帧景别以末帧为准，别以首帧为准。
  视频抽帧当 ref/last 作废（x264 压过的帧进模型质感塌一档）。
  motion context 续镜（h3run.py `--prev-latent`）画面无缝但
  **会盖过 refvideo 声口权威，台词乱编复述**（两个 seed 均崩），只适合无台词
  纯画面延长，台词片禁用。
- **模型会在静音尾幻觉复述台词**：载体静默尾巴收到 ≤0.7s（防幻觉空间），提示词
  RULES 加"says exactly the lines, never repeat"；出片后仍须 ASR 全片核对，
  多余的尾巴 `-t` 精裁到词尾。
- **切镜前静帧**：镜尾留 ~0.5s 静帧再进转场（tpad 延长用 `stop_duration=0.5`，
  `stop` 参数单位是帧不是秒，写 0.5 会静默失效）。
- TTS 换轨分支（上文）降级为备用：需要精确控字幕轴或原生路线翻车时再用。

### 通用后期命令

```bash
# 台词轴:fun-asr 转写拿句子时间戳 → 生成 SRT(按剧本修正标点)
bl speech recognize --url <音频.mp3> --model fun-asr --language en --out <结果.json>
# 烧字幕:教学片用 ali_puhui(易读优先),花哨字体(站酷快乐体)不适合正文
mediakit-cli editing add-subtitle-to-video --video-url <片段.mp4> --subtitle-url <字幕.srt> \
  --subtitle-font-type ali_puhui --subtitle-font-size 38 --client-token <每次唯一>
# 幕间转场:ffmpeg xfade 链(竖屏安全),例:四段 幕内fade+幕间slideup
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=<lenA-0.5>[x1];\
   [x1][2:v]xfade=transition=slideup:duration=0.5:offset=<lenAB-0.5>[v];\
   [0:a][1:a]acrossfade=d=0.5[a1];[a1][2:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]" out.mp4
# 超分(异步约6-7分钟)
mediakit-cli video enhance-video --video-url <成片.mp4> --scene aigc --resolution 1080p \
  --bitrate-level high --client-token <每次唯一>
```

mediakit 任务异步,返回 task_id 后用 `mediakit-cli shared query-task --task-id <id>` 查结果,
产物是 vod 临时链接,及时 curl 拉回本地。**mediakit 默认幂等去重会吞掉参数相同的
连续任务,每个任务必须带唯一 `--client-token`**。mediakit 云端能力需要 MEDIAKIT_API_KEY
(方舟 ARK_API_KEY 不通),本地剪辑/字幕能力零配置零费用。

## 多角色同框

- 同框首帧 = 一张画好所有角色的图（出图管道多 refs，或直接生成同框图），
  再当 `@first`。注意 characters.md 里的体型差构图提醒。
- `@mode ref` 参考图模式（`<Picture 1>` 指代）也可试，但一致性不如首帧锁定稳，
  优先走「同框首帧」路线。
