"""适应度桥 v3 — 归因门从「电平计」改成「基线差分」。

**v2 的病** (state/journal.md 2026-07-13 巡检班验尸, 本班动刀):
  v2 只查「历史上存在过一个 trailer commit 吗」(`git log -n 1`), 存在 → 把赛道的
  **全部继承净值** ($8312.22) 一次性发给 founder-os。
  一份从没运行过的代码 + 一个 trailer = 满分。

  > **归因门测的是「我碰过赛道」, 不是「赛道变好了」。它把接触当成了贡献。**

  这是「声明≠有效」的又一次复发 (第五次), 而这次长在**尺子自己**身上:
    · SCARS #1  规矩写了      ≠ 被遵守
    · GOAL §2   数字不可伪造  ≠ 可归因于我
    · SCARS #5  权限写了      ≠ 真生效
    · preflight 检查了声明    ≠ 检查了有效能力
    · fitness   **可归因**    ≠ **有效贡献**   ← 本文件修的就是这个

**v3 是两刀, 各治一半** (同班合并; 归因窗出自 idea #6):
  1. **归因窗 (30 天)**: v2 是一次性保险丝 —— 一个 trailer 永久点亮 ATTRIBUTABLE,
     传感器在第一次归因后失去全部分辨力。**曾经归因 ≠ 现在归因。**
     窗宽继承 GOAL §2.1 的 MONEY canary 窗 (≥30 天), 不是新的自由参数。
     窗决定「**发不发**分」— 只可能把 1 变 0, 严格更苛。
  2. **基线差分**: 你的分数从你第一次碰赛道那一刻起算, 且**从 0 起算**。
     FITNESS = MONEY(now) − MONEY(epoch),  epoch = 最早的 trailer commit 时刻。
     接触本身发 0 分; 只有接触之后的变化才计入。**继承的历史不是你的。**
     差分决定「发**多少**」分。

**为什么不用 seal 文件存基线** (显然的实现被否决的理由):
  state/ 不入 git。一个可删可改的基线文件 = 给未来的自己留一个刷分口子
  (净值跌了 → 删 seal → 低位重封 → 亏损清零)。
  所以基线**每次现场重算**, 全部取自 agent 改不了的来源:
    · epoch: 赛道 git 里最早的 trailer commit (归因的信任根, 本来就在用)
    · MONEY 基线: 交易所记录的净值历史里 epoch 当天(或之前最近)的值
    · SHIPPED 基线: `git show <epoch>:data/strategy_registry.json` (历史快照, 改不了)
  无状态 → 无 seal → 无篡改面。

**fail closed**: 归因成立但基线算不出 (净值历史为空等) → 响亮地拒绝发分 (exit 3),
  不发电平、不发 0 分假装没事。「失败要吵, 不要静。」

**诚实的局限** (别假装没有):
  · 差分仍被 beta 污染 —— epoch 后 BTC 涨, delta 也涨。这不是本次修的病
    (GOAL 已声明: MONEY 短期=噪声, canary ≥30 天)。本次只修「继承电平被当成贡献」。
  · trailer 仍只证明「碰过」。一个无效 commit 在 v3 下拿 0 分而不是满分 ——
    病没根除, 但毒性从「满分」降到「零分」。
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def count_live(reg: dict) -> int:
    """SHIPPED 口径: registry 里 status 以 live 开头的策略数。"""
    return sum(1 for v in reg.values()
               if isinstance(v, dict) and str(v.get("status", "")).startswith("live"))


def compute(money_now: float, shipped_now: int,
            anchor: str | None, fresh: bool,
            base_money: float | None, base_shipped: int | None) -> dict:
    """纯函数: 该发多少分。牙齿测试咬的就是这里。

    规则 (事前写死):
      从未归因 (无 anchor)      → FITNESS 0 (同 v2)
      归因过但 30 天窗外 (不 fresh) → FITNESS 0 (idea #6: 曾经归因 ≠ 现在归因)
      fresh + 基线可算          → FITNESS = money_now − base_money (差分, 不是电平)
      fresh + 基线算不出        → RuntimeError (调用层必须 exit 非零; 禁止静默发分)
    """
    if not anchor or not fresh:
        return {"attributable": 0, "fitness": 0.0,
                "money_delta": 0.0, "shipped_delta": 0}
    if base_money is None:
        raise RuntimeError(
            "归因成立但 MONEY 基线不可算 — 拒绝发分 (fail closed)。\n"
            "  发电平 = 把继承当贡献; 发 0 = 把故障当清白。两个都是谎。")
    return {
        "attributable": 1,
        "fitness": money_now - base_money,
        "money_delta": money_now - base_money,
        "shipped_delta": shipped_now - (base_shipped or 0),
    }


# ---------- IO 层 (从不可伪造来源取数) ----------

def _git(target: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=target,
                       capture_output=True, text=True, timeout=20)
    return r.stdout.strip() if r.returncode == 0 else ""


def read_money(target: Path) -> float:
    """MONEY: 交易所 API 记录的真钱净值。"""
    try:
        c = sqlite3.connect(target / "data" / "oil_indicators.db")
        r = c.execute("SELECT value FROM indicators WHERE indicator='networth_usd' "
                      "ORDER BY period_date DESC LIMIT 1").fetchone()
        c.close()
        return float(r[0]) if r else 0.0
    except Exception:
        return 0.0


def read_shipped(target: Path) -> int:
    """SHIPPED: 过了 28 天前向门的 live 策略数。"""
    try:
        return count_live(json.loads(
            (target / "data" / "strategy_registry.json").read_text()))
    except Exception:
        return 0


def find_anchor(target: Path) -> str | None:
    """归因锚 (基线的 epoch): 赛道里**最早**的 Founder-OS-Shift trailer commit。"""
    out = _git(target, "log", "--grep=^Founder-OS-Shift:", "--extended-regexp",
               "--reverse", "--format=%H")
    return out.splitlines()[0] if out else None


def is_fresh(target: Path) -> bool:
    """归因窗 (idea #6): 近 30 天内有 trailer commit 吗? 窗外 = 归因已过期。"""
    return bool(_git(target, "log", "--grep=^Founder-OS-Shift:", "--extended-regexp",
                     "--since=30 days ago", "--format=%H", "-n", "1"))


def baseline_money(target: Path, epoch_day: str) -> tuple[float | None, str]:
    """epoch 当天(或之前最近)的净值。没有更早记录 → 用最早一条 (保守, 响亮标注)。"""
    try:
        c = sqlite3.connect(target / "data" / "oil_indicators.db")
        r = c.execute("SELECT value FROM indicators WHERE indicator='networth_usd' "
                      "AND substr(period_date,1,10) <= ? "
                      "ORDER BY period_date DESC LIMIT 1", (epoch_day,)).fetchone()
        if r:
            c.close()
            return float(r[0]), "at-epoch"
        r = c.execute("SELECT value FROM indicators WHERE indicator='networth_usd' "
                      "ORDER BY period_date ASC LIMIT 1").fetchone()
        c.close()
        return (float(r[0]), "earliest-after-epoch") if r else (None, "no-history")
    except Exception:
        return None, "db-error"


def baseline_shipped(target: Path, anchor: str) -> int | None:
    """epoch 时刻的 registry 快照 (git 历史, 改不了)。"""
    txt = _git(target, "show", f"{anchor}:data/strategy_registry.json")
    if not txt:
        return None
    try:
        return count_live(json.loads(txt))
    except Exception:
        return None


def main() -> None:
    target = Path(sys.argv[1])
    money, shipped = read_money(target), read_shipped(target)
    anchor = find_anchor(target)
    fresh = is_fresh(target) if anchor else False

    base_m, base_src, base_s, epoch_day = None, "", None, ""
    if anchor and fresh:
        epoch_day = _git(target, "show", "-s", "--format=%cs", anchor)
        base_m, base_src = baseline_money(target, epoch_day)
        base_s = baseline_shipped(target, anchor)

    print(f"SHIPPED={shipped}")
    print(f"MONEY={money:.2f}")
    print(f"ATTRIBUTABLE={1 if (anchor and fresh) else 0}")

    if not anchor:
        print("# ⚠️ 归因门: founder-os 从未写入赛道 → 上面两个数**不可归因于我们**")
        print("#    它们测的是赛道自己过去的活 + BTC 价格。**进化班不许用它们判断变异去留。**")
        print("#    诚实的 founder-os 贡献 = 0")
        print("FITNESS=0.00")
        return
    if not fresh:
        print("# ⚠️ 归因窗: founder-os 近 30 天未写入赛道 → 归因已过期 (曾经归因 ≠ 现在归因)")
        print("#    诚实的 founder-os 当期贡献 = 0")
        print("FITNESS=0.00")
        return

    shipped_blind = base_s is None
    if shipped_blind:
        # 拿不准 → 少发分, 不是多发。基线取当前值 = SHIPPED 传感器暂时致盲 (delta 恒 0),
        # 但绝不把 epoch 前就 live 的策略记成我们的产出。宁可瞎, 不可谄。
        base_s = shipped

    try:
        res = compute(money, shipped, anchor, fresh, base_m, base_s)
    except RuntimeError as e:
        print(f"# 🛑 {e}", file=sys.stderr)
        raise SystemExit(3)

    if shipped_blind:
        print("# ⚠️ epoch 时刻无 registry 快照 (registry 不在赛道 git 里?) → SHIPPED 基线取当前值,")
        print("#    SHIPPED_DELTA 传感器致盲 (恒 0)。解法: 把 data/strategy_registry.json 纳入赛道 git。")
    print(f"# epoch: {epoch_day} @ {anchor[:12]} (最早 trailer commit; 基线={base_m:.2f}, {base_src})")
    if base_src != "at-epoch":
        print(f"# ⚠️ 基线口径降级: {base_src} — epoch 之前没有净值记录, 用了最早可得的一条")
    print("# FITNESS = MONEY(now) − MONEY(epoch)。继承的电平不是贡献; 接触本身 = 0 分。")
    print(f"SHIPPED_DELTA={res['shipped_delta']}")
    print(f"FITNESS={res['fitness']:.2f}")


if __name__ == "__main__":
    main()
