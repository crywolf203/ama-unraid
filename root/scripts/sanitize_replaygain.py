#!/usr/bin/env python3
from mutagen import File
from pathlib import Path
import re
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/downloads-ama/temp")

removed = 0
checked = 0

for f in target.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in {".flac", ".mp3", ".m4a", ".opus"}:
        continue

    checked += 1
    audio = File(f)

    if not audio or not audio.tags:
        continue

    keys_to_delete = []

    for k, v in audio.tags.items():
        key = str(k).lower()

        if "gain" not in key and "peak" not in key and "r128" not in key:
            continue

        value = str(v[0] if isinstance(v, list) else v)

        bad = False

        if "nan" in value.lower() or "inf" in value.lower():
            bad = True

        m = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)

        if m:
            number = float(m.group(0))

            # Normal ReplayGain values are usually within roughly -20 to +20 dB.
            # Anything beyond 60 dB is definitely broken.
            if "gain" in key and abs(number) > 60:
                bad = True

            # Peak should not be negative.
            if "peak" in key and number < 0:
                bad = True

        if bad:
            keys_to_delete.append(k)

    if keys_to_delete:
        print(f"REPLAYGAIN_SANITIZE :: {f}")
        for k in keys_to_delete:
            print(f"REPLAYGAIN_SANITIZE :: removing {k}: {audio.tags[k]}")
            del audio.tags[k]
            removed += 1
        audio.save()

print(f"REPLAYGAIN_SANITIZE :: checked={checked} removed_bad_tags={removed}")
