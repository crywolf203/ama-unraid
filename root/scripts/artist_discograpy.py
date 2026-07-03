#!/usr/bin/env python3
from deezer import Deezer
import os
import sys


def get_limit():
    value = os.environ.get("MAX_ALBUMS_PER_ARTIST", "").strip()
    if not value:
        return 0

    try:
        parsed = int(value)
    except ValueError:
        return 0

    return max(parsed, 0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dz = Deezer()
        limit = get_limit()

        releases = dz.gw.get_artist_discography_tabs(sys.argv[1], 100)

        seen = set()
        album_ids = []

        for release_type in releases:
            for release in releases[release_type]:
                album_id = str(release.get("id", "")).strip()

                if not album_id or album_id in seen:
                    continue

                seen.add(album_id)
                album_ids.append(album_id)

                if limit and len(album_ids) >= limit:
                    break

            if limit and len(album_ids) >= limit:
                break

        for album_id in album_ids:
            print(album_id)
