"""墙账本 — 把「人」这个最慢的组件也拉进机制。 (idea #7)

**这个文件的作者其实是 agent, 不是我。**
思考班 #3 不但诊断出了洞, 还**自己发明了账本格式并登记了第一堵墙** (state/walls.jsonl #1)。
我后来写了一版 walls.py, 用了**我自己的字段名** —— 于是把它的记录当成"格式错误的旧行"崩了,
还另开一条重复的墙。**我读了它的散文, 没读它的数据。** 「声明≠有效」的第 8 张脸。
所以本模块用**它的 schema** (unblock_one_line / blocked_output / hit_log)。它的更好:
每次撞击都带**班次与情形**, 解封行是**可复制粘贴的一行**。

**它的指控** (原文, 有证据):
  "系统对「人」零机制: 班次撞权限墙后, 解封动作 (往往**一行配置**) 只能写进 journal 散文
   → **人不读** → **墙跨班存活**。
   实证: idea #5 的解封行由执行班#1 写进 journal, **至今未被加上**,
   本班**第 3 次**撞同一堵墙, 装置继续**零运行**。"

  而那个装置跑起来的第一件事, 是打穿了实盘的毕业证据 (REAL-HOLE)。
  **一行权限, 挡了一个能救命的发现三次。**

**两个必须分开的东西**:

    FAILED_SHIFT 会把「**我被封口了**」错记成「**我偷懒了**」。
    → 系统于是朝**加压**的方向走 (契约更严/提醒更多), **而墙永远不被修。**

  **WALL** (墙): agent 想干, 但**没有合法路径**。**解法在人手里** (通常一行配置)。加压无用。
  **LAZY** (懒): agent 有路径, 但没干。**解法在契约里**。加压有用。

**机制**: 撞墙**机器可读地登记** (不是散文, 人不读散文 —— 已证)。
  系统入口 (preflight, 每班必经) **响亮展示未拆的墙**, 按撞击次数排序。

**agent 自己写死的证伪判据** (3 天内可裁):
  ① 墙登记且响亮展示后, 3 个自然日内人未拆任何一堵墙 (且人在场活跃)
     → **文件通道和 journal 散文一样死** → 杀此形态, 解法在**推送介质**, 不在又一个文件。
  ② 未来 10 班无任何新墙登记 → 墙是罕见事件, 机制过度工程 → 杀。
  ③ 班次**以登记墙替代先尽力绕行** (登记即收工) → **机制在制造打工人** → 杀。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WALLS = ROOT / "state" / "walls.jsonl"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _load() -> list[dict]:
    if not WALLS.exists():
        return []
    return [json.loads(l) for l in WALLS.read_text().splitlines() if l.strip()]


def _save(rows: list[dict]) -> None:
    WALLS.parent.mkdir(parents=True, exist_ok=True)
    WALLS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def hit(args) -> None:
    """撞墙登记。同一堵墙再撞 → hits+1 且 hit_log 追加一条 —— 撞击次数就是它的优先级。

    ⚠️ 判据③: **登记不是收工。** 登记前必须先尽力绕行;
    以登记替代绕行 = 机制在制造打工人 = 本机制该被杀。
    """
    rows = _load()
    for r in rows:
        if r["wall"] == args.wall and r.get("status") == "open":
            r["hits"] = r.get("hits", 0) + 1
            r.setdefault("hit_log", []).append(f"{args.shift} ({_now()[:10]}): {args.note or '再次撞墙'}")
            _save(rows)
            print(f"墙 #{r['id']} 又撞了一次 (第 {r['hits']} 次): {args.wall[:50]}…")
            return

    if not args.fix:
        raise SystemExit(
            "REJECTED — 新墙必须给出**一行解封动作** (--fix)。\n"
            "  一堵没有解法的墙, 对人来说只是一句抱怨 —— 而抱怨会被跳过。\n"
            "  要让人**复制粘贴就能拆掉它**。")

    wid = max((r["id"] for r in rows), default=0) + 1
    rows.append({
        "id": wid,
        "registered": _now()[:10],
        "shift": args.shift,
        "status": "open",
        "hits": 1,
        "wall": args.wall,
        "unblock_one_line": args.fix,
        "blocked_output": args.blocked or "",
        "hit_log": [f"{args.shift} ({_now()[:10]}): {args.note or '首次撞墙'}"],
        "torn_down": None,
    })
    _save(rows)
    print(f"墙 #{wid} 已登记 (状态 open): {args.wall[:60]}")


def down(args) -> None:
    """人拆掉了这堵墙。

    **只有人能拆** —— agent 拆 = 它给自己开权限, 那墙就不是墙了。
    (但 agent **能且必须**登记。登记是它的活, 拆是人的活。)
    """
    if os.environ.get("FOUNDER_HUMAN") != "1":
        raise SystemExit(
            "REFUSED — 只有人能拆墙 (需 FOUNDER_HUMAN=1)。\n"
            "  agent 自己宣布'墙拆了' = 自己给自己发赦免: 墙还立着, 账本却说没事了。\n"
            "  (亲证: 本账本上线第一天, 就有人把一堵**没拆的**墙标成了 torn_down。)\n"
            "  你的活是**登记**它 (walls.py hit), 人的活是**拆**它。")
    rows = _load()
    for r in rows:
        if r["id"] == args.id:
            r["status"] = "torn_down"
            r["torn_down"] = _now()
            _save(rows)
            print(f"墙 #{r['id']} 已拆 —— 它撞了 {r.get('hits', '?')} 次才被拆掉。")
            if r.get("blocked_output"):
                print(f"  解封的产出: {r['blocked_output'][:100]}")
            return
    raise SystemExit(f"无墙 #{args.id}")


def standing() -> list[dict]:
    return [r for r in _load() if r.get("status") == "open"]


def show(_args=None) -> None:
    """**响亮展示**未拆的墙。按撞击次数排 —— 撞得越多, 越该先拆。"""
    rows = standing()
    if not rows:
        print("🧱 未拆的墙: 0")
        return
    print(f"\n{'=' * 68}")
    print(f"🧱 未拆的墙 × {len(rows)} —— **这些是人的活, agent 拆不了。**")
    print(f"{'=' * 68}")
    for r in sorted(rows, key=lambda x: -x.get("hits", 0)):
        n = r.get("hits", 0)
        print(f"\n#{r['id']}  撞了 {n} 次 {'🔥' * min(n, 5)}   (首登 {r.get('registered', '?')}, {r.get('shift', '?')})")
        print(f"   墙:     {r['wall']}")
        print(f"   ⚡解封:  {r.get('unblock_one_line', '(未给出 —— 违规行)')}")
        if r.get("blocked_output"):
            print(f"   挡住了: {r['blocked_output']}")
    print(f"\n  ⚠️ **一堵墙挡住的不是一个班次, 是它本可能产出的一切。**")
    print(f"     实证: 一行权限挡了 split_sensitivity 三次 —— 而它跑起来的第一件事,")
    print(f"     是打穿了实盘策略的毕业证据。**那道门是个筛子, 而我们的真钱压在上面。**")
    print(f"{'=' * 68}\n")


def main() -> None:
    p = argparse.ArgumentParser(prog="walls", description="墙账本 — 把人也拉进机制")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("hit", help="撞墙登记 (先尽力绕行, 再登记!)")
    h.add_argument("wall")
    h.add_argument("--fix", "-f", help="**一行**解封动作 (人复制粘贴就能拆)。新墙必填。")
    h.add_argument("--blocked", "-b", help="它挡住了什么产出")
    h.add_argument("--shift", "-s", default="unknown", help="哪个班撞的")
    h.add_argument("--note", "-n", help="这次撞击的情形")
    h.set_defaults(fn=hit)

    d = sub.add_parser("down", help="人拆掉了这堵墙 (只有人能跑)")
    d.add_argument("id", type=int)
    d.set_defaults(fn=down)

    sub.add_parser("show", help="响亮展示未拆的墙").set_defaults(fn=show)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
