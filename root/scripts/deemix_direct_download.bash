#!/usr/bin/env bash
set -euo pipefail

ALBUM_URL="${1:-}"

if [ -z "$ALBUM_URL" ]; then
  echo "Usage: deemix_direct_download.bash <deezer album url>"
  exit 1
fi

DEEMIX_CONFIG_PATH="${DEEMIX_CONFIG_PATH:-/deemix-config}"
DEEMIX_DIRECT_STAGING_ROOT="${DEEMIX_DIRECT_STAGING_ROOT:-/config/deemix-direct-staging}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/config/deemix/xdg}"
FILE_UID="${PUID:-99}"
FILE_GID="${PGID:-100}"

ALBUM_ID="$(printf '%s' "$ALBUM_URL" | sed -nE 's#.*album/([0-9]+).*#\1#p')"

if [ -z "$ALBUM_ID" ]; then
  echo "DEEMIX_DIRECT :: Could not parse album ID from: $ALBUM_URL"
  exit 1
fi

mkdir -p /config/logs "$DEEMIX_DIRECT_STAGING_ROOT"

LOG_FILE="/config/logs/deemix-direct-${ALBUM_ID}-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

fix_permissions() {
  target="$1"

  if [ -e "$target" ]; then
    log "DEEMIX_DIRECT :: Fixing permissions on: $target"
    chown -R "${FILE_UID}:${FILE_GID}" "$target" 2>/dev/null || true
    find "$target" -type d -exec chmod 777 {} + 2>/dev/null || true
    find "$target" -type f -exec chmod 666 {} + 2>/dev/null || true
  fi
}

log_lrc_status() {
  target="$1"

  log "DEEMIX_DIRECT :: Checking LRC sidecars in: $target"

  missing=0
  total=0

  while IFS= read -r audio; do
    total=$((total + 1))
    base="${audio%.*}"
    lrc="${base}.lrc"

    if [ ! -f "$lrc" ]; then
      missing=$((missing + 1))
      log "DEEMIX_DIRECT :: Missing LRC: $(basename "$audio")"
    fi
  done < <(find "$target" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) | sort)

  found=$((total - missing))
  log "DEEMIX_DIRECT :: LRC summary: audio=${total} lrc_found=${found} lrc_missing=${missing}"
}

copy_single_cover() {
  src_dir="$1"
  dest_dir="$2"

  cover=""

  # Prefer true album-cover style names.
  for pattern in \
    "cover.jpg" "cover.jpeg" "cover.png" \
    "folder.jpg" "folder.jpeg" "folder.png" \
    "front.jpg" "front.jpeg" "front.png" \
    "album.jpg" "album.jpeg" "album.png"
  do
    cover="$(find "$src_dir" -type f -iname "$pattern" | sort | head -n 1 || true)"
    if [ -n "$cover" ]; then
      break
    fi
  done

  # Fallback to the first image, but still normalize it to cover.jpg.
  if [ -z "$cover" ]; then
    cover="$(find "$src_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | sort | head -n 1 || true)"
  fi

  if [ -n "$cover" ]; then
    log "DEEMIX_DIRECT :: Copying album art as cover.jpg from: $(basename "$cover")"
    cp -a "$cover" "$dest_dir/cover.jpg"
  else
    log "DEEMIX_DIRECT :: No album art found to copy"
  fi
}


write_deemix_direct_config() {
  mkdir -p "$XDG_CONFIG_HOME/deemix"

  python3 - "$XDG_CONFIG_HOME/deemix/config.json" <<'PYCFG'
import json
import os
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
config_path.parent.mkdir(parents=True, exist_ok=True)

if config_path.exists():
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        config = {}
else:
    config = {}

# Filename/folder behavior
config["downloadLocation"] = os.environ.get("DEEMIX_DIRECT_DOWNLOAD_LOCATION", "/config/music")
config["albumTracknameTemplate"] = os.environ.get("DEEMIX_ALBUM_TRACK_TEMPLATE", "%discnumber%%tracknumber% - %title%")
config["tracknameTemplate"] = os.environ.get("DEEMIX_TRACK_TEMPLATE", "%discnumber%%tracknumber% - %title%")
config["albumNameTemplate"] = os.environ.get("DEEMIX_ALBUM_TEMPLATE", "%artist% - %album%")
config["coverImageTemplate"] = "cover"

# Keep Deemix's output predictable for AMA staging
config["createArtistFolder"] = False
config["createAlbumFolder"] = True
config["createCDFolder"] = False
config["createSingleFolder"] = True
config["padTracks"] = True
config["paddingSize"] = "0"
config["illegalCharacterReplacer"] = " "

# Artwork
config["saveArtwork"] = True
config["saveArtworkArtist"] = False
config["localArtworkFormat"] = "jpg"

# Lyrics
config["syncedLyrics"] = True

tags = config.setdefault("tags", {})
tags["lyrics"] = True
tags["syncedLyrics"] = True
tags["discNumber"] = True
tags["trackNumber"] = True
tags["trackTotal"] = False
tags["discTotal"] = False
tags["cover"] = True

config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(f"DEEMIX_DIRECT :: Wrote Deemix config: {config_path}")
print(f"DEEMIX_DIRECT :: albumTracknameTemplate={config['albumTracknameTemplate']}")
print(f"DEEMIX_DIRECT :: tracknameTemplate={config['tracknameTemplate']}")
print(f"DEEMIX_DIRECT :: createSingleFolder={config['createSingleFolder']}")
PYCFG
}

log "DEEMIX_DIRECT :: Log file: $LOG_FILE"

for cmd in deemix find python3 cp mkdir rm sed tee date chmod chown; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "DEEMIX_DIRECT :: Missing required command inside container: $cmd"
    exit 1
  fi
done

mkdir -p "$XDG_CONFIG_HOME/deemix" "$DEEMIX_DIRECT_STAGING_ROOT" /downloads-ama/temp

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
    log "DEEMIX_DIRECT :: ARL missing from ${DEEMIX_CONFIG_PATH}/login.json"
    exit 1
  fi
  echo -n "$ARL_FROM_LOGIN" > "$XDG_CONFIG_HOME/deemix/.arl"
else
  log "DEEMIX_DIRECT :: Missing ARL_TOKEN and missing ${DEEMIX_CONFIG_PATH}/login.json"
  exit 1
fi

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

RUN_DIR="${DEEMIX_DIRECT_STAGING_ROOT}/${ALBUM_ID}"
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR"

write_deemix_direct_config

log "DEEMIX_DIRECT :: Album URL: $ALBUM_URL"
log "DEEMIX_DIRECT :: Album ID:  $ALBUM_ID"
log "DEEMIX_DIRECT :: Staging:   $RUN_DIR"
log "DEEMIX_DIRECT :: Bitrate:   $CLI_BITRATE"

deemix -b "$CLI_BITRATE" -p "$RUN_DIR" "$ALBUM_URL"

ALBUM_DIR="$(find "$RUN_DIR" -type d -name "*(${ALBUM_ID})" -print -quit 2>/dev/null || true)"

if [ -z "$ALBUM_DIR" ]; then
  ALBUM_DIR="$(find "$RUN_DIR" -type f \( -iname "*.flac" -o -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) -printf '%h\n' 2>/dev/null | sort -u | head -n 1 || true)"
fi

if [ -z "$ALBUM_DIR" ]; then
  log "DEEMIX_DIRECT :: Could not find downloaded album folder for album ID $ALBUM_ID"
  fix_permissions "$RUN_DIR"
  exit 1
fi

case "$(basename "$ALBUM_DIR")" in
  *"(${ALBUM_ID})"*)
    ;;
  *)
    FIXED_ALBUM_DIR="${ALBUM_DIR} (${ALBUM_ID})"
    mv "$ALBUM_DIR" "$FIXED_ALBUM_DIR"
    ALBUM_DIR="$FIXED_ALBUM_DIR"
    ;;
esac

log "DEEMIX_DIRECT :: Album folder: $ALBUM_DIR"

if [ -f /config/scripts/lrc_fallback.py ]; then
  python3 /config/scripts/lrc_fallback.py "$RUN_DIR" "$ALBUM_ID" || true
elif [ -f /scripts/lrc_fallback.py ]; then
  python3 /scripts/lrc_fallback.py "$RUN_DIR" "$ALBUM_ID" || true
fi

log_lrc_status "$ALBUM_DIR"
fix_permissions "$RUN_DIR"

find /downloads-ama/temp -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true

log "DEEMIX_DIRECT :: Copying clean staged audio/LRC files into AMA temp folder"

copy_count=0

while IFS= read -r src; do
  base="$(basename "$src")"
  dest="/downloads-ama/temp/$base"

  if [ -e "$dest" ]; then
    copy_count=$((copy_count + 1))
    dest="/downloads-ama/temp/${copy_count}-${base}"
  fi

  cp -a "$src" "$dest"
done < <(find "$ALBUM_DIR" -type f \( \
  -iname "*.flac" -o \
  -iname "*.mp3" -o \
  -iname "*.m4a" -o \
  -iname "*.opus" -o \
  -iname "*.lrc" \
\) | sort)

copy_single_cover "$ALBUM_DIR" /downloads-ama/temp

fix_permissions /downloads-ama/temp
fix_permissions /config/logs

log_lrc_status /downloads-ama/temp

log "DEEMIX_DIRECT :: Temp audio count: $(find /downloads-ama/temp -type f \( -iname '*.flac' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.opus' \) | wc -l)"
log "DEEMIX_DIRECT :: Temp LRC count:   $(find /downloads-ama/temp -type f -iname '*.lrc' | wc -l)"
log "DEEMIX_DIRECT :: Temp cover count: $(find /downloads-ama/temp -maxdepth 1 -type f -iname 'cover.jpg' | wc -l)"
log "DEEMIX_DIRECT :: Done"
