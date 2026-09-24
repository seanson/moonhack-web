#!/usr/bin/env bash
# Render /og/ to the 1200x630 social card at static/og-moonhack-2026.png.
#
# Usage: bash scripts/make_og.sh [out.png]
# Env:   PORT (default 1417, kept off the dev server's port), CHROME
set -euo pipefail

PORT="${PORT:-1417}"
OUT="${1:-static/og-moonhack-2026.png}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
URL="http://127.0.0.1:${PORT}/og/"

if [[ ! -x "$CHROME" ]]; then
  echo "Chrome not found at: $CHROME (override with CHROME=/path/to/chrome)" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

hugo server --bind 127.0.0.1 --port "$PORT" --logLevel error &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT

for _ in $(seq 1 40); do
  if curl -sf -o /dev/null "$URL"; then
    break
  fi
  sleep 0.25
done

if ! curl -sf -o /dev/null "$URL"; then
  echo "Hugo server never came up on $URL" >&2
  exit 1
fi

"$CHROME" --headless --disable-gpu --hide-scrollbars --no-first-run \
  --virtual-time-budget=5000 --window-size=1200,630 \
  --screenshot="$OUT" "$URL" 2>/dev/null

echo "wrote $OUT"
