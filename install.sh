#!/bin/sh
# 装时钟。**OS 级定时是主驱; 模型的自我排班只是加成, 不是依赖。**
# (亲证: 依赖模型"记得排下一班", 它会漏; launchd/cron 不会。)
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
OS=$(uname -s)

# ============================================================================
# 开箱自检 —— **装完就宣布成功 = 「声明≠有效」**。装之前先验它真的能跑。
# (伤疤 #5: 未信任的 workspace 会**静默**忽略整个权限配置 → 每一班都会 REFUSED,
#           而警告只打到 stderr, 无人值守时没人看得见。**产品出厂即坏。**)
# ============================================================================
echo "== 开箱自检 =="

# 1. 宪法填了吗? (没填 = 无法自我进化, 只能自我催眠)
if [ ! -f "$ROOT/constitution/GOAL.local.md" ]; then
  echo "  ✗ 未填宪法。先做这个 (这是**人的活**, agent 改不了):"
  echo "      cp constitution/GOAL.md constitution/GOAL.local.md"
  echo "      \$EDITOR constitution/GOAL.local.md   # 目标 + **不可伪造的**判据"
  echo ""
  echo "  ⚠️  没有不可伪造的现实反馈信号 → **无法自我进化, 只能自我催眠。**"
  exit 1
fi

# 2. workspace 被信任了吗? (伤疤 #5 —— 这一条不过, 装了也白装)
if ! python3 -c "
import json,sys
from pathlib import Path
try:
    p=json.loads((Path.home()/'.claude.json').read_text()).get('projects',{})
except Exception:
    sys.exit(1)
sys.exit(0 if p.get('$ROOT',{}).get('hasTrustDialogAccepted') is True else 1)
" 2>/dev/null; then
  echo "  ✗ workspace 未被信任 → **settings.json 的权限会被静默忽略 → 每一班都会 REFUSED**"
  echo ""
  echo "    修 (二选一):"
  echo "      a) 在本目录交互式跑一次 claude, 接受信任对话框"
  echo "      b) python3 -c \"import json,pathlib;p=pathlib.Path.home()/'.claude.json';d=json.loads(p.read_text());d.setdefault('projects',{}).setdefault('$ROOT',{})['hasTrustDialogAccepted']=True;p.write_text(json.dumps(d,indent=2))\""
  echo ""
  echo "  **拒绝安装。** 装一个跑不起来的时钟, 比不装更糟 —— 它会让你以为系统在跑。"
  exit 1
fi

# 3. 契约的牙齿还在吗?
python3 -m unittest discover "$ROOT/tests" >/dev/null 2>&1 \
  && echo "  ✓ 牙齿测试全绿" \
  || { echo "  ✗ 牙齿测试失败 —— 机制坏了, 拒绝安装"; exit 1; }

# 4. 各班契约物理上可满足吗? (伤疤 #4: 不可满足的契约不是压力, 是墙)
for s in think build; do
  python3 "$ROOT/src/preflight.py" "$s" >/dev/null 2>&1 \
    || { echo "  ✗ $s 班契约不可满足 —— 拒绝安装 (别让 agent 撞墙)"; exit 1; }
done
echo "  ✓ 契约可满足 (信任+权限都真的生效)"
echo "  ✓ 宪法已填"
echo ""

if [ "$OS" = "Darwin" ]; then
  mkdir -p "$HOME/Library/LaunchAgents"
  # think 每日 10:00 · reflect 周日 11:00 · evolve 周日 12:00
  # think 09:30 每日 (出想法) → build 15:00 每日 (写赛道 — fitness 的唯一来源)
  # reflect 周日 11:00 · evolve 周日 12:00
  for job in "think 9 30 *" "build 15 0 *" "reflect 11 0 0" "evolve 12 0 0"; do
    set -- $job; NAME=$1; HOUR=$2; MIN=$3; DOW=$4
    PLIST="$HOME/Library/LaunchAgents/com.founder-os.$NAME.plist"
    { echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
      echo '<plist version="1.0"><dict>'
      echo "  <key>Label</key><string>com.founder-os.$NAME</string>"
      echo '  <key>ProgramArguments</key><array>'
      echo "    <string>$ROOT/bin/shift</string><string>$NAME</string>"
      echo '  </array>'
      echo "  <key>WorkingDirectory</key><string>$ROOT</string>"
      echo '  <key>StartCalendarInterval</key><dict>'
      echo "    <key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MIN</integer>"
      [ "$DOW" != "*" ] && echo "    <key>Weekday</key><integer>$DOW</integer>"
      echo '  </dict>'
      echo "  <key>StandardOutPath</key><string>$ROOT/state/launchd.log</string>"
      echo "  <key>StandardErrorPath</key><string>$ROOT/state/launchd.log</string>"
      echo '  <key>EnvironmentVariables</key><dict>'
      echo '    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>'
      echo '  </dict>'
      echo '</dict></plist>'
    } > "$PLIST"
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    echo "  ✓ com.founder-os.$NAME"
  done
  echo ""
  echo "装好了。think 09:30 · build 15:00 (每日) · reflect/evolve (周日)。"
  echo ""
  echo "⚠️  **时钟是给'你不在'时的兜底 —— 不是给'你在'时的借口。** (伤疤 #9)"
  echo "    你在的时候, 手动跑: bin/shift think"
else
  echo "Linux: 把这些加进 crontab (注意 cd 前缀):"
  echo "  30 9 * * *  cd $ROOT && ./bin/shift think   >> state/cron.log 2>&1"
  echo "  0 15 * * *  cd $ROOT && ./bin/shift build   >> state/cron.log 2>&1"
  echo "  0 11 * * 0  cd $ROOT && ./bin/shift reflect >> state/cron.log 2>&1"
  echo "  0 12 * * 0  cd $ROOT && ./bin/shift evolve  >> state/cron.log 2>&1"
fi
