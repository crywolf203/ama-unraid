#!/usr/bin/env bash
set -euo pipefail

ALBUM_URL="${1:-}"

if [ -z "$ALBUM_URL" ]; then
  echo "Usage: deemix_direct_download.bash <deezer album url>"
  exit 1
fi

DEEMIX_CONFIG_PATH="${DEEMIX_CONFIG_PATH:-/deemix-config}"
DEEMIX_DOWNLOAD_PATH="${DEEMIX_DOWNLOAD_PATH:-/deemix-downloads}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/config/deemix/xdg}"
FILE_UID="${PUID:-99}"
FILE_GID="${PGID:-100}"

ALBUM_ID="$(printf '%s' "$ALBUM_URL" | sed -nE 's#.*album/([0-9]+).*#\1#p')"

if [ -z "$ALBUM_ID" ]; then
  echo "DEEMIX_DIRECT :: Could not parse album ID from: $ALBUM_URL"
  exit 1
fi

for cmd in deemix find python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "DEEMIX_DIRECT :: Missing required command inside container: $cmd"
    exit 1
  fi
done

mkdir -p "$XDG_CONFIG_HOME/deemix" "$DEEMIX_DOWNLOAD_PATH" /downloads-ama/temp

# Prefer ARL_TOKEN. Fall back to Deemix WebUI login.json if mounted.
if [ -n "${ARL_TOKEN:-}" ]; then
  echo -n "$ARL_TOKEN" > "$XDG_CONFIG_HOME/deemix/.arl"
elif [ -f "${DEEMIX_CONFIG_PATH}/login.json" ]; then
  ARL_FROM_LOGIN="$(python3 - "$DEEMIX_CONFIG_PATH/login.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

print(data.get("arl", ""))
PY
)"
  if [ -z "$ARL_FROM_LOGIN" ]; then
    echo "DEEMIX_DIRECT :: ARL missing from ${DEEMIX_CONFIG_PATH}/login.json"
    exit 1
  fi
  echo -n "$ARL_FROM_LOGIN" > "$XDG_CONFIG_HOME/deemix/.arl"
else
  echo "DEEMIX_DIRECT :: Missing ARL_TOKEN and missing ${DEEMIX_CONFIG_PATH}/login.json"
  exit 1
fi

# Map AMA formats to deemix CLI bitrate values.
# Set DEEMIX_DIRECT_BITRATE manually if you need to override this.
if [ -n "${DEEMIX_DIRECT_BITRATE:-}" ]; then
  CLI_BITRATE="$DEEMIX_DIRECT_BITRATE"
else
  case "${FORMAT:-FLAC}" in
    FLAC|ALAC|OPUS|AAC)
      CLI_BITRATE="flac"
      ;;
    MP3)
      if [ "${BITRATE:-320}" = "128" ]; then
        CLI_BITRATE="128"
      else
        CLI_BITRATE="320"
      fi
      ;;
    *)
      CLI_BITRATE="flac"
      ;;
  esac
fi

MARKER="$(mktemp /tmp/deemix-direct-marker.XXXXXX)"
trap 'rm -f "$MARKER"' EXIT

echo "DEEMIX_DIRECT :: Album URL: $ALBUM_URL"
echo "DEEMIX_DIRECT :: Album ID:  $ALBUM_ID"
echo "DEEMIX_DIRECT :: Output:    $DEEMIX_DOWNLOAD_PATH"
echo "DEEMIX_DIRECT :: Bitrate:   $CLI_BITRATE"

deemix -b "$CLI_BITRATE" -p "$DEEMIX_DOWNLOAD_PATH" "$ALBUM_URL"

ALBUM_DIR="$(find "$DEEMIX_DOWNLOAD_PATH" -type d -name "*(${ALBUM_ID})" -print -quit 2>/dev/null || true)"

# Fallback: find the newest folder with audio created/updated during this run.
if [ -z "$ALBUM_DIR" ]; then
  ALBUM_DIR="$(find "$DEEMIX_DOWNLOAD_PATH" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) -newer "$MARKER" -printf '%h\n' 2>/dev/null | sort -u | head -n 1 || true)"
fi

if [ -z "$ALBUM_DIR" ]; then
  echo "DEEMIX_DIRECT :: Could not find downloaded album folder for album ID $ALBUM_ID"
  exit 1
fi

echo "DEEMIX_DIRECT :: Album folder: $ALBUM_DIR"

if [ -f /config/scripts/lrc_fallback.py ]; then
  python3 /config/scripts/lrc_fallback.py "$DEEMIX_DOWNLOAD_PATH" "$ALBUM_ID" || true
elif [ -f /scripts/lrc_fallback.py ]; then
  python3 /scripts/lrc_fallback.py "$DEEMIX_DOWNLOAD_PATH" "$ALBUM_ID" || true
fi

find /downloads-ama/temp -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true

echo "DEEMIX_DIRECT :: Copying files into AMA temp folder"
cp -a "$ALBUM_DIR"/. /downloads-ama/temp/

chown -R "${FILE_UID}:${FILE_GID}" /downloads-ama/temp "$ALBUM_DIR" 2>/dev/null || true
chmod -R u+rwX,g+rwX,o+rwX /downloads-ama/temp "$ALBUM_DIR" 2>/dev/null || true

echo "DEEMIX_DIRECT :: Temp audio count: $(find /downloads-ama/temp -type f \( -iname '*.flac' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.opus' \) | wc -l)"
echo "DEEMIX_DIRECT :: Temp LRC count:   $(find /downloads-ama/temp -type f -iname '*.lrc' | wc -l)"
echo "DEEMIX_DIRECT :: Done"
