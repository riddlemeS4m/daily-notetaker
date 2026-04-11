#!/usr/bin/env bash
set -euo pipefail

if ! command -v expect >/dev/null 2>&1; then
  echo "Error: expect is not installed."
  echo "Install it on macOS with: brew install expect"
  exit 1
fi

expect <<'EOF'
  set timeout 20

  spawn /usr/bin/script -q /dev/null cursor-agent --force --yolo

  expect {
    -re "Trust this workspace" {
      send -- "\r"
      exp_continue
    }
    eof
  }
EOF
