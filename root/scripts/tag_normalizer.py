#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

from mutagen.flac import FLAC

AUDIO_EXTS = {".flac"}

REMOVE_TAGS = {
    "copyright",
    "source",
    "sourceid",
    "source_id",
    "song_id",
    "songid",
    "sng_id",
    "deezer_id",
    "deezer_track_id",
    "track_id",
}

def clean_spaces(value: str) -> str:
    value = value.replace("_", " ")
    value = value.replace(";", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()

def split_artists(value: str):
    if not value:
        return []

    value = value.replace("\\\\", ";")
    value = value.replace("\\", ";")
    value = value.replace("/", ";")
    value = value.replace(" feat. ", ";")
    value = value.replace(" ft. ", ";")
    value = value.replace(" with ", ";")
    value = value.replace(" & ", ";")
    value = value.replace(",", ";")

    parts = []
    for part in value.split(";"):
        item = clean_spaces(part)
        if item and item.lower() not in [p.lower() for p in parts]:
            parts.append(item)
    return parts

def dedupe_feat_title(title: str) -> str:
    title = clean_spaces(title)

    def repl(match):
        inside = match.group(1)
        artists = split_artists(inside)
        if not artists:
            return ""
        return "(feat. " + " & ".join(artists) + ")"

    title = re.sub(r"\((?:feat\.|ft\.|with)\s+([^)]+)\)", repl, title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def title_has_artist(title: str, artist: str) -> bool:
    return artist.lower() in title.lower()

def normalize_file(path: Path):
    audio = FLAC(path)

    tags = {k.lower(): list(v) for k, v in audio.tags.items()} if audio.tags else {}

    title = audio.get("TITLE", audio.get("title", [path.stem]))[0]
    artist = audio.get("ARTIST", audio.get("artist", [""]))[0]
    album_artist = (
        audio.get("ALBUMARTIST")
        or audio.get("albumartist")
        or audio.get("ALBUM_ARTIST")
        or audio.get("album_artist")
        or audio.get("album_artist_sort")
        or [""]
    )[0]

    title = dedupe_feat_title(title)
    album_artist = clean_spaces(album_artist) or clean_spaces(artist)
    artist_parts = split_artists(artist)

    extra_artists = []
    for item in artist_parts:
        if item.lower() != album_artist.lower() and item.lower() not in [x.lower() for x in extra_artists]:
            extra_artists.append(item)

    # If featured artists are in ARTIST but not in TITLE, append them to TITLE.
    missing_extras = [x for x in extra_artists if not title_has_artist(title, x)]
    if missing_extras:
        title = f"{title} (feat. {' & '.join(missing_extras)})"
        title = dedupe_feat_title(title)

    # Remove unwanted tags.
    for key in list(audio.keys()):
        if key.lower() in REMOVE_TAGS:
            del audio[key]

    # Normalize key fields.
    audio["TITLE"] = [title]
    audio["ARTIST"] = [album_artist]
    audio["ALBUMARTIST"] = [album_artist]

    # Remove lowercase/alternate duplicate album artist keys to reduce confusion.
    for key in list(audio.keys()):
        if key.lower() in {"album_artist", "albumartist"} and key != "ALBUMARTIST":
            try:
                del audio[key]
            except Exception:
                pass

    audio.save()

    new_name = clean_spaces(path.name)
    new_name = new_name.replace(" ; ", " ")
    new_name = re.sub(r"\s+", " ", new_name).strip()

    if new_name != path.name:
        new_path = path.with_name(new_name)
        if not new_path.exists():
            path.rename(new_path)
            path = new_path

    return path, title, album_artist

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/downloads-ama/temp")

    if not root.exists():
        print(f"TAG_NORMALIZER :: folder not found: {root}")
        return 0

    count = 0

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            try:
                new_path, title, album_artist = normalize_file(path)
                print(f"TAG_NORMALIZER :: {new_path.name} :: ARTIST={album_artist} :: TITLE={title}")
                count += 1
            except Exception as exc:
                print(f"TAG_NORMALIZER :: ERROR :: {path} :: {exc}")

    print(f"TAG_NORMALIZER :: processed={count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
