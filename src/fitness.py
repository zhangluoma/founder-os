"""适应度 — 不可伪造的 ground truth (自我进化的自然选择压力)。

**为什么这是命门**:
  如果智能体能改自己的记分方式, **它一定会把自己改成满分**。这是必然, 不是可能 (Goodhart)。
  所以适应度必须是 **agent 改不了、也骗不了**的外部现实。

**检验法**: "agent 能靠自我欺骗让这个数字变好吗?" 能 → 这个判据废了。

本模块:
  1. 从 constitution/GOAL.md 读 FITNESS_CMD (**宪法层, hook 保护, agent 改不了**)
  2. 跑它, 记录数字到 state/fitness.jsonl (append-only)
  3. 供进化班判断: 我上次的机制变异, 让这个数字变好了吗?

**推论 (硬)**: 没有可执行的 FITNESS_CMD 的项目, **无法自我进化 —— 只能自我催眠。**

用法:
  python3 src/fitness.py record          # 跑一次判据, 记一个点
  python3 src/fitness.py trend [--days N] # 看走势 (进化班用)
  python3 src/fitness.py verdict <since>  # 某次变异后, 判据变好了吗? (canary 裁决)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOAL = (ROOT / "constitution" / "GOAL.local.md"
        if (ROOT / "constitution" / "GOAL.local.md").exists()
        else ROOT / "constitution" / "GOAL.md")
HIST = ROOT / "state" / "fitness.jsonl"


def read_config() -> tuple[str | None, bool]:
    """从宪法读 FITNESS_CMD + 方向。agent 改不了这里 (hook 挡)。"""
    if not GOAL.exists():
        return None, True
    text = GOAL.read_text()
    m = re.search(r"^FITNESS_CMD=(.*)$", text, re.M)
    cmd = m.group(1).strip() if m else None
    if cmd in ("", "（填写, 没有就留空）", "(填写, 没有就留空)"):
        cmd = None
    d = re.search(r"^FITNESS_DIRECTION=(\w+)$", text, re.M)
    higher_better = (d.group(1).strip().lower() != "lower") if d else True
    return cmd, higher_better


def _num(s: str) -> float | None:
    """从命令输出里抠出一个数 (最后一个数字)。"""
    nums = re.findall(r"-?\d+\.?\d*", s)
    return float(nums[-1]) if nums else None


def record(_args) -> None:
    cmd, _ = read_config()
    if not cmd:
        raise SystemExit(
            "constitution/GOAL.md 里没有 FITNESS_CMD。\n"
            "  **没有不可伪造的现实反馈信号 → 无法自我进化, 只能自我催眠。**\n"
            "  去填它 (这是人的活, agent 被 hook 挡住)。")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, timeout=600)
    val = _num(r.stdout.strip() or r.stderr.strip())
    rec = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "value": val,
        "rc": r.returncode,
        "raw": (r.stdout.strip() or r.stderr.strip())[:200],
    }
    HIST.parent.mkdir(parents=True, exist_ok=True)
    with HIST.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[fitness] {rec['ts']}  value={val}  (rc={r.returncode})")


def _load() -> list[dict]:
    if not HIST.exists():
        return []
    return [json.loads(l) for l in HIST.read_text().splitlines() if l.strip()]


def trend(args) -> None:
    rows = [r for r in _load() if r.get("value") is not None]
    if not rows:
        print("(还没有 fitness 数据点 — 先 `python3 src/fitness.py record`)")
        return
    _, higher = read_config()
    rows = rows[-args.n:]
    first, last = rows[0]["value"], rows[-1]["value"]
    delta = last - first
    good = (delta > 0) if higher else (delta < 0)
    arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
    print(f"=== 适应度走势 (最近 {len(rows)} 点) ===")
    for r in rows[-10:]:
        print(f"  {r['ts'][:16]}  {r['value']}")
    verdict = "变好 ✓" if good else ("变差 ⚠️" if delta else "持平")
    print(f"\n  {first} {arrow} {last}   (Δ{delta:+g})  → {verdict}")
    print(f"  方向: {'越大越好' if higher else '越小越好'}")


def verdict(args) -> None:
    """canary 裁决: 某个时间点之后, 判据变好了吗? → 进化班据此决定保留/回滚。"""
    rows = [r for r in _load() if r.get("value") is not None]
    before = [r for r in rows if r["ts"] < args.since]
    after = [r for r in rows if r["ts"] >= args.since]
    if not before or not after:
        print(f"INSUFFICIENT — 变异前 {len(before)} 点 / 变异后 {len(after)} 点, 数据不足以裁决。")
        raise SystemExit(2)
    _, higher = read_config()
    b = sum(r["value"] for r in before[-5:]) / len(before[-5:])
    a = sum(r["value"] for r in after) / len(after)
    improved = (a > b) if higher else (a < b)
    print(f"变异前均值 {b:g} → 变异后均值 {a:g}")
    if improved:
        print("PASS — 判据改善, 保留这次变异 (commit)。")
        raise SystemExit(0)
    print("FAIL — 判据未改善。**自动回滚** (git revert), 不要给自己找理由留下。")
    raise SystemExit(1)


def main() -> None:
    p = argparse.ArgumentParser(prog="fitness", description="不可伪造的 ground truth")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("record").set_defaults(fn=record)
    t = sub.add_parser("trend"); t.add_argument("-n", type=int, default=30); t.set_defaults(fn=trend)
    v = sub.add_parser("verdict"); v.add_argument("since", help="变异时刻 ISO, 如 2026-07-12T10:00:00+00:00")
    v.set_defaults(fn=verdict)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
