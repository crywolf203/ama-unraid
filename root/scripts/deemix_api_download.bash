#!/usr/bin/env bash
set -euo pipefail

ALBUM_URL="${1:-}"

if [ -z "$ALBUM_URL" ]; then
  echo "Usage: deemix_api_download.bash <deezer album url>"
  exit 1
fi

DEEMIX_API_URL="${DEEMIX_API_URL:-http://10.13.1.138:6595}"
DEEMIX_CONFIG_PATH="${DEEMIX_CONFIG_PATH:-/deemix-config}"
DEEMIX_DOWNLOAD_PATH="${DEEMIX_DOWNLOAD_PATH:-/deemix-downloads}"
BITRATE="${BITRATE:-9}"
FILE_UID="${PUID:-99}"
FILE_GID="${PGID:-100}"
POLL_SECONDS="${DEEMIX_POLL_SECONDS:-10}"
MAX_POLLS="${DEEMIX_API_MAX_POLLS:-20}"
STABLE_POLLS="${DEEMIX_STABLE_POLLS:-3}"

ALBUM_ID="$(printf '%s' "$ALBUM_URL" | sed -nE 's#.*album/([0-9]+).*#\1#p')"

if [ -z "$ALBUM_ID" ]; then
  echo "Could not parse album ID from: $ALBUM_URL"
  exit 1
fi

for cmd in curl jq find python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command inside container: $cmd"
    exit 1
  fi
done

LOGIN_JSON="${DEEMIX_CONFIG_PATH}/login.json"

if [ ! -f "$LOGIN_JSON" ]; then
  echo "Missing Deemix login file: $LOGIN_JSON"
  exit 1
fi

ARL_FROM_DEEMIX="$(jq -r '.arl // empty' "$LOGIN_JSON")"

if [ -z "$ARL_FROM_DEEMIX" ]; then
  echo "ARL missing from $LOGIN_JSON"
  exit 1
fi

COOKIE="$(mktemp /tmp/deemix-api-cookie.XXXXXX)"
trap 'rm -f "$COOKIE"' EXIT

echo "DEEMIX_API :: Album URL: $ALBUM_URL"
echo "DEEMIX_API :: Album ID:  $ALBUM_ID"
echo "DEEMIX_API :: API URL:   $DEEMIX_API_URL"

LOGIN_BODY="$(jq -nc --arg arl "$ARL_FROM_DEEMIX" '{arl:$arl}')"

LOGIN_RESP="$(curl -sS -c "$COOKIE" -b "$COOKIE" \
  -X POST "${DEEMIX_API_URL}/api/loginArl" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_BODY")"

LOGIN_STATUS="$(echo "$LOGIN_RESP" | jq -r '.status // empty')"

case "$LOGIN_STATUS" in
  1|2|3)
    echo "DEEMIX_API :: Login OK"
    ;;
  *)
    echo "DEEMIX_API :: Login failed"
    echo "$LOGIN_RESP" | jq .
    exit 1
    ;;
esac

ADD_BODY="$(jq -nc --arg url "$ALBUM_URL" --argjson bitrate "$BITRATE" '{url:$url,bitrate:$bitrate}')"

ADD_RESP="$(curl -sS -c "$COOKIE" -b "$COOKIE" \
  -X POST "${DEEMIX_API_URL}/api/addToQueue" \
  -H "Content-Type: application/json" \
  -d "$ADD_BODY")"

ADD_RESULT="$(echo "$ADD_RESP" | jq -r '.result // false')"

if [ "$ADD_RESULT" != "true" ]; then
  echo "DEEMIX_API :: Failed to add album to queue"
  echo "$ADD_RESP" | jq .
  exit 1
fi

echo "DEEMIX_API :: Album accepted by Deemix"

QUEUE_FILE="${DEEMIX_CONFIG_PATH}/queue/album_${ALBUM_ID}_${BITRATE}.json"
ALBUM_DIR=""
LAST_SIG=""
STABLE_COUNT=0

MAX_POLLS="${DEEMIX_API_MAX_POLLS:-20}"
echo "DEEMIX_API :: Max polls: $MAX_POLLS"
for i in $(seq 1 "$MAX_POLLS"); do
  ALBUM_DIR="$(find "$DEEMIX_DOWNLOAD_PATH" -type d -name "*(${ALBUM_ID})" -print -quit 2>/dev/null || true)"

  AUDIO_COUNT=0
  LRC_COUNT=0
  STATUS=""

  if [ -n "$ALBUM_DIR" ]; then
    AUDIO_COUNT="$(find "$ALBUM_DIR" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) 2>/dev/null | wc -l)"
    LRC_COUNT="$(find "$ALBUM_DIR" -type f -iname "*.lrc" 2>/dev/null | wc -l)"
  fi

  if [ -f "$QUEUE_FILE" ]; then
    STATUS="$(jq -r '.status // empty' "$QUEUE_FILE" 2>/dev/null || true)"
  fi

  SIG="${STATUS}:${AUDIO_COUNT}:${LRC_COUNT}"

  if [ "$SIG" = "$LAST_SIG" ] && [ "$AUDIO_COUNT" -gt 0 ]; then
    STABLE_COUNT=$((STABLE_COUNT + 1))
  else
    STABLE_COUNT=0
  fi

  LAST_SIG="$SIG"

  echo "DEEMIX_API :: Check $i status=${STATUS:-none} audio=${AUDIO_COUNT} lrc=${LRC_COUNT} stable=${STABLE_COUNT}"

  if [ "$AUDIO_COUNT" -gt 0 ] && { [ "$STATUS" = "completed" ] || [ "$STABLE_COUNT" -ge "$STABLE_POLLS" ]; }; then
    break
  fi

  sleep "$POLL_SECONDS"
done

if [ -z "$ALBUM_DIR" ]; then
  echo "DEEMIX_API :: Could not find album folder for album ID $ALBUM_ID"
  exit 1
fi

echo "DEEMIX_API :: Album folder: $ALBUM_DIR"

python3 /config/scripts/lrc_fallback.py "$DEEMIX_DOWNLOAD_PATH" "$ALBUM_ID"

mkdir -p /downloads-ama/temp
find /downloads-ama/temp -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true

echo "DEEMIX_API :: Copying files into AMA temp folder"
cp -a "$ALBUM_DIR"/. /downloads-ama/temp/

chown -R "${FILE_UID}:${FILE_GID}" /downloads-ama/temp "$ALBUM_DIR" 2>/dev/null || true
chmod -R u+rwX,g+rwX,o+rwX /downloads-ama/temp "$ALBUM_DIR" 2>/dev/null || true

echo "DEEMIX_API :: Temp audio count: $(find /downloads-ama/temp -type f \( -iname '*.flac' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.opus' \) | wc -l)"
echo "DEEMIX_API :: Temp LRC count:   $(find /downloads-ama/temp -type f -iname '*.lrc' | wc -l)"
echo "DEEMIX_API :: Done"
