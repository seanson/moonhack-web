#!/usr/bin/env bash
# Render /poster/ to an A4 PDF with headless Chrome.
#
# Usage: bash scripts/make_poster.sh [out.pdf]
# Env:   PORT (default 1415, kept off the dev server's port), CHROME
set -euo pipefail

PORT="${PORT:-1415}"
OUT="${1:-.work/data/moonhack-2026-poster-a4.pdf}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
URL="http://127.0.0.1:${PORT}/poster/"

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

"$CHROME" --headless --disable-gpu --no-first-run \
  --virtual-time-budget=5000 --no-pdf-header-footer \
  --print-to-pdf="$OUT" "$URL" 2>/dev/null

echo "wrote $OUT"
