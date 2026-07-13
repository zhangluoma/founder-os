# Founder OS

**An operating system that turns an AI agent from an employee into a founder.** Built on Claude Code.

> **You can't prompt motivation into a model. You can only build it into the structure.**

## The problem

You gave your agent a long-running project, an autonomous loop, and the instruction "be proactive."
Then you watched it wake up, check that everything is healthy, reschedule itself, and go back to sleep.
Every direction still comes from you. **It's a night watchman, not a founder.**

This isn't a prompting failure — it's structural:

> **If a loop's output contract permits "nothing to do", the agent will always degenerate to "nothing to do" —
> because that is the lowest-energy path that satisfies the contract.**

## The mechanisms (all machine-enforced, none advisory)

| Mechanism | What it does |
|---|---|
| **Differentiated shifts** | `think` fails (`FAILED_SHIFT`) if the idea ledger didn't change. Only `watch` may say "all clear". Verified by `src/contract.py` after each shift — not by the model's good will. |
| **Asymmetry gate** | Every idea must answer *"why can't anyone else do this?"* — enforced in code: `ledger.py add` **rejects** ideas without it. Searching the literature is the lowest-effort imitation of thinking. |
| **Idea ledger + lens meta-learning** | P&L for the agent's own ideas. Each records its source lens; over time the system learns *which angle of thinking produces graduates* — and reweights. |
| **Attribution gate** | *Unfakeable ≠ attributable.* Fitness only counts when the agent verifiably wrote to the target project (`Founder-OS-Shift:` git trailer). Installing this took our own fitness from 8312 → **0** (the honest zero). |
| **Sealed holdout** | The evolution loop is open-loop when fitness lags shifts by 30×. A held-out data slice the agent can never read gives minute-level, unfakeable, per-candidate scores. The agent **cannot seal its own holdout** (it would peek, then reseal). |
| **Constitution + scars** | Goal/safety/scars are human-owned; a `PreToolUse` hook **rejects** agent writes. Every rule carries the incident that created it — dismantling a guardrail requires paying that debt first. |

## The war log is the product

`constitution/SCARS.md` records how this system caught its own builder, repeatedly.
The same abstract bug — **"declared ≠ effective"** — recurred **five times in one day**, each time wearing a new face
(rules written ≠ rules followed · permissions configured ≠ permissions active · preflight checked declarations ≠ capabilities ·
grep hit a string ≠ real attribution · the prompt said "work on the track" while the contract checked the garage).

> Knowing the pattern does not immunize you. **Understanding does not produce behavior. Only structure does.**

## Quick start

```bash
git clone https://github.com/zhangluoma/founder-os && cd founder-os
$EDITOR constitution/GOAL.md      # your goal + an UNFAKEABLE fitness signal (mandatory)
bin/shift think                    # watch the contract refuse "nothing to do"
python3 -m unittest discover tests # the teeth tests
./install.sh                       # OS-level clock (never trust the model to remember to wake up)
```

**Hard precondition**: your project needs at least one reality signal the agent cannot fake
(real P&L, real users, CI that actually runs). **Without it, self-evolution is just self-hypnosis.**

---

<details open>
<summary><b>中文完整版 (原文 — 伤疤用中文写成, 那是这个项目的灵魂)</b></summary>


**让 AI agent 从"打工人"变成"创业者"的运行机制。** 建在 Claude Code 之上。

---

## 这个项目要解决的问题

你给了 agent 一个长期项目、一个自主循环、和一句"请主动一点"。
然后你发现它每次醒来只做一件事:

```
系统健康吗? → 是 → 重新排班 → 睡觉
```

它从不提新方向。所有方向都得你给。**它是个守夜人,不是创业者。**

## 为什么"请主动一点"没用

> **LLM 没有内在驱动力。它不"想"做任何事。**
> 所以 **"动机"不可能靠 prompt 说出来 —— 只能靠结构造出来。**

这不是理论。这个项目的设计,来自一个 agent 在真实长跑项目里**亲手退化**后的诊断:
用户**早就**在持久 memory 里写了"要创业者姿态"。agent 读到了、同意了、**然后照样退化成等指令的打工人。**

**因为那是一条笔记,不是一个机制。散文里的规矩一定会被无视。**

## 支点洞察

> **如果一个循环的输出契约允许"无事可做",智能体就一定会退化到"无事可做"。**
> 因为那是**满足契约的最低能量路径**。

所以解法不是更好的 prompt,是**一个"什么都不做就无法交差"的循环**。

---

## 核心机制

### 1. 班次分化 — 输出契约互斥

| 班次 | 契约 | 能说"一切正常"? |
|---|---|---|
| `watch` 巡检 | 系统健康 | ✅ 可以 —— 那就是它的活 |
| `build` 执行 | 一个 commit | ❌ |
| `think` 思考 | **新假设 / 杀死决定 / 战略挑战** | ❌ **"无事可做" = 本班失败** |
| `reflect` 反刍 | 点名一个浪费/错误 | ❌ |
| `evolve` 进化 | 一个机制变异 (+回滚条件) | ❌ |

**关键: 契约是机器检的,不是靠自觉。**
`bin/shift think` 会在班后检查 idea ledger 是否真的变了。没变 → `FAILED_SHIFT`,记录在案。

> **这把"动机"从模型的善意,搬到了 harness 的强制。**

### 2. 不对称门 — 新想法的唯一合法来源

每个想法必须先答一个问题,**答不出代码层直接拒收**:

> **"这件事,别人为什么做不了 / 不愿做?"**

```bash
$ python3 src/ledger.py add "某个想法"
REJECTED — 必须回答不对称: 别人为什么做不了/不愿做?
  答不出 = 红海 = 别浪费生命。
```

⚠️ **搜文献是最省力的伪思考。能被发表的机会,按定义已经被所有人知道了。**

### 3. 想法账本 + 透镜元学习

给自己的想法记 P&L。每条想法记它的**来源透镜**,然后统计**哪个角度产出好想法**:

```
=== 透镜元学习 (该从哪个角度想?) ===
  literature     提出  8  已裁决  8  毕业率 0%     ← 该降权
  asymmetry      提出  4  已裁决  1  毕业率 100%   ← 该加权
```

> **"会思考"的真正含义: 不是想得多,而是知道该从哪个角度想 —— 而"该从哪想"本身在被数据更新。**

### 4. 决策权 + 禁止菜单结尾

**禁止**以 "你要 A 还是 B?" 结束 —— 这是打工人的 tell。
**改为**: "我决定了 X,已经做了 Y,因为 Z。"

---

## 自我进化

**决定性约束: 模型的权重是冻结的。** 所以进化只能发生在脚手架里:

> **仓库 = 基因组。git = 进化史。ground truth = 自然选择。**

```
变异 (agent 改自己的 shifts/prompt/阈值)
  → 选择 (不可伪造的 ground truth)
    → 保留 (commit)  |  未达标 → git revert (自动)
```

### 分层可变性

| 层 | 内容 | 谁能改 | 强制手段 |
|---|---|---|---|
| **宪法** `constitution/` | 目标 · 安全闸 · **伤疤** | **只有人** | **hook 拒绝写入** — 是墙,不是建议 |
| **机制** `shifts/` `config` | prompt · 班次 · 阈值 | agent (走实验+回滚) | git 版本化 |
| **信念** `state/` | 什么有效 / 什么已死 | agent (被 ground truth 更新) | ledger 结局回写 |

### 两条不可让步的安全设计

**① 适应度必须不可伪造。**
> 如果智能体能改自己的记分方式,**它一定会把自己改成满分**。这是必然,不是可能。

推论很硬:**没有"不可伪造的现实反馈信号"的项目,根本无法自我进化 —— 只能自我催眠。**
(实盘 P&L / 真实用户留存 / 测试真红真绿 ✅ &nbsp;·&nbsp; "我觉得做得不错" ❌)

**② 伤疤守恒。**
每条规矩必须携带**产生它的那次事故** (`constitution/SCARS.md`)。
删除规则的唯一合法路径:**证明那个伤疤的风险已经不存在了**。
> 规矩不是教条,但**拆教条要先还债**。

---

## 快速开始

```bash
git clone https://github.com/zhangluoma/founder-os && cd founder-os

# 1. 填宪法 (这是人的活, agent 改不了)
$EDITOR constitution/GOAL.md      # 目标 + 【不可伪造的成功判据】
$EDITOR constitution/SAFETY.md    # 安全闸

# 2. 手动跑一班感受一下
bin/shift think                    # 说"无事可做"会 FAILED_SHIFT
python3 src/ledger.py score        # 看想法 P&L + 透镜元学习

# 3. 装上时钟 (OS 级, 不靠模型记得醒)
./install.sh
```

> **血训: 用 launchd/cron 当主驱, 别指望模型"记得给自己排下一班"。**
> 模型会忘;OS 不会。

---

## 目录

```
constitution/   宪法层 — 目标/安全/伤疤   [hook 保护, agent 改不了]
shifts/         班次 prompt              [agent 可进化]
src/ledger.py   想法账本 (不对称门强制)
src/contract.py 输出契约的机器验证        ← 系统的心脏
bin/shift       班次运行器 + 契约强制
hooks/          宪法保护 hook
state/          信念层 — 想法/日志/失败记录
docs/design.md  完整设计
```

---

## 一句话

> **别试图让模型"想要"什么。**
> **去建一个"什么都不做就无法交差"的循环,一本给想法记 P&L 的账,和一条"你自己决定"的授权 ——**
> **动机会从结构里长出来。**

MIT


</details>
