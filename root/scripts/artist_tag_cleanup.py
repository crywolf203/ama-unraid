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

def first_artist(value):
    value = str(value or "").replace("\\\\", ";").replace("\\", ";")
    for sep in [";", "/", ","]:
        if sep in value:
            value = value.split(sep)[0]
            break
    return clean(value)

def get_values(audio, names):
    out = []
    wanted = {x.lower() for x in names}
    for key in audio.keys():
        if key.lower() in wanted:
            out.extend(audio.get(key, []))
    return [clean(x) for x in out if clean(x)]

def process(path):
    audio = FLAC(path)

    album_artist_values = get_values(audio, [
        "ALBUMARTIST", "albumartist", "ALBUM_ARTIST", "album_artist", "Album Artist"
    ])
    artist_values = get_values(audio, ["ARTIST", "artist"])

    album_artist = ""
    if album_artist_values:
        album_artist = first_artist(album_artist_values[0])
    elif artist_values:
        album_artist = first_artist(artist_values[0])

    if not album_artist:
        print(f"ARTIST_CLEANUP :: SKIP no album artist :: {path}")
        return

    title_values = get_values(audio, ["TITLE", "title"])
    title = title_values[0] if title_values else None

    for key in list(audio.keys()):
        if key.lower() in ARTIST_TAGS or key.lower() in REMOVE_TAGS:
            del audio[key]

    if title:
        audio["TITLE"] = [title]

    audio["ARTIST"] = [album_artist]
    audio["ALBUMARTIST"] = [album_artist]
    audio.save()

    print(f"ARTIST_CLEANUP :: {path.name} :: ARTIST={album_artist}")

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/downloads-ama/temp")
    count = 0
    for path in sorted(root.rglob("*.flac")):
        process(path)
        count += 1
    print(f"ARTIST_CLEANUP :: processed={count}")

if __name__ == "__main__":
    main()
