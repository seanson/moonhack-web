#!/usr/bin/env bash
# Screenshot pages from the local Hugo server with headless Chrome.
#
# Usage: bash scripts/dev_screenshot.sh [path ...]
# Env:   PORT (default 1414), OUT (default .work/data/screenshots)
#
# Headless Chrome enforces a ~500px minimum window width, so the phone shot
# uses a 2x device scale factor (780px window => 390px CSS viewport).
set -euo pipefail

PORT="${PORT:-1414}"
OUT="${OUT:-.work/data/screenshots}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
BASE="http://127.0.0.1:${PORT}"

if [[ ! -x "$CHROME" ]]; then
  echo "Chrome not found at: $CHROME (override with CHROME=/path/to/chrome)" >&2
  exit 1
fi

if ! curl -sf -o /dev/null "$BASE/"; then
  echo "No Hugo server on $BASE - start one with 'make web'" >&2
  exit 1
fi

paths=("$@")
if [[ ${#paths[@]} -eq 0 ]]; then
  paths=("/")
fi

mkdir -p "$OUT"

shoot() {
  local url="$1" file="$2"
  shift 2
  "$CHROME" --headless --disable-gpu --hide-scrollbars --no-first-run \
    --virtual-time-budget=5000 "$@" --screenshot="$file" "$url" 2>/dev/null
  echo "  $file"
}

for path in "${paths[@]}"; do
  slug="$(echo "${path#/}" | tr -c 'A-Za-z0-9._-' '-' | sed 's/-*$//')"
  slug="${slug:-home}"
  echo "${BASE}${path}"
  shoot "${BASE}${path}" "${OUT}/${slug}-desktop.png" --window-size=1440,2400
  shoot "${BASE}${path}" "${OUT}/${slug}-mobile.png" \
    --force-device-scale-factor=2 --window-size=780,2400
done
