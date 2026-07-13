#!/bin/sh
# 装时钟。**OS 级定时是主驱; 模型的自我排班只是加成, 不是依赖。**
# (亲证: 依赖模型"记得排下一班", 它会漏; launchd/cron 不会。)
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
OS=$(uname -s)

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
  echo "装好了。think 09:30 · build 15:00 (每日) · reflect/evolve (周日)。"
else
  echo "Linux: 把这些加进 crontab (注意 cd 前缀):"
  echo "  30 9 * * *  cd $ROOT && ./bin/shift think   >> state/cron.log 2>&1"
  echo "  0 15 * * *  cd $ROOT && ./bin/shift build   >> state/cron.log 2>&1"
  echo "  0 11 * * 0  cd $ROOT && ./bin/shift reflect >> state/cron.log 2>&1"
  echo "  0 12 * * 0  cd $ROOT && ./bin/shift evolve  >> state/cron.log 2>&1"
fi
