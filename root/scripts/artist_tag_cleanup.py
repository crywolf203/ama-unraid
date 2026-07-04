#!/usr/bin/env python3
from pathlib import Path
import re
import sys
from mutagen.flac import FLAC

REMOVE_TAGS = {
    "copyright", "source", "sourceid", "source_id",
    "song_id", "songid", "sng_id",
    "deezer_id", "deezer_track_id", "track_id",
}

ARTIST_TAGS = {
    "artist", "artists",
    "albumartist", "album_artist", "album artist",
    "albumartists", "albumartistsort", "album_artist_sort",
}

def clean(value):
    value = str(value or "").replace("_", " ").strip()
    return re.sub(r"\s+", " ", value)

def norm(value):
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())

def split_artists(value):
    value = str(value or "")
    value = value.replace("\\\\", ";").replace("\\", ";")
    value = re.sub(r"\s+(?:feat\.|ft\.|with)\s+", ";", value, flags=re.I)

    # Do not split names like "Ty Dolla $ign" on "$"; only common artist separators.
    for sep in [";", "/", ","]:
        value = value.replace(sep, ";")

    out = []
    for part in value.split(";"):
        part = clean(part)
        if part and norm(part) not in [norm(x) for x in out]:
            out.append(part)
    return out

def get_values(audio, names):
    wanted = {x.lower() for x in names}
    out = []
    for key in audio.keys():
        if key.lower() in wanted:
            out.extend(audio.get(key, []))
    return [clean(x) for x in out if clean(x)]

def get_title(audio, path):
    vals = get_values(audio, ["TITLE", "title"])
    return vals[0] if vals else path.stem

def get_main_artist(audio):
    album_artist_values = get_values(audio, [
        "ALBUMARTIST", "albumartist", "ALBUM_ARTIST", "album_artist", "Album Artist"
    ])
    artist_values = get_values(audio, ["ARTIST", "artist", "ARTISTS", "artists"])

    if album_artist_values:
        parts = split_artists(album_artist_values[0])
        if parts:
            return parts[0]

    if artist_values:
        parts = split_artists(";".join(artist_values))
        if parts:
            return parts[0]

    return ""

def get_track_artists(audio):
    artist_values = get_values(audio, ["ARTIST", "artist", "ARTISTS", "artists"])
    return split_artists(";".join(artist_values))

def title_contains_artist(title, artist):
    return norm(artist) in norm(title)

def merge_featured_into_title(title, extra_artists):
    title = clean(title)
    existing = []

    def remove_existing_feat(match):
        inside = match.group(1)
        for artist in split_artists(inside):
            if norm(artist) not in [norm(x) for x in existing]:
                existing.append(artist)
        return ""

    base = re.sub(
        r"\s*\((?:feat\.|ft\.|with)\s+([^)]+)\)",
        remove_existing_feat,
        title,
        flags=re.I
    )
    base = clean(base)

    merged = []
    for artist in existing + extra_artists:
        artist = clean(artist)
        if artist and norm(artist) not in [norm(x) for x in merged]:
            merged.append(artist)

    if merged:
        return f"{base} (feat. {' & '.join(merged)})"
    return base

def process(path):
    audio = FLAC(path)

    title = get_title(audio, path)
    main_artist = get_main_artist(audio)

    if not main_artist:
        print(f"ARTIST_CLEANUP :: SKIP no main artist :: {path.name}")
        return False

    track_artists = get_track_artists(audio)

    extra_artists = []
    for artist in track_artists:
        if norm(artist) == norm(main_artist):
            continue
        if title_contains_artist(title, artist):
            continue
        if norm(artist) not in [norm(x) for x in extra_artists]:
            extra_artists.append(artist)

    fixed_title = merge_featured_into_title(title, extra_artists) if extra_artists else title

    for key in list(audio.keys()):
        if key.lower() in ARTIST_TAGS or key.lower() in REMOVE_TAGS:
            del audio[key]

    audio["TITLE"] = [fixed_title]
    audio["ARTIST"] = [main_artist]
    audio["ALBUMARTIST"] = [main_artist]
    audio.save()

    if fixed_title != title:
        print(f"ARTIST_CLEANUP :: {path.name} :: ARTIST={main_artist} :: TITLE={fixed_title}")
    else:
        print(f"ARTIST_CLEANUP :: {path.name} :: ARTIST={main_artist}")

    return True

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/downloads-ama/temp")

    if not root.exists():
        print(f"ARTIST_CLEANUP :: folder not found: {root}")
        return 0

    count = 0
    for path in sorted(root.rglob("*.flac")):
        try:
            if process(path):
                count += 1
        except Exception as exc:
            print(f"ARTIST_CLEANUP :: ERROR :: {path} :: {exc}")

    print(f"ARTIST_CLEANUP :: processed={count}")

# Also clean artist tags for Deemix bitrate-fallback files such as MP3/M4A/OPUS.
# The original cleanup may only touch FLAC, which leaves fallback MP3s at processed=0.
if find "${TEMP_DIR:-/downloads-ama/temp}" -maxdepth 1 -type f \( -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.opus" \) -print -quit 2>/dev/null | grep -q .; then
  python3 - "${TEMP_DIR:-/downloads-ama/temp}" <<'ARTIST_CLEANUP_FALLBACK_PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
exts = {".mp3", ".m4a", ".opus"}
processed = 0

try:
    from mutagen import File as MutagenFile
except Exception as exc:
    print(f"ARTIST_CLEANUP :: fallback_warn=mutagen unavailable: {exc}")
    raise SystemExit(0)

for audio in sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in exts):
    try:
        tags = MutagenFile(audio, easy=True)
        if tags is None:
            print(f"ARTIST_CLEANUP :: {audio.name} :: SKIP no tag handler")
            continue

        artist_vals = tags.get("artist", [])
        albumartist_vals = tags.get("albumartist", [])
        artist = artist_vals[0].strip() if artist_vals and artist_vals[0] else ""

        # Preserve Deemix's artist tag, but ensure fallback files are saved
        # through Mutagen and have albumartist when possible.
        if artist:
            tags["artist"] = [artist]
            if not albumartist_vals:
                tags["albumartist"] = [artist]

        tags.save()
        processed += 1
        print(f"ARTIST_CLEANUP :: {audio.name} :: ARTIST={artist or '<missing>'}")
    except Exception as exc:
        print(f"ARTIST_CLEANUP :: {audio.name} :: WARN {exc}")

print(f"ARTIST_CLEANUP :: fallback_processed={processed}")
ARTIST_CLEANUP_FALLBACK_PY
fi

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
