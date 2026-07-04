#!/usr/bin/env bash
set -Eeuo pipefail

ALBUM_URL="${1:-${DEEMIX_DIRECT_URL:-}}"

if [ -z "$ALBUM_URL" ]; then
  echo "DEEMIX_DIRECT :: ERROR: No album URL provided"
  exit 1
fi

mkdir -p /config/logs

ALBUM_ID="$(printf '%s' "$ALBUM_URL" | grep -oE '(album|track)/[0-9]+' | tail -1 | cut -d/ -f2 || true)"
if [ -z "$ALBUM_ID" ]; then
  ALBUM_ID="$(date +%s)"
fi

LOG_FILE="/config/logs/deemix-direct-${ALBUM_ID}-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

fix_permissions() {
  local target="$1"

  if [ -e "$target" ]; then
    log "DEEMIX_DIRECT :: Fixing permissions on: $target"
    chown -R "${PUID:-99}:${PGID:-100}" "$target" 2>/dev/null || true
    find "$target" -type d -exec chmod "${FOLDER_PERMISSIONS:-777}" {} + 2>/dev/null || true
    find "$target" -type f -exec chmod "${FILE_PERMISSIONS:-777}" {} + 2>/dev/null || true
  fi
}

check_lrc_sidecars() {
  local check_dir="$1"
  local audio_count=0
  local lrc_found=0
  local lrc_missing=0

  log "DEEMIX_DIRECT :: Checking LRC sidecars in: $check_dir"

  while IFS= read -r -d '' audio_file; do
    audio_count=$((audio_count + 1))
    lrc_file="${audio_file%.*}.lrc"

    if [ -f "$lrc_file" ]; then
      lrc_found=$((lrc_found + 1))
    else
      lrc_missing=$((lrc_missing + 1))
      log "DEEMIX_DIRECT :: Missing LRC: $(basename "$audio_file")"
    fi
  done < <(find "$check_dir" -type f \( \
    -iname "*.flac" -o \
    -iname "*.mp3" -o \
    -iname "*.m4a" -o \
    -iname "*.opus" \
  \) -print0 2>/dev/null)

  log "DEEMIX_DIRECT :: LRC summary: audio=$audio_count lrc_found=$lrc_found lrc_missing=$lrc_missing"
}


normalize_explicit_filenames() {
  local album_folder="$1"
  local album_id="$2"

  if [ "${DEEMIX_DIRECT_APPEND_EXPLICIT:-true}" != "true" ]; then
    log "DEEMIX_DIRECT :: Explicit filename labels disabled"
    return
  fi

  
  ALBUM_FOLDER="$album_folder" ALBUM_ID="$album_id" python3 - <<'PY'
import json
import os
import re
import urllib.request
from pathlib import Path

root = Path(os.environ["ALBUM_FOLDER"])
album_id = os.environ.get("ALBUM_ID", "").strip()

audio_exts = {".flac", ".mp3", ".m4a", ".opus"}

def fetch_album(album_id):
    if not album_id:
        return {}
    url = f"https://api.deezer.com/album/{album_id}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AMA-Unraid/2.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))

def clean_existing_label(stem):
    return re.search(r"\((explicit|clean)\)\s*$", stem, flags=re.I) is not None

def position_key(track):
    disk = track.get("disk_number") or track.get("disk") or 1
    pos = track.get("track_position") or track.get("track_position_on_disk") or track.get("position")
    try:
        disk = int(disk)
    except Exception:
        disk = 1
    try:
        pos = int(pos)
    except Exception:
        return None

    return f"{disk}{pos:02d}"

def rename_with_sidecar(path, explicit):
    if not explicit:
        return False

    stem = path.stem

    if clean_existing_label(stem):
        return False

    new_path = path.with_name(f"{stem} (Explicit){path.suffix}")

    if new_path.exists():
        return False

    old_lrc = path.with_suffix(".lrc")
    new_lrc = new_path.with_suffix(".lrc")

    path.rename(new_path)

    if old_lrc.exists() and not new_lrc.exists():
        old_lrc.rename(new_lrc)

    print(f"EXPLICIT_FILENAME :: renamed :: {path.name} -> {new_path.name}")
    return True

explicit_by_position = {}

try:
    album = fetch_album(album_id)
    tracks = ((album.get("tracks") or {}).get("data") or [])

    for track in tracks:
        key = position_key(track)
        if not key:
            continue
        explicit_by_position[key] = bool(track.get("explicit_lyrics"))
except Exception as exc:
    print(f"EXPLICIT_FILENAME :: warning :: album API failed: {exc}")

renamed = 0
checked = 0

for path in sorted(root.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in audio_exts:
        continue

    checked += 1
    match = re.match(r"^(\d{3})\s+-\s+", path.name)
    if not match:
        continue

    key = match.group(1)
    explicit = explicit_by_position.get(key, False)

    if rename_with_sidecar(path, explicit):
        renamed += 1

print(f"EXPLICIT_FILENAME :: checked={checked} renamed={renamed}")
PY
}

TEMP_DIR="/downloads-ama/temp"
DEEMIX_CONFIG_PATH="${DEEMIX_CONFIG_PATH:-/deemix-config}"
XDG_CONFIG_HOME="/config/deemix/xdg"
DEEMIX_XDG_DIR="$XDG_CONFIG_HOME/deemix"
DEEMIX_CONFIG_JSON="$DEEMIX_XDG_DIR/config.json"

mkdir -p "$TEMP_DIR" "$DEEMIX_XDG_DIR"

log "DEEMIX_DIRECT :: Log file: $LOG_FILE"
log "DEEMIX_DIRECT :: Album URL: $ALBUM_URL"
log "DEEMIX_DIRECT :: Album ID:  $ALBUM_ID"
log "DEEMIX_DIRECT :: Temp dir:   $TEMP_DIR"
log "DEEMIX_DIRECT :: Flow:       direct-temp"

log "DEEMIX_DIRECT :: Cleaning AMA temp before album"
find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$TEMP_DIR"

if [ -f "$DEEMIX_CONFIG_PATH/login.json" ]; then
  cp -f "$DEEMIX_CONFIG_PATH/login.json" "$DEEMIX_XDG_DIR/login.json"
fi

export XDG_CONFIG_HOME

python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path("/config/deemix/xdg/deemix/config.json")
config_path.parent.mkdir(parents=True, exist_ok=True)

config = {}
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
    except Exception:
        config = {}

temp_dir = "/downloads-ama/temp"

config["downloadLocation"] = temp_dir
explicit_suffix = " %explicit%" if os.environ.get("AMA_ALBUM_EXPLICIT", "").strip().lower() == "true" else ""
config["albumTracknameTemplate"] = "%discnumber%%tracknumber% - %title%" + explicit_suffix
config["tracknameTemplate"] = "%discnumber%%tracknumber% - %title%" + explicit_suffix
config["createSingleFolder"] = True
config["queueConcurrency"] = int(os.environ.get("DEEMIX_QUEUE_CONCURRENCY", "1"))
config["concurrentDownloads"] = int(os.environ.get("DEEMIX_QUEUE_CONCURRENCY", "1"))
config["maxConcurrentDownloads"] = int(os.environ.get("DEEMIX_QUEUE_CONCURRENCY", "1"))

config_path.write_text(json.dumps(config, indent=2))

print(f"DEEMIX_DIRECT :: Wrote Deemix config: {config_path}")
print(f"DEEMIX_DIRECT :: albumTracknameTemplate={config['albumTracknameTemplate']}")
print(f"DEEMIX_DIRECT :: tracknameTemplate={config['tracknameTemplate']}")
print(f"DEEMIX_DIRECT :: createSingleFolder={config['createSingleFolder']}")
print(f"DEEMIX_DIRECT :: queueConcurrency={config['queueConcurrency']}")
PY

FORMAT_UPPER="$(printf '%s' "${FORMAT:-FLAC}" | tr '[:lower:]' '[:upper:]')"

case "$FORMAT_UPPER" in
  FLAC|LOSSLESS|ALAC|AAC|OPUS)
    CLI_BITRATE="flac"
    ;;
  MP3|MP3_320|320)
    CLI_BITRATE="320"
    ;;
  MP3_128|128)
    CLI_BITRATE="128"
    ;;
  *)
    CLI_BITRATE="flac"
    ;;
esac

log "DEEMIX_DIRECT :: Bitrate: $CLI_BITRATE"

set +e
deemix -b "$CLI_BITRATE" -p "$TEMP_DIR" "$ALBUM_URL"
DEEMIX_EXIT="$?"
set -e

if [ "$DEEMIX_EXIT" -ne 0 ]; then
  log "DEEMIX_DIRECT :: ERROR: deemix exited with code $DEEMIX_EXIT"
  exit "$DEEMIX_EXIT"
fi

if grep -qiE "Traceback|MutagenError|FileNotFoundError|\[Errno [0-9]+\]" "$LOG_FILE"; then
  log "DEEMIX_DIRECT :: ERROR: deemix log contains a download/tagging error"
  exit 1
fi

FIRST_MEDIA_FILE="$(find "$TEMP_DIR" -mindepth 1 -maxdepth 6 -type f \( \
  -iname "*.flac" -o \
  -iname "*.mp3" -o \
  -iname "*.m4a" -o \
  -iname "*.opus" \
\) 2>/dev/null | head -1 || true)"

if [ -z "$FIRST_MEDIA_FILE" ] || [ ! -f "$FIRST_MEDIA_FILE" ]; then
  log "DEEMIX_DIRECT :: ERROR: No downloaded audio files found in AMA temp"
  find "$TEMP_DIR" -mindepth 1 -maxdepth 6 -print 2>/dev/null | sed "s/^/DEEMIX_DIRECT :: TEMP DEBUG :: /" || true
  exit 1
fi

ALBUM_FOLDER="$(dirname "$FIRST_MEDIA_FILE")"
log "DEEMIX_DIRECT :: Album folder before LRC ID check: $ALBUM_FOLDER"

# lrc_fallback.py expects a downloads root plus album_id.
# Make sure the downloaded album folder includes the album ID before running fallback.
if [ -n "${ALBUM_ID:-}" ] && [[ "$ALBUM_FOLDER" != *"[$ALBUM_ID]" ]]; then
  ALBUM_FOLDER_WITH_ID="${ALBUM_FOLDER} [$ALBUM_ID]"
  log "DEEMIX_DIRECT :: Adding album ID to folder for LRC fallback: $ALBUM_FOLDER_WITH_ID"
  rm -rf "$ALBUM_FOLDER_WITH_ID"
  mv "$ALBUM_FOLDER" "$ALBUM_FOLDER_WITH_ID"
  ALBUM_FOLDER="$ALBUM_FOLDER_WITH_ID"
fi

log "DEEMIX_DIRECT :: Running LRC fallback root: $TEMP_DIR"
log "DEEMIX_DIRECT :: Running LRC fallback album ID: $ALBUM_ID"

if [ -f /config/scripts/lrc_fallback.py ]; then
  python3 /config/scripts/lrc_fallback.py "$TEMP_DIR" "$ALBUM_ID"
else
  log "DEEMIX_DIRECT :: lrc_fallback.py not found, skipping LRC fallback"
fi

check_lrc_sidecars "$ALBUM_FOLDER"

fix_permissions "$ALBUM_FOLDER"

log "DEEMIX_DIRECT :: Flattening downloaded files into AMA temp root"

COVER_SRC="$(find "$ALBUM_FOLDER" -maxdepth 3 -type f \( \
  -iname "cover.jpg" -o \
  -iname "folder.jpg" -o \
  -iname "*.jpg" -o \
  -iname "*.png" \
\) 2>/dev/null | head -1 || true)"

if [ -n "$COVER_SRC" ] && [ -f "$COVER_SRC" ]; then
  cp -f "$COVER_SRC" "$TEMP_DIR/cover.jpg"
  log "DEEMIX_DIRECT :: Copied album art: $COVER_SRC"
else
  log "DEEMIX_DIRECT :: No album art found to copy"
fi

MOVED_MEDIA_COUNT=0

while IFS= read -r -d '' src; do
  base="$(basename "$src")"
  dest="$TEMP_DIR/$base"

  if [ "$src" != "$dest" ]; then
    mv -f "$src" "$dest"
  fi

  MOVED_MEDIA_COUNT=$((MOVED_MEDIA_COUNT + 1))
done < <(find "$ALBUM_FOLDER" -type f \( \
  -iname "*.flac" -o \
  -iname "*.mp3" -o \
  -iname "*.m4a" -o \
  -iname "*.opus" -o \
  -iname "*.lrc" \
\) -print0 2>/dev/null)

log "DEEMIX_DIRECT :: Moved media/LRC files into AMA temp: $MOVED_MEDIA_COUNT"

if [ "$MOVED_MEDIA_COUNT" -eq 0 ]; then
  log "DEEMIX_DIRECT :: ERROR: No media/LRC files moved into AMA temp"
  exit 1
fi

log "DEEMIX_DIRECT :: Removing leftover temp subfolders"
find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true

fix_permissions "$TEMP_DIR"
fix_permissions "/config/logs"

check_lrc_sidecars "$TEMP_DIR"

TEMP_AUDIO_COUNT="$(find "$TEMP_DIR" -maxdepth 1 -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) 2>/dev/null | wc -l)"
TEMP_LRC_COUNT="$(find "$TEMP_DIR" -maxdepth 1 -type f -iname "*.lrc" 2>/dev/null | wc -l)"
TEMP_COVER_COUNT="$(find "$TEMP_DIR" -maxdepth 1 -type f \( -iname "cover.jpg" -o -iname "folder.jpg" \) 2>/dev/null | wc -l)"

log "DEEMIX_DIRECT :: Temp audio count: $TEMP_AUDIO_COUNT"
log "DEEMIX_DIRECT :: Temp LRC count:   $TEMP_LRC_COUNT"
log "DEEMIX_DIRECT :: Temp cover count: $TEMP_COVER_COUNT"

if [ "$TEMP_AUDIO_COUNT" -eq 0 ]; then
  log "DEEMIX_DIRECT :: ERROR: No audio files in AMA temp after flattening"
  exit 1
fi

log "DEEMIX_DIRECT :: Done"
