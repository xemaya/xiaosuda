# Hi, Soda! 英语情景剧：接手入口

2026-10-18。供新的 agent 在不依赖原聊天历史的情况下制作下一集。当前规则以仓库根目录 `AGENTS.md` 为准；角色和内容以 `docs/series-bible.md` 为准。

**后续剧本入口：`scripts/editorial/index.md`。** 已归档用户提供的《少儿英语大纲.docx》、可搜索全文及S1E01～S1E06逐集原文。编辑S1E03是《荡秋千》，不是旧`SERIES.md`选题表中的《感谢》。工程现有`episodes/s1e03/script.md`是另一agent原创《谢谢啦》，有其单独确认历史；不得混称编辑原稿，也不得仅因补齐原稿就擅自覆盖/取消它。接续制作前明确使用哪份来源，用户已明确选择的版本优先。

本文主要记录英语情景剧的共用制作方法。**环游世界/真实地点旅行线另读[旅行线接手入口](travel/README.md)**，其中有黄山正式片、真实参考资料、最终镜头/对白索引、静默云海修正和下一目的地流程；黄山不占用S1E01/S1E02编号。

## 已有能力与边界

已经跑通并保存：剧本拆解→角色/场景设定→分镜→主图/动作关键帧→原配音→原生视频→口型/动作审查→特写剪辑→字幕/OP/BGM→用户验收→归档。S1E01、S1E02都有用户认可成片。

这是**可交接、有人审看的半自动制作流程**。工作台负责版本、素材、任务回执与基础生成；复杂动作关键帧、镜头返工、对白特写和轻声BGM还有单集制片脚本。尚无“任意新剧本直接一键变成合格成片”的通用命令；`jobs/`内脚本包含集号、角色、ID、帧数和已存在状态，不能照抄后直接运行。

## 新 agent 需要什么

| 能力/权限 | 用途 |
|---|---|
| 图像理解，能查看实际图片和视频画面 | 审身份、姿态、毛型、道具、口型与接点；只读提示词不够 |
| 读写完整工程，运行 Python / ffmpeg / ffprobe | 制片文件、配音长度、载体、剪辑、字幕、混音与校验 |
| SSH进入现有4090，或已登录工作台的操作权限 | 调用已部署写手/Qwen/H3，检查队列和原任务回执 |
| 使用已有配音配置的权限（仅有新对白时） | 固定声线；配置由后端读取，不复制或打印密钥 |

不要求 agent 自带同一种生图工具。**默认生图/改图仍走4090 Qwen-Image-2.1**；agent主要做约束、看图和筛选。换成其他图像提供方需要用户另行同意。没有4090/工具执行权限时，可以做剧本与审图，不能声称完成了拍摄。

## 先读、先校验

从工程根目录依次阅读：

1. `AGENTS.md`、本文件、`WORKFLOW.md`。
2. `docs/series-bible.md`、`characters.md`、实际角色卡 `sheets/`。
3. `recipes/plush-dialogue-v14/README.md`、`recipes/s1e01-keyframes-bgm-v1/README.md`。
4. `recipes/s1e02-fluffy-quadruped-v1/README.md`：最新自然犬类姿态、毛绒材质和双人对白实例。
5. `workbench/README.md`：现有工作台入口及版本/采用规则。

```bash
# 只读，无联网、GPU或配音调用
python3 recipes/plush-dialogue-v14/verify.py
python3 recipes/s1e01-keyframes-bgm-v1/verify.py
python3 recipes/s1e02-fluffy-quadruped-v1/verify.py
```

当前认可成片入口为 `releases/s1e01/current.json`、`releases/s1e02/current.json`、`releases/s1e03/current.json`、`releases/s1e04/current.json`；旧 `releases/ep01/current.json` 是 How are you? 技术样片，不能当新剧集编号或叙事模板。

**S1E04《认识新朋友》2026-10-18 已定稿**（用户“通过，归档”）：Mimi 首次登场，声线 `lovely_girl` +2 / speed 1.05 已入库；11 句/一处三机位/1026 帧/42.75 秒。三人同框的配方经验（新角色只喂单角色面板、三档身高写法、重复角色修法）与已知偏差见 `recipes/s1e04-new-friend-v1/README.md`。下一集是 S1E05《学会分享》，先在 `scripts/editorial/s1e05-original.txt` 基础上做制作稿，不要沿用本集脚本里的固定 ID。

## 每集执行顺序

| 阶段 | 必须留下的结果 | 进入下一步的条件 |
|---|---|---|
| 剧本核对 | `episodes/<集号>/`内原稿出处、正式名剧本、逐句对白/说话者/译文 | 不漏改剧情和英语；不明角色先解决 |
| 剧情/分镜 | 角色清单、2～4个场景主图预算、机位/景别、动作、对白归属 | 形式为情景剧，含包装≤5分钟，安排全景与特写 |
| 单张风格校准 | 一张代表画面及其模型/参考哈希/seed/prompt_id | 用户确认角色身份、动物姿态、毛绒材质后再扩图 |
| 全套关键帧 | 每机位主图，必要的同机位动作中间状态，审图与用户确认记录 | 用户确认全套后才能拍；候选不自动采用 |
| 原声/定时 | 固定声线的逐句原音、实测秒数、准确对白间隔 | 完全匹配的合格原声直接复用；新句子才新配音；未知回执先核查 |
| 原生拍摄 | 写手实际提示词、静态载体、本段音轨、API图、seed、唯一prompt_id、原片、实际保留22尾帧 | 先查共享队列；每段2～10秒，连续表演能一次完成就一次生成 |
| 审查/返工 | 完整动作与逐句口型核对，失败原因及独立候选 | 不把生成成功当通过；先查输入/主图/关键状态，再重生成或换镜头语言 |
| 剪辑/合成 | 原生素材特写、大字幕、2秒OP、低音量BGM、成片/字幕/混音检查 | 确认每段帧数、CFR24、原声完整、字幕安全、BGM避让、不削波 |
| 用户验收/归档 | 验收原话、成片SHA、release入口、素材/配方/来源链 | 用户认可前不覆盖正式基线；无平台上传授权就只交付文件 |

原声可以按工作台流程提前准备，但**准备原声不代表获准生成视频**。用户本轮明确“只出图”时，不生成配音或视频。

## 三项最容易退化的约束

- **Soda姿态属于身份的一部分。** 默认大头、短腿、自然犬坐/四脚着地/四足跑；不要把第一集积木桌旁的例外双脚直立扩散到全集。35/42cm不是坐姿头顶必须对齐的比例。Jacky是双足小鸡，不能跟着变四足。
- **顺毛不等于短绒。** Soda的胸颊需要有长度、疏密和立体分层，Jacky需要柔软绒羽。避免尖刺炸毛与强逆光，也不能压成植绒、短天鹅绒或塑料。每张直接对照认可样张，不让候选层层转引磨掉材质。
- **嘴型按声音归属验收。** 逐句核对谁说、谁听；听者闭嘴。有笑容、点头、动作自然都不能替代这项检查。用原生说话者特写切镜可以改善表达，禁止逐帧涂嘴/贴毛或修补颜色遮盖结构错误。

S1E02认可材质样张：`jobs/1017-s1e02-material-v3/porch-material-candidate.png`。整套认可关键帧及哈希见 `episodes/s1e02/keyframes-v4.json`。它们适合Soda/Jacky的材质与姿态参考，不是其他集的新布景，也不替代其他角色的角色卡。

## 现有执行通道与代码位置

工作台：**https://soda.buplayground.cn/**。优先复用其项目、版本、素材、原声和回执，不新建另一套数据库/服务；不能改 Short Video旧站。

| 位置 | 用途 / 注意 |
|---|---|
| `workbench/domain.py` | 人物、设定、分镜、对白覆盖校验 |
| `workbench/store.py` | 项目版本、采用关系、任务、素材；先查当前版本，不能用旧主图/旧分镜冒充当前 |
| `workbench/providers.py` | 写手、Qwen/H3、原声复用、实际音频定时、任务回执恢复 |
| `recipes/plush-dialogue-v14/continuity.py` | 冻结原生接法，只导出图；不自行提交GPU |
| `jobs/1017-s1e02-filming-v5/` | 已成功单集实例；先读README，再参考prepare/create_board/shoot/editorial_cfr24/finishing，不直接运行旧集脚本 |
| `jobs/1017-s1e02-filming-v5/delivery-evidence.tgz` | 本集实际API图、原声、提示词/种子/回执、字幕与混音证据，113项；不是新集配置文件 |

如当前机器已配置 `shouyun-4090`，只读连接自检：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 shouyun-4090 'test -d /data/app/huanghaibin/soda && test -x /home/huanghaibin/envs/webui/bin/python && test -x /home/huanghaibin/envs/web/bin/ffmpeg'
```

当前服务器路径（新环境需核实，不能假设存在）：

- 服务源码：`/home/huanghaibin/soda/current/xiaosuda`；服务数据：`/data/app/huanghaibin/soda`。
- Python：`/home/huanghaibin/envs/webui/bin/python`；在服务源码目录使用`PYTHONPATH=.`。
- 合成时为**本进程**显式设置`SODA_FFMPEG=/home/huanghaibin/envs/web/bin/ffmpeg`、`SODA_FFPROBE=/home/huanghaibin/envs/web/bin/ffprobe`，避免误用旧`/usr/bin/ffmpeg`。
- 只用当前启用的8188～8192空闲队列；8194/8195曾按用户要求停用，不启动它们。检查队列、取得空闲实例后提交；不抢占、重启或修改共享节点。
- `IdleReservedProduction`的文件锁空闲GPU选择器目前由历史制片工具提供；工作台普通队列选择与特殊中间帧注入没有全部抽成统一新集CLI。参考实现时复制到**新集独立执行器**并保留回执契约，不修改该历史共享文件。

## 拍摄与后期必须保留的细节

H3 Ref2VA FP8＋turbo 4step LoRA强度1，4 steps、euler/beta，768×1376、CFR24，原生帧数17k+5；载体384×688，只放本段原声。具体权重名以v14 recipe为准。

连续机位用同一高清主图。续接只传**实际保留画面的最后22帧**，不传旧音频/AV latent；续段载体前加22/24秒静音，出片裁掉画面上下文头。`audio_context_length=0`并不是禁用音频，不能凭字面改接法。

动作中间状态用独立图片的`LoadImage → MiniMaxH3AddGuide`；同一首帧重复钉在中间会冻结动作。S1E02奔跑第64帧只是该集已验证时间点，新集要按真实配音/动作重定，不能照抄。

字幕采用Alibaba PuHuiTi，在768×1376坐标中英文46/中文42、安全宽620，输出1080×1932；按**新集实际文字和音频**重新换行计时，不能复用旧集同名d1/d2的字幕内容。BGM复用已认可无损底轨、压低并侧链避让人声，不增加歌词。

特写从原生运动素材裁切即可；固定相机不等于全程中景。overlay后避免冗余fps过滤导致少一帧；逐片验证帧数及r/avg_frame_rate=24/1，不以复制末帧补齐。OP与正文颜色元数据可能使诊断过滤器重初始化；精确按帧检查时用`-reinit_filter 0`，不能仅靠接触表标签断言时间错位。

未知GPU或配音回执：先查原`prompt_id`/history和已保存文件；不重抽、重复计费。候选失败先保留证据，修改输入后用新候选ID；不要改已登记素材的文件内容。

## 可以直接给下一个 agent 的任务

> 接手本工程制作指定的一集英语情景剧。先读AGENTS.md和docs/agent-handoff.md，校验v14、S1E01、S1E02认可配方；使用docs/series-bible.md、characters.md和已认可成片/关键帧保持角色、自然动物姿态、毛绒材质及固定声线。沿用现有soda工作台与4090，不新建服务；先核对我提供的剧本，控制2～4个场景主图，出一张代表样图供我确认，再扩全套关键帧；我确认全套后才拍。新集独立目录和任务前缀，逐张逐段保存真实模型、参考哈希、seed、prompt_id、原音与审核。缺少服务器/工具权限请明确报告；不要用成功回执代替视觉验收，也不要直接执行旧集带固定ID的脚本。
