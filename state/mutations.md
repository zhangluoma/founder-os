# 机制变异记录 (事前判据 + 回滚条件 —— 让机器回滚, 别让自己找理由留下)

## M1 · 2026-07-13 · 归因门 v3: 电平计 → 归因窗 × 基线差分

**改 X**: `bin/fitness-driven-project` + 新 `src/fitness_bridge.py` (逻辑抽成纯函数, 可被牙齿测试咬)。

- 病 (巡检班验尸, state/journal.md 2026-07-13): v2 归因门是电平计 + 一次性保险丝 ——
  一个 trailer commit (代码从没跑过) → 永久 ATTRIBUTABLE=1 → 把赛道**继承净值 $8312.22 整个发给 founder-os**。
  **可归因 ≠ 有效; 接触 ≠ 贡献。**「声明≠有效」第 5 次复发, 长在尺子上。
- 刀 1 (归因窗 30 天, idea #6, 同班并行产出, 已合并): 曾经归因 ≠ 现在归因。窗外 → 0 分。
- 刀 2 (基线差分, 本班): FITNESS = MONEY(now) − MONEY(epoch), epoch = 赛道最早的 trailer commit。
  基线**每次从不可伪造来源现场重算** (净值历史 DB + git 历史快照), 无 seal 文件 = 无篡改面。
- 顺手修的两处「静不吵」: ① 赛道路径信任根改为宪法 (GOAL.local.md), 环境变量降为后备
  (实测 env 被污染成模板占位符, 桥静默输出 "0" —— 会被 `_num` 当成合法读数); ② SHIPPED 基线
  缺失时取当前值 (delta=0, 传感器致盲) 而不是取 0 (会把 epoch 前的 3 个 live 策略记成我们的)。

**事前判据 Y (全部立即可验, 已于 2026-07-13T01:32Z 验收)**:
1. `./bin/fitness-driven-project` 报 FITNESS=0.00 (差分), 不再是 8312.22 (电平)。✅ 实测通过。
2. 无赛道新 commit 时连跑两次输出完全一致 (不可自我刷分)。✅ 实测通过。
3. SHIPPED_DELTA=0 (epoch 前已 live 的 3 个策略不计入)。✅ 实测通过。
4. 牙齿测试 5 条新断言 (tests/test_teeth.py::BaselineDifferencing) 全绿。
   ⚠️ **本班沙箱跑不了 unittest** (`python3 -m unittest` / `./bin/teeth` 均未放行) —— 已写好,
   **未运行**。不假装绿。解封行 (人来加): `"Bash(./bin/teeth)"` 加进 settings 的 allow。
   下一个能跑的班第一件事: `./bin/teeth`, 有红 → 立即修或 revert 本 commit。

**回滚条件 (机器判, 不商量)**:
- 判据 4 跑通之前, 若任何班发现 FITNESS 输出了电平 (≈ MONEY 而非差分) → `git revert` 本 commit。
- 7 天内 (至 2026-07-20) 若 `python3 src/fitness.py record` 因本改动无法记录合法数据点
  (桥 exit≠0 且原因在桥自身 bug) → `git revert` 本 commit。

**度量口径公告 (防止未来班次误裁决)**:
- `state/fitness.jsonl` 中 **ts < 2026-07-13T01:32Z 的点是 v2 电平口径且已被验尸判假** (两个 8312.22)。
- **任何 canary `verdict` 不得跨越该边界比较** —— 跨界比较会把"废掉假分"误读成"fitness 暴跌"而触发假回滚。
- 新口径下 FITNESS 可以为负 (epoch 后净值回撤)。负数是诚实的, 不是故障。

## 待决 · 复杂度棘轮提名 (进化班必答 #3)

**提名该杀: `src/holdout.py` (封存留出, idea #4)。**
- 现状: 84 行, `state/holdout_seal.json` **不存在** → 它从被写下起**一次都没运行过**。
- 它自带事前证伪判据 (对 4 条已裁决想法算分, llm_eq 必须最差, 否则自杀), 但执行它需要
  赛道代码执行权限 —— 与 build 班撞的是同一堵墙。
- **判决线 (事前写死): 2026-07-20 前若仍未产出第一次裁决 → 删除该文件** (一个从不感知的传感器
  = 纯复杂度, 且比没有更糟 —— 它让人以为"我们有留出机制")。解封后若跑了且自杀条件触发 → 也删。
