"""输出契约的机器强制 (机制 1 的核心)。

**支点洞察**: 如果一个循环的输出契约允许"无事可做", 智能体就一定会退化到"无事可做" ——
因为那是**满足契约的最低能量路径**。

所以: 契约不能是 prompt 里的一句叮嘱 (会被无视), 必须是**班后由机器验证的断言**。
本模块 = 那台机器。班次不达标 → FAILED_SHIFT, 记录在案。

各班契约 (输出互斥):
  watch   : 可以"一切正常" —— 那就是它的活 (唯一允许无为的班)
  think   : ledger 必须变化 (新想法 / 杀死 / 升级)。"无事可做" = 失败
  reflect : journal 必须新增一条, 且必须点名一个"浪费/错误"
  evolve  : 必须有 commit 改动机制层 (shifts/ 或 config), 或写下带数据的"不变"决定
  build   : 必须有新 commit
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "state" / "ideas.jsonl"
JOURNAL = ROOT / "state" / "journal.md"


def _hash(p: Path) -> str:
    if not p.exists():
        return "absent"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip() or "none"
    except Exception:
        return "none"


def _target() -> str:
    for line in (ROOT / "constitution" / "GOAL.md").read_text().splitlines():
        if line.startswith("FOUNDER_TARGET="):
            return line.split("=", 1)[1].strip()
    return ""


def _track_attributed() -> int:
    """赛道上**带 Founder-OS-Shift trailer** 的 commit 数。

    **这是可归因的计数, 不是'HEAD 变了没'。**
    伤疤 #8: 原版检 founder-os 的 HEAD —— 于是**任何人**的 commit 都能让 build 班 PASS
    (包括人类在班次运行期间的并发 commit)。**不可伪造 ≠ 可归因** —— 这条 agent 教过我,
    我把它用在了 fitness 上, **却没用在契约本身上**。
    """
    tgt = _target()
    if not tgt or not Path(tgt).exists():
        return -1
    try:
        r = subprocess.run(["git", "log", "--grep=^Founder-OS-Shift:", "--extended-regexp",
                            "--oneline"], cwd=tgt, capture_output=True, text=True, timeout=20)
        return len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        return -1


def snapshot() -> dict:
    """班前快照。"""
    return {"ledger": _hash(LEDGER), "journal": _hash(JOURNAL), "head": _git_head(),
            "track": _track_attributed()}


def verify(shift: str, before: dict) -> tuple[bool, str]:
    """班后验证契约。→ (达标?, 说明)"""
    after = snapshot()

    if shift == "watch":
        return True, "巡检班允许'一切正常' (唯一允许无为的班)"

    if shift == "think":
        if after["ledger"] == before["ledger"]:
            return False, ("idea ledger 无变化 —— 未提新想法, 也未杀/升级任何想法。\n"
                           "  思考班说'无事可做' = 本班失败。那是巡检班的活, 不是你的。")
        return True, "ledger 已变化 (提出/杀死/升级了想法)"

    if shift == "reflect":
        if after["journal"] == before["journal"]:
            return False, "journal 无新增 —— 反刍班必须点名一个浪费/错误。'一切都好' = 失败。"
        return True, "journal 已记录反刍"

    if shift == "evolve":
        if after["head"] == before["head"] and after["journal"] == before["journal"]:
            return False, ("既无机制变异 (commit), 也无带数据的'不变'决定 (journal)。\n"
                           "  进化班必须二选一。")
        return True, "机制已变异, 或已记录带数据的'不变'决定"

    if shift == "build":
        # **检赛道, 不检车库。检可归因的 trailer, 不检"HEAD 变了没"。** (伤疤 #8)
        if after["track"] <= before["track"]:
            return False, (
                "赛道上没有新的**可归因** commit。\n"
                "  执行班的工作现场在**赛道**, 不在车库。只改 founder-os 自己 = **在车库里擦车, 圈速不会变**。\n"
                "  赛道 commit 必须带 trailer: `Founder-OS-Shift: build`\n"
                "  (伤疤 #8: 旧契约检 founder-os 的 HEAD → **任何人**的 commit 都能让你 PASS, 包括人类并发提交的。\n"
                "   **不可伪造 ≠ 可归因。**)")
        return True, f"赛道上产出可归因 commit (trailer 计数 {before['track']} → {after['track']})"

    return True, f"(未知班次 {shift}, 不设契约)"


if __name__ == "__main__":
    # 用法: contract.py snapshot                              → 班前快照 (供 shell 捕获)
    #       contract.py verify <shift> <ledger> <journal> <head>   (也接受三者拼成一个参数)
    if len(sys.argv) < 2:
        raise SystemExit("用法: contract.py snapshot | verify <shift> <ledger> <journal> <head>")

    if sys.argv[1] == "snapshot":
        s = snapshot()
        print(f"{s['ledger']} {s['journal']} {s['head']} {s['track']}")

    elif sys.argv[1] == "verify":
        if len(sys.argv) < 4:
            raise SystemExit("verify 需要: <shift> <ledger> <journal> <head>")
        shift = sys.argv[2]
        # 容错: 三个哈希可能作为 3 个参数传入, 也可能被引号包成 1 个
        parts = " ".join(sys.argv[3:]).split()
        if len(parts) != 4:
            raise SystemExit(f"班前快照应为 4 段 (ledger journal head track), 收到 {len(parts)}")
        before = dict(zip(("ledger", "journal", "head", "track"), parts))
        before["track"] = int(before["track"])
        ok, msg = verify(shift, before)
        print(msg)
        sys.exit(0 if ok else 1)
