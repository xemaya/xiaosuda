# 小苏打宇宙 · 当前制作入口

当前内容口径见 **[系列统一口径 V1](docs/series-bible.md)**（2026-10-16）：按新编剧情景剧形式制作，单集含包装不超过5分钟，可分部分；不强制“教→学”或 Practice time!。角色改用正式名 Soda、Jacky、Angela、Dad、Mom、Mimi；栗子为已有保留角色。新版 Mimi 卡已归档，工作台角色库和写手使用同一套口径；Mimi具体声线仍待试听定稿。

历史样片已完成正式交付：**Hi, Soda! EP01 — How are you?**，现作为技术原点，主片仍见 `releases/ep01/current.json` 指向的文件（38.299 秒、1080×1932、24fps）。完整 OP + A 幕间 + 原表演/击掌，用户明确当次“仅成片”；保留历史文件，不占用或约束新情景剧的编号与内容。

动画生成配方和原始表演基线仍为 **v14**，原片及冻结配方继续保留，供下次制作复用。

**默认配方：[毛绒动物对白 v14](recipes/plush-dialogue-v14/README.md)**

```bash
# 从本目录运行；只读校验，无网络或 GPU 操作
python3 recipes/plush-dialogue-v14/verify.py

# 导出可复用的 ComfyUI API 示例图，不提交渲染
python3 recipes/plush-dialogue-v14/continuity.py --out /tmp/new-episode.graph.json
```

当前 S1E01 准备稿见 `episodes/s1e01/`：全景/特写/中景交替，Jacky在旁搭积木，Angela读书；用后期下拉揭幕切换北方冰雪场景。换景别或地点分别做主图，背景活动不等于配角说话。

## 下次制作遵守的核心规则

1. 同一个连续机位共用一张干净高清场景图，固定角色、尺度、背景、光照；角色卡只用于产生这张图。
2. 台词和单句配音先落地，实测时间后再编排动作。现有声线见 `characters.md`。
3. 连续表演能在一次约 10 秒生成内完成，就一次完成；不把多个小镜头拼成 10 秒测试段。
4. 需要接长时，在同一 API 图内继承上一段真正被保留的最后 22 帧未压缩画面；不接旧音频或 AV latent。
5. 每段载体只用高清主图和本段对白，384×688、24fps。续接载体先加 22 帧对应的静音，出片后裁掉画面头部上下文。
6. `audio_context_length=0` 不等于关闭音频。准确接线和帧数计算以配方里的 `continuity.py` 为准。
7. 不复制末帧补尾、不用静帧凑时长；下一段不能继承上一段已被裁掉的额外尾巴。
8. 生成、剪辑、字幕、交付统一 CFR24。默认交付 1080×1932；字幕本地渲染。
9. 看完整成片与每个接点，检查镜内换构图、静帧、纹理/角色漂移和说话口型。像素差与抽帧不能代替观看验收。

模型、LoRA、CLIP、双 VAE、seed 示例、首段与接续图、运行时源码、字体及校验清单均在配方目录。
实际出片仍使用现有自部署 H3、4 steps、euler/beta；无需改共享服务器节点或训练模型。

## 已认可的证据

- [v14 完整成片](jobs/1015-v14-native-continuity/xiaosuda-how-are-you-v14-review.mp4)
- [v14 制作记录](jobs/1015-v14-native-continuity/README.md)
- [可复用配方](recipes/plush-dialogue-v14/README.md)
- [冻结参数](recipes/plush-dialogue-v14/recipe.json)

## 历史样片优化记录

用户明确决定回到 v14。v15/v16 的重新生成路径已放弃：v15 说话角色错误，v16 丢失末尾击掌。只替换 v14 教→学的上滑转场，保留全部已认可表演，使用约 1 秒的 **Practice time!** 幕间卡。

通用幕间卡：`assets/intertitles/practice-time.png`，米色绒面底、蓝黄毛绒布艺字和通用爪印，不含角色及场景，后续各集复用。内置 imagegen 生成，提示词见同目录 `.prompt.txt`。新版本在 `jobs/1015-v17-practice-intertitle/`，无任何新生成视频。仅插入幕间停顿，并同步后移练习音轨/字幕，台词和原始动作不变。v14 保持已验收基线。

用户新增要求对比三种幕间动效：A 爪印回弹、B 布艺翻页、C 针脚画圈。母版在 `assets/intertitles/motion/`（ProRes 4444 透明通道、各 32 帧/24fps），三份完整视频与 7.5 秒并排预览在 `jobs/1015-v18-intertitle-motion/`。没有重新生成动物视频。用户已选 **A 爪印回弹** 为默认幕间，选择与母版/成片哈希记录在 `assets/intertitles/motion/default.json`。当前选定剪辑为 `jobs/1015-v18-intertitle-motion/v18-a-paw-pop-review.mp4`；v14 仍为已验收的动画生成配方和原始表演基线。


OP 已确定标题 **Hi, Soda!**，无副标题，计划 2 秒，沿用 A 幕间的毛绒布艺字风格，不含角色和场景。首版静态主画面已生成并保存到 `assets/op/hi-soda-v1.png`，提示词与结果记录在 `jobs/1015-op-hi-soda/`；静态图已获认可，两秒 OP 动效已完成，MP4 和 ProRes 4444 透明母版位于 `assets/op/hi-soda-motion/`，48 帧/24fps，沿用 A 的爪印与文字回弹；动画已获用户认可，并与 A 版正片无重编码拼接成正式交付。原素材和历史版继续保留。

## 剧本工作台

**入口：https://soda.buplayground.cn/**，沿用现有 buplayground 登录。代码与操作说明见 `workbench/README.md`。

当前已部署工作台支持粘贴及批量 TXT / MD / JSON 导入，按 **剧本 → 剧情设定（人物、场景、对白）→ 分镜 → 拍摄/采用/合成** 推进。后端固定七个角色、毛绒画风与 v14 配方，采用新正式名与旧称映射；单集含包装不超过5分钟，OP可复用，A幕间按剧情选用。栗子的配音仍待定，不临时冒用他人声线。

工作台有独立数据库、文字/GPU任务队列和版本记录。每阶段先检查确认，主图及镜头候选不自动采用。原第一集保持只读参考，Short Video 旧站未修改。真实验收示例位于工作台作品列表，完整输入、模型回执、5秒原生片段和含OP的7秒成片均已保留；证据见 `workbench/evidence/live-e2e.json` 与 `validation-summary.json`。

## 历史材料

旧 v12 的配方和失败记录继续保留，便于追溯；旧文件中的静帧补尾、AV latent 续接和跨机位关键帧接法不再作为默认做法。

- [v12 冻结配方](recipes/ep01-v12/README.md)
- [v13 否决记录](jobs/1015-v13-continuity-experiment/README.md)
- [v14 前的完整流程存档](docs/history/WORKFLOW-before-v14-promotion-20261015.md)
