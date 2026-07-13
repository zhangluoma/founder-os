"""封存留出 (Sealed Holdout) — 闭合开环的进化环。 (idea #4, 由系统自己的思考班挖出)

**它诊断出的病** (我没看见):
  GOAL 的两个数都是**月级延迟** (SHIPPED 需 28 天前向, MONEY canary ≥30 天),
  而班次是**天级** —— **执行器比传感器快 30 倍, 进化环是开环的。**
  一个开环的进化系统, 变异是随机漂移, 不是进化。

**补救不是加纪律, 是造第三个数**:
  赛道历史数据切一片 → **hook 强制 agent 永远读不到** →
  候选策略在这片上的分数: **分钟级可算 · 不可伪造 (没见过就过拟合不了) · 可归因 (逐候选)**。
  **这是 Kaggle 私榜, 装在自举环里。**

**它的不对称论证 (为什么全世界没人这么做)**:
  "封存留出**纯粹是下行**: 缩小可用数据、压低报告 Sharpe、一旦偷看就永久烧毁。
   任何一个业绩排第一的研究者/机构都没有动机自砍数据。
   更根本: **一个用 fitness 决定自己变异去留的 agent, 绝不会自愿装一个只会拉低自己分数的传感器。**
   这需要一部把'诚实高于业绩'排在业绩之上、且把'想法大量死'定义为成功的宪法。"

  并点破整个领域的盲区:
  "所有在 instant-oracle 基准 (SWE-bench 等) 上评测的 agent 框架, **结构性地永远撞不到这个问题**
   —— 他们的预言机免费且瞬时, 所以从不知道真实世界的适应度信号是**延迟受限**的。"

**它自己写的证伪判据 (天级, 立刻可跑)**:
  对 registry 里**已裁决**的 4 条算封存留出分。若该分数**排不开**过门组 (eth/btcgold/spy_night)
  与证否组 (llm_eq) —— 即 llm_eq 不是最差 —— **则它是个伪装成传感器的谎言 → 立刻杀。**
  诚实声明: n=4 **只够杀, 不够祝福**。(证伪快, 验证慢 —— 这恰是本想法自己的论点。)
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "state" / "holdout_seal.json"


def _target() -> Path:
    goal = (ROOT / "constitution" / "GOAL.md").read_text()
    for line in goal.splitlines():
        if line.startswith("FOUNDER_TARGET="):
            return Path(line.split("=", 1)[1].strip())
    return Path(os.environ.get("FOUNDER_TARGET", ""))


def seal(cutoff: str) -> dict:
    """封存: cutoff 之后的赛道数据 = 私榜。**只有人能封, agent 不能自己重封** (否则它会偷看后重封)。

    封存记录进 state/holdout_seal.json 并 commit —— **一旦封存, 篡改会留在 git 里。**
    """
    rec = {
        "cutoff": cutoff,
        "sealed_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(timespec="seconds"),
        "note": "cutoff 之后的赛道数据 = 私榜。agent 的研究代码永远不许读。偷看即永久烧毁。",
    }
    rec["seal_hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()[:16]
    SEAL.parent.mkdir(parents=True, exist_ok=True)
    SEAL.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def status() -> str:
    if not SEAL.exists():
        return ("**未封存** —— 进化环仍是开环的 (执行器天级 / 传感器月级, 快30倍)。\n"
                "  封存是**人的活** (agent 不能自己封, 否则它会偷看后重封):\n"
                "    python3 src/holdout.py seal <cutoff日期>")
    r = json.loads(SEAL.read_text())
    return (f"已封存 · cutoff={r['cutoff']} · seal={r['seal_hash']}\n"
            f"  **{r['cutoff']} 之后的赛道数据 = 私榜。研究代码读到它 = 永久烧毁。**")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "seal":
        if os.environ.get("FOUNDER_HUMAN") != "1":
            raise SystemExit(
                "**拒绝** —— 封存是人的活。\n"
                "  一个能自己重封留出的 agent, 会先偷看再重封。**它必须封不了自己的私榜。**\n"
                "  人执行: FOUNDER_HUMAN=1 python3 src/holdout.py seal <cutoff>")
        print(json.dumps(seal(sys.argv[2]), ensure_ascii=False, indent=1))
    else:
        print(status())
