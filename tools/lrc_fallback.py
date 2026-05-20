#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: lrc_fallback.py <downloads_root> <album_id>")
    raise SystemExit(1)

root = Path(sys.argv[1])
album_id = sys.argv[2]

file_uid = int(os.environ.get("FILE_UID", "99"))
file_gid = int(os.environ.get("FILE_GID", "100"))

audio_exts = {".flac", ".mp3", ".m4a", ".opus"}
user_agent = "AMA-Unraid-LRC-Fallback/1.0"

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def ffprobe(path: Path):
    result = run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration:format_tags",
        "-of", "json",
        str(path)
    ])
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout or "{}")
    except Exception:
        return {}

def tag(tags, *names):
    lowered = {str(k).lower(): v for k, v in (tags or {}).items()}
    for name in names:
        value = lowered.get(name.lower())
        if value:
            return str(value).strip()
    return ""

def normalize(value):
    value = value or ""
    value = value.replace("_", "?")
    value = value.replace("’", "'")
    value = re.sub(r"\s+\((explicit|clean)\)$", "", value, flags=re.I)
    value = re.sub(r"\s+\[(explicit|clean)\]$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip()
    return value

def simple_key(value):
    value = normalize(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value

def title_variants(title):
    base = normalize(title)
    variants = [
        base,
        base.replace("?", ""),
        base.replace("'", ""),
        base.replace("’", ""),
        re.sub(r"\s+\(.*?\)$", "", base).strip(),
        re.sub(r"\s+(feat\.|ft\.|with).*$", "", base, flags=re.I).strip(),
    ]
    clean = []
    for item in variants:
        if item and item not in clean:
            clean.append(item)
    return clean

def artist_variants(artist):
    base = normalize(artist)
    parts = re.split(r"\s*(?:,|;|&|feat\.|ft\.|with)\s*", base, flags=re.I)
    variants = [base]
    if parts and parts[0] and parts[0] != base:
        variants.append(parts[0])
    clean = []
    for item in variants:
        if item and item not in clean:
            clean.append(item)
    return clean

def is_timed(text):
    return bool(re.search(r"(?m)^\[[0-9]{1,2}:[0-9]{2}(?:\.[0-9]{1,3})?\]", text or ""))

def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def chmod_chown(path: Path):
    try:
        os.chmod(path, 0o777)
    except Exception:
        pass
    try:
        os.chown(path, file_uid, file_gid)
    except Exception:
        pass

def write_lrc(lrc_path: Path, text: str, source: str):
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return False
    lrc_path.write_text(text + "\n", encoding="utf-8")
    chmod_chown(lrc_path)
    kind = "timed" if is_timed(text) else "plain"
    print(f"Created {kind} .lrc from {source}: {lrc_path.name}")
    return True

def lrclib_search(artist, title, album, duration):
    best_synced = None
    best_plain = None

    for artist_query in artist_variants(artist):
        for title_query in title_variants(title):
            params = {
                "artist_name": artist_query,
                "track_name": title_query,
            }
            url = "https://lrclib.net/api/search?" + urllib.parse.urlencode(params)
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})

            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
            except Exception:
                continue

            if not isinstance(data, list):
                continue

            def score(item):
                score_value = 0
                item_title = item.get("trackName") or ""
                item_artist = item.get("artistName") or ""
                item_album = item.get("albumName") or ""

                if simple_key(item_title) == simple_key(title):
                    score_value += 100
                elif simple_key(title) in simple_key(item_title) or simple_key(item_title) in simple_key(title):
                    score_value += 40

                if simple_key(artist_query) and simple_key(artist_query) in simple_key(item_artist):
                    score_value += 30

                if album and simple_key(album) and simple_key(album) in simple_key(item_album):
                    score_value += 15

                try:
                    item_duration = int(item.get("duration") or 0)
                    if duration and abs(item_duration - duration) <= 3:
                        score_value += 20
                except Exception:
                    pass

                return score_value

            for item in sorted(data, key=score, reverse=True):
                synced = (item.get("syncedLyrics") or "").strip()
                plain = (item.get("plainLyrics") or "").strip()

                if synced and not best_synced:
                    best_synced = synced
                if plain and not best_plain:
                    best_plain = plain

            if best_synced:
                return best_synced, "LRCLIB synced"

    if best_plain:
        return best_plain, "LRCLIB plain"

    return "", ""

album_dirs = [p for p in root.rglob(f"*({album_id})") if p.is_dir()]
if not album_dirs:
    raise SystemExit(f"No album directory found for album ID {album_id}")

album_dir = album_dirs[0]
print(f"Processing album folder: {album_dir}")

audio_files = sorted(p for p in album_dir.rglob("*") if p.is_file() and p.suffix.lower() in audio_exts)

if not audio_files:
    raise SystemExit("No audio files found.")

created = 0
kept = 0
missing = 0

for audio in audio_files:
    lrc = audio.with_suffix(".lrc")

    if lrc.exists() and is_timed(read_text(lrc)):
        print(f"Kept existing timed .lrc: {lrc.name}")
        chmod_chown(lrc)
        kept += 1
        continue

    data = ffprobe(audio)
    fmt = data.get("format", {}) if isinstance(data, dict) else {}
    tags = fmt.get("tags", {}) or {}

    title = normalize(tag(tags, "TITLE", "title"))
    artist = normalize(tag(tags, "ARTIST", "artist", "ALBUMARTIST", "albumartist", "album_artist"))
    album = normalize(tag(tags, "ALBUM", "album"))

    if not title:
        title = normalize(re.sub(r"^[0-9]+[\s.-]+", "", audio.stem))

    duration = None
    try:
        duration = int(round(float(fmt.get("duration", "0"))))
    except Exception:
        pass

    text, source = lrclib_search(artist, title, album, duration)

    if text and write_lrc(lrc, text, source):
        created += 1
        continue

    embedded_synced = tag(tags, "SYNCEDLYRICS", "SyncedLyrics", "syncedlyrics", "SYNCED LYRICS")
    if embedded_synced and write_lrc(lrc, embedded_synced, "embedded synced lyrics"):
        created += 1
        continue

    embedded_plain = tag(tags, "LYRICS", "Lyrics", "lyrics", "UNSYNCEDLYRICS", "UnsyncedLyrics")
    if embedded_plain and write_lrc(lrc, embedded_plain, "embedded plain lyrics"):
        created += 1
        continue

    if lrc.exists():
        print(f"Kept existing non-timed .lrc: {lrc.name}")
        chmod_chown(lrc)
        kept += 1
    else:
        print(f"No lyrics found for: {audio.name}")
        missing += 1

for path in album_dir.rglob("*"):
    chmod_chown(path)

chmod_chown(album_dir)

print()
print(f"Summary: created={created} kept={kept} missing={missing}")
