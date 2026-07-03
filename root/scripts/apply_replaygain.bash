#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-/downloads-ama/temp}"

echo "$(date '+%Y-%m-%d %H:%M:%S') REPLAYGAIN :: Target: $TARGET"

if [ ! -d "$TARGET" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') REPLAYGAIN :: Target does not exist, skipping"
  exit 0
fi

if ! command -v rsgain >/dev/null 2>&1; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') REPLAYGAIN :: ERROR: rsgain not found"
  exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') REPLAYGAIN :: Using $(rsgain --version 2>&1 | head -1)"

# AMA processes one album folder at a time in /downloads-ama/temp.
# rsgain easy is album-folder aware and writes ReplayGain 2.0 tags.
rsgain easy -q "$TARGET"

if [ -f /config/scripts/sanitize_replaygain.py ]; then
  python3 /config/scripts/sanitize_replaygain.py "$TARGET" || true
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') REPLAYGAIN :: Done"
