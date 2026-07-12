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


def snapshot() -> dict:
    """班前快照。"""
    return {"ledger": _hash(LEDGER), "journal": _hash(JOURNAL), "head": _git_head()}


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
        if after["head"] == before["head"]:
            return False, "无新 commit —— 执行班必须产出可验证的推进。"
        return True, "已产出 commit"

    return True, f"(未知班次 {shift}, 不设契约)"


if __name__ == "__main__":
    # 用法: contract.py snapshot                              → 班前快照 (供 shell 捕获)
    #       contract.py verify <shift> <ledger> <journal> <head>   (也接受三者拼成一个参数)
    if len(sys.argv) < 2:
        raise SystemExit("用法: contract.py snapshot | verify <shift> <ledger> <journal> <head>")

    if sys.argv[1] == "snapshot":
        s = snapshot()
        print(f"{s['ledger']} {s['journal']} {s['head']}")

    elif sys.argv[1] == "verify":
        if len(sys.argv) < 4:
            raise SystemExit("verify 需要: <shift> <ledger> <journal> <head>")
        shift = sys.argv[2]
        # 容错: 三个哈希可能作为 3 个参数传入, 也可能被引号包成 1 个
        parts = " ".join(sys.argv[3:]).split()
        if len(parts) != 3:
            raise SystemExit(f"班前快照应为 3 段 (ledger journal head), 收到 {len(parts)}")
        before = dict(zip(("ledger", "journal", "head"), parts))
        ok, msg = verify(shift, before)
        print(msg)
        sys.exit(0 if ok else 1)
