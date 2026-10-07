#!/bin/bash
# Run only in a disposable test container with private /config and /downloads-ama mounts.
set -o pipefail
ALBUM_ID="${1:-1367549}"
[[ "$ALBUM_ID" =~ ^[0-9]+$ ]] || exit 1
mkdir -p /config/{scripts,cache,list,ignore,logs} /downloads-ama
cp /scripts/* /config/scripts/ || exit 1
if [ -n "${AMA_TEST_PATCH_ROOT:-}" ]; then
    cp "$AMA_TEST_PATCH_ROOT"/root/scripts/* /config/scripts/ || exit 1
fi
# Load the actual workflow functions without starting the normal artist scan.
source <(sed '/^Main$/,$d' /config/scripts/download.bash)
Configuration
albumdata="$(curl -sSL --fail "https://api.deezer.com/album/$ALBUM_ID")" || exit 1
artistid="$(printf '%s' "$albumdata" | jq -r '.artist.id')"
[[ "$artistid" =~ ^[0-9]+$ ]] || exit 1
ArtistInfo "$artistid"
albumlistdata="$(printf '%s' "$albumdata" | jq '[.]')"
albumids=("$ALBUM_ID")
albumcount=1
logheaderstart="PARTIAL INTEGRATION TEST"
logheader="$logheaderstart"
ProcessArtist
RECORD="/config/partial-albums/$ALBUM_ID.json"
if [ ! -f "$RECORD" ]; then
    echo 'No partial record: inspect whether the album completed or processing failed.'
    exit 1
fi
printf '\n===== RETAINED PARTIAL ALBUM =====\n'
jq '{album_id,expected,audio_count,missing,next_retry,target,catalog_error}' "$RECORD"
TARGET="$(jq -r '.target' "$RECORD")"
find "$TARGET" -type f \( -iname '*.mp3' -o -iname '*.flac' -o -iname '*.m4a' -o -iname '*.opus' \) -exec sha256sum {} + > /config/original-audio.sha256
# Simulate tomorrow for this disposable test record only.
python3 - "$RECORD" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]); data = json.loads(p.read_text()); data['next_retry'] = 0
p.write_text(json.dumps(data, indent=2))
PY
printf '\n===== MISSING-TRACK RETRY =====\n'
RetryPartialAlbums
printf '\n===== EXISTING AUDIO CHECK =====\n'
sha256sum -c /config/original-audio.sha256 || exit 1
if [ -f "$RECORD" ]; then
    printf '\n===== STILL PENDING =====\n'
    jq '{album_id,expected,audio_count,missing,next_retry,catalog_error}' "$RECORD"
elif [ -f "/config/logs/downloads/$ALBUM_ID" ]; then
    echo 'Album complete; partial record cleared.'
else
    echo 'ERROR: Partial record and completion marker are both missing.'
    exit 1
fi
