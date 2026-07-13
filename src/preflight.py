"""班前检查 — 契约是**物理上可满足**的吗? (伤疤 #4 + #5 的根治机制)

**为什么存在** (constitution/SCARS.md #4):
  系统的第一次思考班就 FAILED_SHIFT。契约要求"必须写 idea ledger",
  但 shift 的权限模式**不允许跑 Bash** —— 而 ledger 只能用 Bash 写。
  **agent 根本没有任何合法路径满足契约。** 它撞墙后退化成了打工人 (伸手要权限、给菜单、等点头)。

**两层教训**:
  1. **不可满足的契约不是压力, 是墙。**
  2. 更深: **agent 被环境锁死时, 默认行为就是退化成打工人。**
     → **给了契约, 就必须给对应的权限。要求产出却不给工具 = 制造打工人。**

---

**本模块的 v1 是个安慰剂 —— 它自己踩了伤疤 #5** (证据: state/shifts.log):

    [think] === 开班 (契约可满足 (工具已放行: ['Bash(python3 src/ledger.py'])) ===
    Ignoring 21 permissions.allow entries: this workspace has not been trusted.

  **同一时刻**, preflight 说"绿灯", 而整个 allowlist 正在被运行时忽略。
  它把班次一路放进了它本该拦住的那堵墙, 然后那个班照常 FAILED_SHIFT。

**v1 错在哪 (这是本文件存在的真正理由)**:
  它检查的是**声明** (settings.json 里写了吗), 不是**有效能力** (运行时真的生效了吗)。

  这是同一个错误的第三次复发:
    · SCARS #1  规矩**写在文档里** ≠ 规矩**被遵守**
    · GOAL §2   数字**不可伪造**   ≠ 数字**可归因于我**
    · SCARS #5  权限**写在配置里** ≠ 权限**真的生效**

  **未生效的机制 = 不存在的机制。而报告"已生效"的未生效机制, 比没有机制更糟 ——**
  **它让所有人停止追查。**

**v2 的原则: 失败要吵, 不要静。** 拿不准就拒绝开班 (fail closed)。
  让一个班**响亮地拒绝开**, 远好过让它**安静地撞墙**然后被记一笔 FAILED_SHIFT ——
  后者会把"我被封口了"错记成"我偷懒了", 而系统永远学不会区分**墙**和**懒**。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
GLOBAL_CFG = Path(os.path.expanduser("~/.claude.json"))

# 各班要满足契约, 必须能跑的东西
NEEDS: dict[str, list[str]] = {
    "think":   ["Bash(python3 src/ledger.py"],                      # 必须能写 ledger
    "reflect": [],                                                   # 只需 Edit (acceptEdits 自带)
    "evolve":  ["Bash(git commit"],                                  # 必须能 commit 机制变异
    "build":   ["Bash(git commit"],                                  # 必须能 commit
    "watch":   [],                                                   # 无产出契约
}


def _trusted() -> tuple[bool, str]:
    """workspace 被信任了吗?

    **这是有效性检查, 不是声明检查。** 未信任的 workspace 会**静默**丢弃
    settings.json 里的**整个** permissions 块 —— allowlist 写得再全也等于没写。
    警告只打到 stderr, 无人值守时没有任何人会看见 (伤疤 #5)。

    **fail closed**: 读不到 / 拿不准 → 一律当作未信任。
    宁可响亮地拒绝开班, 不可安静地放它撞墙。
    """
    if not GLOBAL_CFG.exists():
        return False, f"{GLOBAL_CFG} 不存在 —— 无法确认 workspace 已被信任"
    try:
        proj = json.loads(GLOBAL_CFG.read_text()).get("projects", {})
    except Exception as e:
        return False, f"{GLOBAL_CFG} 读不了 ({e}) —— 无法确认 workspace 已被信任"

    entry = proj.get(str(ROOT))
    if entry is None:
        return False, f"~/.claude.json 的 projects 里没有 {ROOT} —— workspace 未被信任"
    if entry.get("hasTrustDialogAccepted") is not True:
        return False, f"projects['{ROOT}'].hasTrustDialogAccepted != true —— workspace 未被信任"
    return True, "workspace 已信任 (settings.json 的 permissions 会真的生效)"


def check(shift: str) -> tuple[bool, str]:
    needs = NEEDS.get(shift, [])
    if not needs:
        return True, "本班无需额外工具 (acceptEdits 自带 Edit/Write)"

    # --- 门 1: 有效性 (伤疤 #5) —— 先问"权限会生效吗", 再问"权限写了吗" ---
    ok, why = _trusted()
    if not ok:
        return False, (
            f"**权限配置不会生效** —— {why}\n"
            f"  伤疤 #5: 未信任的 workspace 会**静默**忽略整个 allowlist。\n"
            f"  于是 {shift} 班的契约要求 {needs}, 而 agent 一个都跑不了 ——\n"
            f"  它会撞墙、被记 FAILED_SHIFT, 而真因是**它被封口了, 不是它偷懒**。\n"
            f"  → 修复 (人来做, 这是安全边界, agent 不该能自己授信):\n"
            f"      在本目录交互式跑一次 Claude Code 并接受信任对话框, 或\n"
            f"      ~/.claude.json → projects['{ROOT}'].hasTrustDialogAccepted = true\n"
            f"  **拒绝开班。响亮地失败, 好过安静地撞墙。**")

    # --- 门 2: 声明 (伤疤 #4) —— 权限会生效了, 那它写了吗? ---
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

    return True, f"契约可满足 (已信任 + 已放行: {needs})"


if __name__ == "__main__":
    ok, msg = check(sys.argv[1] if len(sys.argv) > 1 else "")
    print(msg)
    sys.exit(0 if ok else 1)
