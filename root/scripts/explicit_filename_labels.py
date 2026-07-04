#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
from pathlib import Path

AUDIO_EXTS = {".flac", ".mp3", ".m4a", ".opus"}


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


def already_labeled(stem):
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


def rename_audio_and_lrc(path, label):
    stem = path.stem

    if already_labeled(stem):
        return False

    new_path = path.with_name(f"{stem} ({label}){path.suffix}")

    if new_path.exists():
        return False

    old_lrc = path.with_suffix(".lrc")
    new_lrc = new_path.with_suffix(".lrc")

    path.rename(new_path)

    if old_lrc.exists() and not new_lrc.exists():
        old_lrc.rename(new_lrc)

    print(f"EXPLICIT_FILENAME :: renamed :: {path.name} -> {new_path.name}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: explicit_filename_labels.py <album_folder> <album_id>")
        return 1

    root = Path(sys.argv[1])
    album_id = str(sys.argv[2]).strip()

    if not root.exists():
        print(f"EXPLICIT_FILENAME :: album folder missing: {root}")
        return 0

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
        return 0

    checked = 0
    renamed = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
            continue

        checked += 1

        match = re.match(r"^(\d{3})\s+-\s+", path.name)
        if not match:
            continue

        key = match.group(1)

        if explicit_by_position.get(key, False):
            if rename_audio_and_lrc(path, "Explicit"):
                renamed += 1

    print(f"EXPLICIT_FILENAME :: checked={checked} renamed={renamed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
