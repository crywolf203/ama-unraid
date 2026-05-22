#!/usr/bin/env bash
set -euo pipefail

ALBUM_URL="${1:-}"

if [ -z "$ALBUM_URL" ]; then
  echo "Usage: $0 <deezer album url>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEEMIX_API_URL="${DEEMIX_API_URL:-http://127.0.0.1:6595}"
DEEMIX_CONFIG_PATH="${DEEMIX_CONFIG_PATH:-/mnt/cache/appdata/Deemix-1}"
DEEMIX_DOWNLOAD_PATH="${DEEMIX_DOWNLOAD_PATH:-/mnt/user/media2/deemix-1}"
AMA_IMAGE="${AMA_IMAGE:-ghcr.io/crywolf203/ama-unraid:latest}"
BITRATE="${BITRATE:-9}"
FILE_UID="${FILE_UID:-99}"
FILE_GID="${FILE_GID:-100}"
POLL_SECONDS="${POLL_SECONDS:-10}"
MAX_POLLS="${DEEMIX_API_MAX_POLLS:-20}"
STABLE_POLLS="${STABLE_POLLS:-3}"

ALBUM_ID="$(printf '%s' "$ALBUM_URL" | sed -nE 's#.*album/([0-9]+).*#\1#p')"

if [ -z "$ALBUM_ID" ]; then
  echo "Could not parse album ID from: $ALBUM_URL"
  exit 1
fi

for cmd in curl jq docker find; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command on host: $cmd"
    exit 1
  fi
done

if [ ! -f "${SCRIPT_DIR}/lrc_fallback.py" ]; then
  echo "Missing helper: ${SCRIPT_DIR}/lrc_fallback.py"
  exit 1
fi

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

echo "Album URL: $ALBUM_URL"
echo "Album ID:  $ALBUM_ID"
echo "API URL:   $DEEMIX_API_URL"
echo

echo "Logging into Deemix API session..."
LOGIN_BODY="$(jq -nc --arg arl "$ARL_FROM_DEEMIX" '{arl:$arl}')"

LOGIN_RESP="$(curl -sS -c "$COOKIE" -b "$COOKIE" \
  -X POST "${DEEMIX_API_URL}/api/loginArl" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_BODY")"

echo "$LOGIN_RESP" | jq '{status,user:{id:.user.id,name:.user.name},currentChild}'

LOGIN_STATUS="$(echo "$LOGIN_RESP" | jq -r '.status // empty')"

case "$LOGIN_STATUS" in
  1|2|3)
    echo "Deemix API login OK."
    ;;
  *)
    echo "Deemix API login failed."
    exit 1
    ;;
esac

echo
echo "Adding album to Deemix queue..."
ADD_BODY="$(jq -nc --arg url "$ALBUM_URL" --argjson bitrate "$BITRATE" '{url:$url,bitrate:$bitrate}')"

ADD_RESP="$(curl -sS -c "$COOKIE" -b "$COOKIE" \
  -X POST "${DEEMIX_API_URL}/api/addToQueue" \
  -H "Content-Type: application/json" \
  -d "$ADD_BODY")"

echo "$ADD_RESP" | jq .

ADD_RESULT="$(echo "$ADD_RESP" | jq -r '.result // false')"

if [ "$ADD_RESULT" != "true" ]; then
  echo "Failed to add album to Deemix queue."
  exit 1
fi

echo
echo "Waiting for Deemix output folder/files..."

QUEUE_FILE="${DEEMIX_CONFIG_PATH}/queue/album_${ALBUM_ID}_${BITRATE}.json"
ALBUM_DIR=""
LAST_SIG=""
STABLE_COUNT=0

for i in $(seq 1 "$MAX_POLLS"); do
  ALBUM_DIR="$(find "$DEEMIX_DOWNLOAD_PATH" -type d -name "*(${ALBUM_ID})" -print -quit 2>/dev/null || true)"

  FLAC_COUNT=0
  LRC_COUNT=0
  STATUS=""

  if [ -n "$ALBUM_DIR" ]; then
    FLAC_COUNT="$(find "$ALBUM_DIR" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) 2>/dev/null | wc -l)"
    LRC_COUNT="$(find "$ALBUM_DIR" -type f -iname "*.lrc" 2>/dev/null | wc -l)"
  fi

  if [ -f "$QUEUE_FILE" ]; then
    STATUS="$(jq -r '.status // empty' "$QUEUE_FILE" 2>/dev/null || true)"
  fi

  SIG="${STATUS}:${FLAC_COUNT}:${LRC_COUNT}"

  if [ "$SIG" = "$LAST_SIG" ] && [ "$FLAC_COUNT" -gt 0 ]; then
    STABLE_COUNT=$((STABLE_COUNT + 1))
  else
    STABLE_COUNT=0
  fi

  LAST_SIG="$SIG"

  echo "Check $i: status=${STATUS:-none} audio=${FLAC_COUNT} lrc=${LRC_COUNT} stable=${STABLE_COUNT}"

  if [ "$FLAC_COUNT" -gt 0 ] && { [ "$STATUS" = "completed" ] || [ "$STABLE_COUNT" -ge "$STABLE_POLLS" ]; }; then
    break
  fi

  sleep "$POLL_SECONDS"
done

if [ -z "$ALBUM_DIR" ]; then
  echo "Could not find downloaded album folder for album ID $ALBUM_ID"
  exit 1
fi

echo
echo "Album folder found:"
echo "$ALBUM_DIR"
echo

echo "Running timed-LRC fallback processor..."
docker run --rm \
  --entrypoint python3 \
  -e ALBUM_ID="$ALBUM_ID" \
  -e FILE_UID="$FILE_UID" \
  -e FILE_GID="$FILE_GID" \
  -v "${DEEMIX_DOWNLOAD_PATH}:/downloads:rw" \
  -v "${SCRIPT_DIR}/lrc_fallback.py:/tmp/lrc_fallback.py:ro" \
  "$AMA_IMAGE" /tmp/lrc_fallback.py /downloads "$ALBUM_ID"

echo
echo "Fixing host permissions..."
chown -R "${FILE_UID}:${FILE_GID}" "$ALBUM_DIR" || true
chmod -R u+rwX,g+rwX,o+rwX "$ALBUM_DIR" || true

echo
echo "Final file counts:"
find "$ALBUM_DIR" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) | wc -l | awk '{print "Audio:", $1}'
find "$ALBUM_DIR" -type f -iname "*.lrc" | wc -l | awk '{print "LRC:  ", $1}'

echo
echo "Sample LRC:"
FIRST_LRC="$(find "$ALBUM_DIR" -type f -iname "*.lrc" | head -1 || true)"
echo "$FIRST_LRC"
if [ -n "$FIRST_LRC" ]; then
  head -15 "$FIRST_LRC"
fi

echo
echo "Done."
