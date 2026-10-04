#!/usr/bin/env python3

import mimetypes
import sys
from pathlib import Path

from mutagen.id3 import APIC, ID3, ID3NoHeaderError


def main():
    if len(sys.argv) != 3:
        print("Usage: embed_mp3_cover.py <mp3> <cover>")
        return 2

    mp3 = Path(sys.argv[1])
    cover = Path(sys.argv[2])

    if not mp3.is_file():
        print(f"MP3_ARTWORK :: ERROR :: MP3 not found: {mp3}")
        return 1

    if not cover.is_file():
        print(f"MP3_ARTWORK :: ERROR :: Cover not found: {cover}")
        return 1

    try:
        tags = ID3(mp3)
    except ID3NoHeaderError:
        tags = ID3()

    mime = mimetypes.guess_type(cover.name)[0] or "image/jpeg"

    tags.delall("APIC")

    tags.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,
            desc="Cover",
            data=cover.read_bytes(),
        )
    )

    tags.save(mp3, v2_version=3)

    print(f"MP3_ARTWORK :: embedded {cover.name} into {mp3.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
