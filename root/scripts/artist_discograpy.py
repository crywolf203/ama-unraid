#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
import urllib.request

from deezer import Deezer


def get_limit():
    value = os.environ.get("MAX_ALBUMS_PER_ARTIST", "").strip()

    # Historical AMA behavior is unlimited. Some older/test images carried
    # MAX_ALBUMS_PER_ARTIST=25 internally even though the Unraid template did
    # not expose it. Treat 25 as legacy/unset unless explicitly changed later.
    if not value or value == "25":
        return 0

    try:
        parsed = int(value)
    except ValueError:
        return 0

    return max(parsed, 0)


def add_album_id(album_ids, seen, album_id, limit=0):
    album_id = str(album_id or "").strip()

    if not album_id or album_id in seen:
        return False

    seen.add(album_id)
    album_ids.append(album_id)

    if limit and len(album_ids) >= limit:
        return True

    return False


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AMA-Unraid/2.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def get_api_artist_albums(artist_id):
    album_ids = []
    seen = set()

    url = f"https://api.deezer.com/artist/{urllib.parse.quote(str(artist_id))}/albums?limit=100"

    while url:
        data = fetch_json(url)

        for album in data.get("data", []):
            add_album_id(album_ids, seen, album.get("id"), 0)

        url = data.get("next") or ""

    return album_ids


def get_gw_artist_albums(artist_id):
    album_ids = []
    seen = set()

    dz = Deezer()
    releases = dz.gw.get_artist_discography_tabs(artist_id, 1000)

    if isinstance(releases, dict):
        for release_type in releases:
            for release in releases.get(release_type, []):
                add_album_id(album_ids, seen, release.get("id"), 0)

    return album_ids


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        raise SystemExit(0)

    artist_id = sys.argv[1]
    limit = get_limit()

    seen = set()
    album_ids = []

    for getter in (get_api_artist_albums, get_gw_artist_albums):
        try:
            for album_id in getter(artist_id):
                if add_album_id(album_ids, seen, album_id, limit):
                    break
        except Exception as exc:
            print(f"artist_discograpy.py warning: {getter.__name__} failed: {exc}", file=sys.stderr)

        if limit and len(album_ids) >= limit:
            break

    for album_id in album_ids:
        print(album_id)
