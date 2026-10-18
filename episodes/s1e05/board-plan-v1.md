# S1E05 分镜准备 V1（学会分享）

配音前的估算分镜：20 段、约 2 分 12 秒（3177 帧含 2 秒 OP）。**秒数是估计值**，等 40 句原声实测后按真实秒数重算成 `board-v1.json`，以执行图为准。

| 段 | 机位 | 计划窗口 | 对白 | 主要动作 |
|---|---|---:|---|---|
| S01 | `park-lawn-wide` | 3.5 秒 | d1 Soda | 三人站定，Soda 捧起红球给两人看，Jacky、Mimi 都看向球 |
| S02 | `ball-play-medium` | 8.2 秒 | d2 Jacky / d3 Soda / d4 Jacky | Jacky 前倾问能不能玩，Soda 把球递过去，Jacky 小跳道谢 |
| S03 | `ball-play-medium` · 续 | 8.1 秒 | d5 Mimi / d6 Jacky | Mimi 举前爪问能不能轮到她，Jacky 用翅手在两人之间一比 |
| S04 | `ball-play-medium` | 7.2 秒 | d7 Mimi / d8 Soda | Mimi 小心伸爪碰球，Soda 点头 |
| S05 | `ball-play-medium` · 续 | 8.3 秒 | d9 Mimi / d10 Jacky | Mimi 低头把球滚出去，Jacky 側身问「玩好能给我吗」 |
| S06 | `ball-play-medium` | 8.1 秒 | d11 Mimi / d12 Jacky / d13 Mimi | Mimi 再滚一次，Jacky 坐下等，Mimi 把球推给他 |
| S07 | `ball-play-medium` · 续 | 4.6 秒 | d14 Jacky / d15 Soda | Jacky 挺起胸道谢，Soda 看一眼两人再开口 |
| S08 | `ball-play-medium` · 续 | 6.3 秒 | d16 Mimi | Mimi 认真说完「不用所有东西同时玩」 |
| S09 | `ball-play-medium` | 6.1 秒 | d17 Jacky / d18 Soda | Jacky 补一句耐心等，Soda 点头收束第二段落 |
| S10 | `picnic-blanket-medium` | 9.0 秒 | d19 Jacky / d20 Mimi / d21 Soda | Jacky 打开铁盒，Mimi 探头闻，Soda 问能不能分 |
| S11 | `picnic-blanket-medium` · 续 | 7.2 秒 | d22 Jacky / d23 Mimi | Jacky 把盒子往前推，Mimi 尾巴翘起 |
| S12 | `picnic-blanket-medium` | 7.5 秒 | d24 Soda / d25 Mimi | Soda 用前爪推一块饼干给 Mimi，Mimi 也推一块回来 |
| S13 | `picnic-blanket-medium` · 续 | 6.9 秒 | d26 Jacky / d27 Soda | Jacky 盖一下盒子留一点，Soda 点头 |
| S14 | `picnic-blanket-medium` | 6.6 秒 | d28 Mimi / d29 Jacky | Mimi 说完分享的快乐，Jacky 接一句总结 |
| S15 | `blocks-lawn-wide` | 9.8 秒 | d30 Jacky / d31 Mimi | 积木塔已倒，Jacky 低头难过，Mimi 立刻凑近要帮 |
| S16 | `blocks-lawn-wide` · 续 | 8.0 秒 | d32 Soda / d33 Jacky | Soda 从左侧跑来一起收拾，Jacky 抬头道谢 |
| S17 | `blocks-lawn-wide` · 续 | 6.0 秒 | d34 Mimi / d35 Soda | Mimi 举一块积木说朋友互相帮忙，Soda 举起最后一块 |
| S18 | `blocks-lawn-close` | 6.0 秒 | d36 Jacky / d37 Mimi | 近景：Jacky 把积木放回塔，Mimi 也放下一块 |
| S19 | `park-lawn-wide` | 6.8 秒 | d38 Soda / d39 Jacky | 回到开场全景，Soda 说「有你们这样的朋友真开心」，Jacky 接话 |
| S20 | `park-lawn-wide` · 续 | 4.7 秒 | d40 Mimi | Mimi 说完，三人一起欢呼拍手收尾（无台词，约 1.2 秒） |

## 场景与机位预算

一个公园、五个机位（理由见 `script.md`）：球（`ball-play-medium`，8 段）、点心（`picnic-blanket-medium`，5 段）、积木（`blocks-lawn-wide` 3 段 + `blocks-lawn-close` 1 段）、开场与结尾共用 `park-lawn-wide`（3 段）。

续接只用 22 帧纯画面接法，且**每段续接都接在上一段的实际采用末尾**：S03←S02、S05←S04、S07←S06、S08←S07、S11←S10、S13←S12、S16←S15、S17←S16、S20←S19。其余是换机位或换段的直接剪接。

## 逐镜验收重点

1. **身高三档**：Jacky > Soda > Mimi；Mimi 头顶（不含耳尖）不得高过 Soda。
2. **三种结构**：犬四足、鸡双足、猫四足；谁都不许拟人直立、不出现人手。
3. **口型归属**：每句只核对一个人动嘴，其余闭嘴；三人同框时容易看错，逐句放大核对。
4. **道具连续性**：红球在谁那里、饼干盒开合、积木数量与位置，逐段对得上；球不穿模、积木不悬空。
5. **接缝**：九处 22 帧续接逐处比对上一段末帧，位置、光向、道具不跳变。

## 拍摄批次建议

- 批次 A：S01–S09（红球段落，9 段）
- 批次 B：S10–S14（点心段落，5 段）
- 批次 C：S15–S20（积木段落与结尾，6 段）

每批拍完逐镜审核、采用，再进下一批；最后一次性合成整集。

## 待办

1. 用户确认本制作稿与分镜（40 句、五个机位、20 段、约 2 分 12 秒）。
2. 确认后先出一张代表样图（建议 S02 中景：三人围着红球），核对身高三档、道具与材质。
3. 三张以上主图确认 → 40 句原声实测 → 重算 `board-v1.json` → 分批拍摄 → 逐句口型审核 → 合成 → 验收归档。
