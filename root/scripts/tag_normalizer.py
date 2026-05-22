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

def merge_feat_artists(title: str, extra_artists):
    title = clean_spaces(title)
    existing = []

    def remove_feat(match):
        inside = match.group(1)
        for item in split_artists(inside):
            if item.lower() not in [x.lower() for x in existing]:
                existing.append(item)
        return ""

    base = re.sub(r"\s*\((?:feat\.|ft\.|with)\s+([^)]+)\)", remove_feat, title, flags=re.I)
    base = clean_spaces(base)

    merged = []
    for item in existing + list(extra_artists):
        item = clean_spaces(item)
        if item and item.lower() not in [x.lower() for x in merged]:
            merged.append(item)

    if merged:
        return f"{base} (feat. {' & '.join(merged)})"
    return base


def normalize_file(path: Path):
    audio = FLAC(path)

    tags = {k.lower(): list(v) for k, v in audio.tags.items()} if audio.tags else {}

    title = (audio.get("TITLE") or audio.get("title") or [path.stem])[0]

    artist_values = []
    for key in ("ARTIST", "artist"):
        artist_values.extend(audio.get(key, []))
    artist = ";".join(str(x) for x in artist_values if str(x).strip())

    album_artist_values = []
    for key in ("ALBUMARTIST", "albumartist", "ALBUM_ARTIST", "album_artist", "album_artist_sort"):
        album_artist_values.extend(audio.get(key, []))
    album_artist = ";".join(str(x) for x in album_artist_values if str(x).strip())

    album_artist_candidates = split_artists(album_artist)
    artist_parts = split_artists(artist)

    if album_artist_candidates:
        album_artist = album_artist_candidates[0]
    elif artist_parts:
        album_artist = artist_parts[0]
    else:
        album_artist = clean_spaces(artist)

    title = dedupe_feat_title(title)

    extra_artists = []
    for item in artist_parts:
        if item.lower() != album_artist.lower() and item.lower() not in [x.lower() for x in extra_artists]:
            extra_artists.append(item)

    # Move all non-album artists into a single title feat group.
    if extra_artists:
        title = merge_feat_artists(title, extra_artists)

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
