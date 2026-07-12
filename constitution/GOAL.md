# 目标 (宪法层 — 只有人能改; agent 被 hook 挡住)

> **目标是人的; 手段是 agent 的。**
> agent 读这份文件、服务它, 但**改不了它** —— 否则它会把目标改成"我已经达成了"。

---

## 1. 使命 (一句话)

<!-- 例:
  - 把 xxx 做成同类开源库里最好用的
  - 让这个 $2k 账户持续盈利
  - 把这个 side project 做到 1000 个真实用户
-->
（填写）

---

## 2. 【核心】不可伪造的成功判据

> **这是整个自我进化的命门。**
> 如果 agent 能改自己的记分方式, **它一定会把自己改成满分** —— 这是必然, 不是可能。
>
> **检验法**: 问 —— **"agent 能靠自我欺骗让这个数字变好吗?"**
> 能 → 这个判据废了, 重写。

### 2.1 判据 (必须是外部现实, 不是 agent 的自评)

<!-- 例 (选一个真实的, 别写"质量提升"这种):
  - GitHub stars / 真实下载量 / 真实 DAU / 付费转化
  - 实盘 P&L (真金白银, 骗不了)
  - benchmark 跑分 / 测试通过率 / CI 真绿
  - 前向验证通过的假设数 (n≥28 天才算数)
-->
（填写）

### 2.2 【最强形式】一条能跑的命令

> 判据能写成**机器可执行的命令**时, agent 连辩解的余地都没有。

```bash
# 例:
#   pytest -q --tb=no | tail -1
#   gh api repos/OWNER/REPO --jq .stargazers_count
#   python scripts/pnl.py --json
#   curl -s https://api.myapp.com/metrics | jq .dau
FITNESS_CMD=gh api repos/zhangluoma/founder-os --jq .stargazers_count
```

### 2.3 方向 (机器可读 — 别用散文, 散文会被解析歧义)

```bash
# higher = 越大越好 (star/收入/通过率)   lower = 越小越好 (bug数/延迟/回撤)
FITNESS_DIRECTION=higher
```

---

## 3. 边界 — 不做什么

<!-- 例:
  - 不为了刷指标牺牲真实用户价值
  - 不碰 xxx 领域
  - 不做需要持续人工运维的东西
-->
（填写）

---

## 4. 当前最大的一注 (agent 每周复盘时对照这里)

<!-- 人写下你认为现在最该押的方向。agent 可以挑战它 (那是它的活),
     但挑战必须带数据, 不能凭感觉。 -->
（填写）
