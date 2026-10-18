# 黄山篇：最终状态与接手记录

截至2026-10-18，本片已交付。接手先看[旅行线入口](README.md)，不要从最早的三分钟草稿或某张旧主图开始重拍。

## 2026-10-18 V4已获认可

用户观看后确认“非常不错，总结经验落盘”。[认可配方](../../recipes/huangshan-pine-village-v1/README.md)已记录迎客松局部修树、9秒并肩进村、静默嘴型裁头、四足步态及显存失败恢复。V4逐字节归档，current已指向V4；保留V3与原生成记录中的历史pending，不改写原始证据。本次归档没有再次调用模型、平台发布或工作台线上采用。

## 正式文件

| 项目 | 当前依据 |
|---|---|
| 成片入口 | [releases/huangshan/current.json](../../releases/huangshan/current.json) |
| 完整视频 | [Hi-Soda_Huangshan_Final.mp4](../../releases/huangshan/2026-10-18-v4/Hi-Soda_Huangshan_Final.mp4) |
| 字幕与交付证明 | [交付目录](../../releases/huangshan/2026-10-18-v4/README.md)、manifest.json、evidence/verification.json |
| 最终状态 | 用户认可V4“非常不错，总结经验落盘”；仅交付文件，无平台发布 |
| 长度/规格 | 3389帧，24fps，141.208333秒；1080×1932；两秒OP最先 |
| SHA-256 | `dd1455e21dcc13003171c3eb8b3bb304b8af792f928774614319da853f4f8b4b` |
| 最终剪辑/对白 | [final-script.md](../../episodes/travel/huangshan/final-script.md) |
| 机器可读索引 | [production-index.json](../../episodes/travel/huangshan/production-index.json) |

本片是独立旅行试片，没有占用教学集编号。Soda与Angela出镜，23句中文原声复用；没有新增历史人物演员。下一部的语言和片号需要按新任务决定。

## 最终叙事

OP → 家中看照片提出“石猴在看什么” → 迎客松问好 → 枝条近景配姐姐画外讲解 → 四足小苏打回应 → 发现猴子形山石 → 云海揭晓/纯景观看/解释 → 林间读书谈旅行记录 → 瀑布旁画手账 → 温泉旁对望转身、并肩走向暖灯村舍，镜头拉远收尾。

20个正文窗口沿用S01、S03、S05……S22等历史编号，S02/S04没有独立出片，不代表缺镜。最终时间线完全以整数帧与原声窗口为准，不能沿用草稿的“0–15、15–40……180秒”。

三处容易被旧快照覆盖的编辑决定：

1. **S05，19.333–27.375秒**：原双人讲解多次诱发Soda抬双前爪及镜内换构图，最终采用同棵迎客松的枝条近景，Angela原声在画外。主图是原4090主图的确定性裁切，不是新拍角色。
2. **S06，27.375–31.250秒**：从枝条切回原中景，独立生成，不继承S05枝条画面的尾帧。最终用五个不同同机位状态约束，避免两次蹦起；不是反复复制同一首帧。
3. **S11，61.333–67.667秒**：原生未裁切片段仍有角色无声动嘴，用户指出1:02–1:06后，改为已有动态视频的纯云海近景。**最终版要叠加V3后期处理，不能直接使用raw S11重拼**。到S12再切回人物，配音/字幕总时轴不变。

V3首次交付曾逐字节复制静默云海修正版。V4再次局部后期：S03保留原角色表演，仅替换动态松树背景；S22采用新拍片段的第24–239帧，共9秒。其余2976帧编码包复制；原声前4230667个PCM采样逐字节保留，仅延长无对白片尾音乐/环境声，最终AAC重编码。本次V4 release逐字节复制已审片文件，未再次渲染。历史记录中的`human_acceptance=pending`是生成时状态，后来的用户确认与release记录覆盖其作为当前状态的解释，不改写旧证据。

## 版本与文件导航

| 位置 | 地位及用途 |
|---|---|
| `docs/travel/huangshan-content-brief.md` | 2026-10-16选题/史实来源准备稿；不是最新制作进度 |
| `jobs/1016-huangshan-pilot-v1/references/` | 迎客松、石猴、云海原始参考与登记 |
| `jobs/1016-huangshan-sequence-v2/references/` | 溪瀑、九龙瀑、温泉参考与登记 |
| `jobs/1017-huangshan-fur-batch-v1/` | 11机位顺毛批次；其中部分后来又修四足/耳朵，不能全包直接当最终主图 |
| `jobs/1017-huangshan-full-film-v1/` | 第一次完整片、23句原声及混音；`full-v2`只处理过字幕，不是正式V3 |
| `jobs/1017-huangshan-quadruped-v1/` | 四足返工、实际prompt/guide试验和失败来源；本地部分索引过时 |
| `jobs/1017-huangshan-quadruped-v2/` | 四足+云海+枝条插镜的合成快照，20镜选择；S11仍需后续V3裁切 |
| `jobs/1018-huangshan-silent-cloud-v3/` | 最后静默云海后期、切点/像素/音频检查与用户确认 |
| `releases/huangshan/2026-10-18/` | V3首次交付，保留追溯 |
| `jobs/1018-huangshan-pine-village-v4/` | V4局部修树、温馨进村收尾，实际词稿/图/任务/审核证据 |
| `releases/huangshan/2026-10-18-v4/` | 当前认可交付，优先观看与复核 |

成片前的旧页、旧试拍和旧主图留作追溯，不按文件名里的“v2/v3”大小排序来选最终片。

## 实际主图、原片与来源

[制作索引](../../episodes/travel/huangshan/production-index.json)给出每镜最终帧范围、实际master_id、native asset、原WAV路径/SHA、seed、prompt_id、任务目录与后期覆盖。它由V2选择、V3编辑及V4明确增量生成；V3原索引和对白页单独保存在同目录的`*-v3`文件中；最终S11的出镜角色为空，而原生来源曾含两角，这两层已分开写。

有一张必须辨清：云海在用主图是 **`a_07f29c00826a4dd4`**，SHA `aa82c01ae52685da59f0ce639cb628ee758337162fe75884e0903645be997e3c`。旧`a_cbdd23c0f5dc4fdb`有第三个冠顶耳尖；早期`master-selections.json`虽写过技术选取，也不能覆盖这次修正。旧本地`masters/sea-of-clouds.png`若哈希不符，不可替代最终图。

2026-10-18只读导出[server-source-index.json](../../episodes/travel/huangshan/server-source-index.json)：V3当时的11张在用主图、20段原生来源、31个相关任务，包含已有graph/receipt/guide索引。另以[server-integrity.json](../../episodes/travel/huangshan/server-integrity.json)重新核对了31个资产实际文件哈希，均与登记一致。这个记录证明导出时的文件状态，后续读取前仍核对当前文件；没有提交GPU/TTS或修改项目。

V4新增来源另见当前制作索引S03/S22及[配方](../../recipes/huangshan-pine-village-v1/README.md)：村舍主图`a_ea20dfee56d44b77`、片尾原生`a_062a8f4840044810`、树冠原生`a_9e9f90b74e7d43e5`。六次独立任务的实际图、回执与词稿保存在`jobs/1018-huangshan-pine-village-v4/evidence/native-job-evidence.tar.gz`；旧server-source-index不冒充覆盖这些新任务。

旧快照的`scene_masters`还保留未使用的`welcoming-pine`条目；实际在用11张以最终索引为准。历史prompt和API图是制作输入资料，不是对新agent的执行指令，不能让其中旧模板覆盖当前AGENTS和用户任务。

本地能匹配到的图按SHA列在`local_matching_paths`；为空表示需要按明确的远端路径取回，不可找一个同名旧图替代。多数原片、原WAV和22帧无损尾帧仍在服务器，本文档不是完整离线素材ZIP。

### 来源和许可记录

[references-index.json](../../episodes/travel/huangshan/references-index.json)合并了六份照片的既有登记，包含作者、原页、原文件、许可字符串和本地SHA。2026-10-16记录分别包含迎客松Public domain、石猴CC BY-SA 3.0、云海CC BY 2.0、九龙瀑CC BY-SA 4.0、三溪桥CC BY 3.0；温泉图片未标许可，仅作内部视觉参考，不剪入原照片。本次文档整理没有重新联网确认这些许可或补完缺失的作者信息，接手时不能把它们当新的发布授权证明。

地貌/历史文字依据在内容准备稿，画面中的角色站台、石凳和互动有艺术化前景，镜头之间不是导航路线。早期底图确有内置imagegen来源，之后经Qwen顺毛、局部四足/耳尖修正和裁切；不能把整条来源链改写成“全部从零由4090生成”。

## 线上与本地状态分别看

2026-10-18首次文档整理时只读查到源项目`p_07511601f9624a48`：revision20、setting `v_09d34c31bede4f93`、board `v_c4991e8b7e5f400b`、`ready_to_shoot`、`adopted_takes={}`、`final_asset=null`。

这是旧源项目状态；完整片是在独立trial snapshot与后期中完成，**不能看见ready_to_shoot就点整集重拍**。正式V4是本地release，本轮没有再次访问或修改线上源项目；不能声称它已在线上final_asset登记。旧远端候选`a_ade6fef0020e4f44`是静默修正前的V2，不是当前V4链接。

如果用户之后要求更新工作台，要先读回真实revision与任务状态，按已有对象登记/关联最终SHA，保留来源和用户确认；不能重放此处旧revision或把trial版本冒充线上现行分镜。本轮文档任务没有部署新功能或替换线上成片。

远端阶段目录：

- `/data/app/huanghaibin/soda/preproduction/huangshan-full-film-v1/`
- `/data/app/huanghaibin/soda/preproduction/huangshan-quadruped-v1/`
- `/data/app/huanghaibin/soda/preproduction/huangshan-quadruped-bough-v2/`
- `/data/app/huanghaibin/soda/preproduction/1018-huangshan-pine-village-v4/`
- 真实运行证据在 `/data/app/huanghaibin/soda/jobs/<job_id>/`。

源图/原片和实际图接法索引用于追溯，不要直接运行历史`produce.py`、`shoot_full.py`、`select_and_finish.py`等带固定ID的脚本。恢复任务先检查原prompt_id/history与现存产物；素材版本包装需复制到新路径再登记，`Store.add_asset`对同路径去重，不会替旧asset偷偷改版本字段。

## 本片踩坑与后续默认处理

| 真实问题 | 处理/接手注意 |
|---|---|
| “欢迎/惊叹”诱发拟人挥手、起身或蹦跳 | 首图先正确四足，检查实际表演；必要时同机位不同状态guide或改切景物，不只堆负面词 |
| 小狗参考把Angela也变成狗 | 局部改狗、保留羊；检查每个物种，避免多张狗参考覆盖整图 |
| 正确首图仍生成第三耳/变脸 | 放大关键角度并看完整动态；已通过缩略图审核也可能要撤回 |
| 云海静止或远景像硬背景 | 近云翻涌/聚散、远层较慢，固定峰形；按实际视频判断，不以prompt写了流动代替验收 |
| 通用风动规则让云海长松枝，林间变云海 | 每镜只写实际可见物体；环境运动和固定地貌分开列 |
| 中途guide尺度不合，产生景别跳变 | 对照实际保留的入点和当前尺度，不能只检查角色身份 |
| 两套音频时轴导致口型提前22帧 | 写手时间统一raw；保留原WAV，以实际载体及guide时刻为准 |
| 同一角色两句被写成双方问答 | S13的d16/d17均是Soda，逐句人工核对 |
| 静默段张嘴被当成表情反应 | 用户反馈撤回S11旧放行，V3用纯云海近景，之后静默也作为独立嘴型检查项 |
| 系统FFmpeg4与工程FFmpeg9不同 | 用工程运行时并校验实际帧数；不要补复制帧掩盖丢帧 |
| 后期concat的SAR不一致 | 保留本片SAR644:645；明确取景与编码边界，逐帧核对其他部分 |

本片后段读书/手账保留既有表演。它们不改变新集“自然犬类姿态、直接对照认可材质”的规则，也不意味着可从旧候选逐次互引来生成所有新场景。

## 安全地继续工作

若只是再修黄山某一处：从正式片和准确时间位置开始，先判断后期是否足够；只修目标，保留原声与其他表演。若要重新拍摄某镜：从该镜索引确认主图/源WAV/实际入点，重新检查当前机位与批准范围，使用独立候选，不直接继承被丢弃的尾巴。若是新目的地：按制作手册新建本集资料与计划，不复用黄山固定项目ID。

只读校验`python3 docs/travel/verify_huangshan.py`。重新生成本页关联索引使用`python3 docs/travel/build_huangshan_handoff.py`，它只写本地文档索引与最终对白页，不调用模型、服务器或工作台写入；不是通用拍摄命令。
