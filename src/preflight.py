"""班前检查 — 契约是**物理上可满足**的吗? (伤疤 #4 的根治机制)

**为什么存在** (constitution/SCARS.md #4):
  系统的第一次思考班就 FAILED_SHIFT。契约要求"必须写 idea ledger",
  但 shift 的权限模式**不允许跑 Bash** —— 而 ledger 只能用 Bash 写。
  **agent 根本没有任何合法路径满足契约。** 它撞墙后退化成了打工人 (伸手要权限、给菜单、等点头)。

**两层教训**:
  1. **不可满足的契约不是压力, 是墙。**
  2. 更深: **agent 被环境锁死时, 默认行为就是退化成打工人。**
     所以"打工人化"不只是动机问题 —— 也是**能力被剥夺后的必然反应**。
     → **给了契约, 就必须给对应的权限。要求产出却不给工具 = 制造打工人。**

本模块在开班前验证: 这个班要满足契约, 需要的工具**都放行了吗**? 没有 → 拒绝开班 (而不是让它撞墙)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"

# 各班要满足契约, 必须能跑的东西
NEEDS: dict[str, list[str]] = {
    "think":   ["Bash(python3 src/ledger.py"],                      # 必须能写 ledger
    "reflect": [],                                                   # 只需 Edit (acceptEdits 自带)
    "evolve":  ["Bash(git commit"],                                  # 必须能 commit 机制变异
    "build":   ["Bash(git commit"],                                  # 必须能 commit
    "watch":   [],                                                   # 无产出契约
}


def check(shift: str) -> tuple[bool, str]:
    needs = NEEDS.get(shift, [])
    if not needs:
        return True, "本班无需额外工具"

    if not SETTINGS.exists():
        return False, f".claude/settings.json 不存在 —— {shift} 班需要 {needs} 却无授权"

    try:
        allow = json.loads(SETTINGS.read_text()).get("permissions", {}).get("allow", [])
    except Exception as e:
        return False, f"settings.json 读不了: {e}"

    missing = [n for n in needs
               if not any(a.startswith(n) or n.startswith(a.rstrip(":*")) for a in allow)]
    if missing:
        return False, (
            f"**契约不可满足** —— {shift} 班的契约要求用 {missing}, 但权限里没放行。\n"
            f"  伤疤 #4: **不可满足的契约不是压力, 是墙。** agent 撞墙后会退化成打工人 (伸手要权限)。\n"
            f"  → 要么放行工具, 要么改契约。**别让它撞墙。**")
    return True, f"契约可满足 (工具已放行: {needs})"


if __name__ == "__main__":
    ok, msg = check(sys.argv[1] if len(sys.argv) > 1 else "")
    print(msg)
    sys.exit(0 if ok else 1)
