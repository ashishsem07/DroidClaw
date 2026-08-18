#!/usr/bin/env bash
# Start the local ADB bridge (MobileRun-compatible REST API over plain ADB).
# Portable: resolves adb-bridge.py next to this script, runs from anywhere.
#
#   local-bridge/start-bridge.sh
#   ADB_SERIAL=<serial> PORT=8723 local-bridge/start-bridge.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"

if ! command -v adb >/dev/null 2>&1; then
  echo "adb not found. Install: brew install android-platform-tools" >&2
  exit 1
fi

echo "ADB devices:"
adb devices | sed 's/^/  /'

PORT="${PORT:-8723}" python3 "$HERE/adb-bridge.py"
