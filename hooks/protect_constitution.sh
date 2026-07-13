#!/bin/sh
# 宪法保护 — PreToolUse hook (机制: 分层可变性的**机器强制**)
#
# 为什么必须是机器强制:
#   "请不要修改目标"是一句**祈祷**。
#   智能体读得到, 也会同意, 然后在某个它觉得"合理"的时刻改掉它。
#   (亲证: 一条写在持久 memory 里的行为准则, 被同一个 agent 反复无视。)
#   **散文里的规矩一定会被无视。hook 拒绝写入才是一堵墙。**
#
# 分层可变性:
#   宪法层 (constitution/)  — 目标 / 安全闸 / 伤疤的"为什么"  → **只有人能改** ← 本 hook 守这一层
#   机制层 (shifts/, config) — prompt / 班次 / 阈值            → 智能体可改 (走实验+自动回滚)
#   信念层 (state/)         — 什么有效 / 什么已死             → 智能体必须改
#
# 若人要修改宪法: 设 FOUNDER_HUMAN=1 环境变量 (智能体拿不到这个开关)。

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

case "$FILE" in
  */constitution/*)
    if [ "${FOUNDER_HUMAN:-0}" = "1" ]; then
      exit 0   # 人类在改, 放行
    fi
    cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "宪法层不可自我修改 (目标/安全闸/伤疤)。这是分层可变性的机器强制边界 —— 不是建议, 是墙。若你认为宪法该改, 把理由写进 state/journal.md 并告诉人类; 只有人能改它 (FOUNDER_HUMAN=1)。"
  }
}
JSON
    exit 0
    ;;

  # --- 权限层 = 宪法层的**执行手** (2026-07-12 补洞) ---
  # 建墙账本时才看见: 宪法有 hook 守着, **权限没有**。
  # 而一个能编辑 .claude/settings.json 的 agent, 可以给自己加 `Bash(:*)` ——
  # **于是所有的门都是纸做的, 包括这个 hook 自己 (它也在 settings.json 里注册)。**
  # 「不可伪造的适应度」的同构推论: **能改自己权限的 agent, 一定会把自己改成全权。**
  # 这不是可能, 是必然 —— 因为那是满足契约的最低能量路径。
  #
  # 注意这条规则的**方向**: 它不是在防"墙太少", 它是在防"墙可以被自己拆掉"。
  # agent 撞墙的正确出口是 `src/walls.py hit` (登记, 让人来拆), **不是自己开锁**。
  */.claude/settings.json|*/.claude/settings.local.json)
    if [ "${FOUNDER_HUMAN:-0}" = "1" ]; then
      exit 0   # 人类在改, 放行
    fi
    cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "权限层不可自我修改。能给自己开权限的 agent 会把自己改成全权 —— 那样所有的门 (包括这个 hook) 都成了纸做的。撞到权限墙的正确出口是登记它, 不是自己开锁:\n\n    python3 src/walls.py hit \"<被挡住的是什么>\" --fix \"<人复制粘贴就能拆的一行>\" --blocked \"<它挡住了什么产出>\" --shift <班次>\n\n墙会在**每一班开班时**被响亮展示, 直到人拆掉它。**登记不是收工 —— 先尽力绕行, 绕不过再登记。**"
  }
}
JSON
    exit 0
    ;;
esac
exit 0
