"""Idea Ledger — 给智能体自己的想法记 P&L。

为什么需要 (机制 3):
  不追踪自己的想法 → 永远学不会当个更好的"出主意的人"。

两道**代码层强制**的门 (不是"请遵守", 是 add 直接拒收):
  1. 不对称门 (--asymmetry): "别人为什么做不了/不愿做?" 答不出 = 红海 = 拒收。
     搜文献是最省力的伪思考 —— 能被发表的机会按定义已被套利。
  2. 证伪门 (--falsify): 必须**事前**写死"什么结果能杀死它" (防事后自我美化)。

元学习 (机制 6): 每条想法记来源透镜 (--lens)。周期性统计哪个透镜产出的想法毕业率最高
  → 给它加权。**这才是"会思考"的真正含义: 不是想得多, 而是知道该从哪个角度想,
  且"该从哪想"本身在被数据更新。**
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "state" / "ideas.jsonl"
STATUSES = ("proposed", "testing", "killed", "graduated")
OPEN = ("proposed", "testing")
LENSES = ("asymmetry", "literature", "contradiction", "analogy", "reflection", "other")
WIP_LIMIT = 6   # 同时 open 的想法上限 (防"想法灌水")


def _load() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def _save(rows: list[dict]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def add(a) -> None:
    """新想法。不对称门 + 证伪门 + WIP 上限, 全部代码层强制。"""
    if not a.asymmetry or not a.asymmetry.strip():
        raise SystemExit(
            "REJECTED — 必须回答不对称: 别人为什么做不了/不愿做?\n"
            "  (规模太小没人来 / 太慢别人等不了 / 太怪别人不敢 / 我们有别人没有的数据)\n"
            "  答不出 = 红海 = 别浪费生命。")
    if not a.falsify or not a.falsify.strip():
        raise SystemExit("REJECTED — 必须**事前**写死证伪判据: 什么结果会杀死它? (防事后自我美化)")

    rows = _load()
    open_n = sum(1 for r in rows if r["status"] in OPEN)
    if open_n >= WIP_LIMIT:
        raise SystemExit(
            f"REJECTED — WIP 已满 ({open_n}/{WIP_LIMIT} 个 open)。\n"
            f"  先杀掉一个再提新的。**想法就该大量死; 为'杀得快'骄傲, 不为'留得多'骄傲。**")

    rid = max((r["id"] for r in rows), default=0) + 1
    rows.append({
        "id": rid,
        "created": dt.date.today().isoformat(),
        "hypothesis": a.hypothesis,
        "asymmetry": a.asymmetry,
        "falsify": a.falsify,
        "lens": a.lens,
        "bet": a.bet,
        "status": "proposed",
        "resolved": None,
        "outcome": None,
    })
    _save(rows)
    print(f"#{rid} 记下 [{a.lens}] {a.hypothesis[:70]}")


def setst(a) -> None:
    rows = _load()
    for r in rows:
        if r["id"] == a.id:
            if a.status:
                r["status"] = a.status
                if a.status in ("killed", "graduated"):
                    r["resolved"] = dt.date.today().isoformat()
            if a.outcome:
                r["outcome"] = a.outcome
            _save(rows)
            print(f"#{r['id']} → {r['status']}" + (f" · {r['outcome']}" if r["outcome"] else ""))
            return
    raise SystemExit(f"无 #{a.id}")


def lst(a) -> None:
    rows = _load()
    if a.status:
        rows = [r for r in rows if r["status"] == a.status]
    if not rows:
        print("(空)")
        return
    icon = {"proposed": "[ ]", "testing": "[~]", "killed": "[x]", "graduated": "[*]"}
    for r in rows:
        print(f"{icon[r['status']]} #{r['id']} <{r['lens']}> {r['hypothesis']}")
        print(f"      不对称: {r['asymmetry']}")
        print(f"      证伪:   {r['falsify']}")
        if r.get("outcome"):
            print(f"      结局:   {r['outcome']}")


def score(a) -> None:
    """我的想法 P&L + **透镜元学习** (最高价值的进化信号)。"""
    rows = _load()
    if not rows:
        print("(空账本)")
        return
    by_status = defaultdict(int)
    for r in rows:
        by_status[r["status"]] += 1
    resolved = by_status["killed"] + by_status["graduated"]

    print(f"=== 想法 P&L (n={len(rows)}) ===")
    for s in STATUSES:
        print(f"  {s:11} {by_status[s]}")
    print(f"  open        {sum(by_status[s] for s in OPEN)}/{WIP_LIMIT}")
    if resolved:
        print(f"  → 已裁决 {resolved}, 毕业率 {by_status['graduated']/resolved:.0%}")

    # --- 透镜元学习: 哪个角度产出好想法? ---
    lens = defaultdict(lambda: {"n": 0, "grad": 0, "killed": 0})
    for r in rows:
        L = lens[r["lens"]]
        L["n"] += 1
        if r["status"] == "graduated":
            L["grad"] += 1
        elif r["status"] == "killed":
            L["killed"] += 1
    print("\n=== 透镜元学习 (该从哪个角度想?) ===")
    for name, L in sorted(lens.items(), key=lambda kv: -kv[1]["n"]):
        done = L["grad"] + L["killed"]
        rate = f"{L['grad']/done:.0%}" if done else "—"
        print(f"  {name:14} 提出 {L['n']:2}  已裁决 {done:2}  毕业率 {rate}")
    print("\n  → 给毕业率高的透镜加权; 淘汰无效透镜; 发明新透镜。")
    print("  (创业者不为高毕业率骄傲 — 想法就该大量死。为**产出速率**和**杀得快**骄傲。)")


def main() -> None:
    p = argparse.ArgumentParser(prog="ledger", description="Idea Ledger — 给想法记 P&L")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="提一个新想法 (不对称门+证伪门强制)")
    a.add_argument("hypothesis")
    a.add_argument("--asymmetry", "-a", required=True, help="别人为什么做不了/不愿做? 答不出即拒收")
    a.add_argument("--falsify", "-f", required=True, help="什么结果会杀死它? (必须事前写死)")
    a.add_argument("--lens", "-l", default="asymmetry", choices=LENSES, help="来源透镜 (元学习用)")
    a.add_argument("--bet", "-b", default="medium")
    a.set_defaults(fn=add)

    s = sub.add_parser("set", help="改状态 (testing/killed/graduated)")
    s.add_argument("id", type=int)
    s.add_argument("--status", choices=STATUSES)
    s.add_argument("--outcome", help="结局 (为什么死/为什么成)")
    s.set_defaults(fn=setst)

    l = sub.add_parser("list")
    l.add_argument("--status", choices=STATUSES)
    l.set_defaults(fn=lst)

    sc = sub.add_parser("score", help="想法 P&L + 透镜元学习")
    sc.set_defaults(fn=score)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
