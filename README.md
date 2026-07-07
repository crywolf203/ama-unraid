<p align="center">
<img src="ama-unraid-icon.png" alt="AMA-Unraid" width="150">
</p>

<h1 align="center">AMA-Unraid</h1>

<p align="center">
<strong>Unraid-friendly Automated Music Archiver</strong><br>
Deemix Direct · Synced Lyrics · ReplayGain · Plex/Roon Metadata Cleanup · High-Quality Album Art
</p>

<p align="center">
<a href="https://unraid.net/"><img alt="Unraid" src="https://img.shields.io/badge/Unraid-Community%20Applications-orange?style=for-the-badge&logo=unraid&logoColor=white"></a>
<a href="https://github.com/crywolf203/ama-unraid/pkgs/container/ama-unraid"><img alt="GHCR" src="https://img.shields.io/badge/GHCR-ama--unraid-blue?style=for-the-badge&logo=github&logoColor=white"></a>
<a href="https://github.com/crywolf203/ama-unraid/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-GPLv3-blue?style=for-the-badge"></a>
<a href="https://buymeacoffee.com/crywolf203"><img alt="Buy Me a Coffee" src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support-yellow?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
</p>

<p align="center">
<a href="https://github.com/crywolf203/unraid-templates"><img alt="Unraid Templates" src="https://img.shields.io/badge/Unraid-Templates-orange?style=flat-square&logo=unraid&logoColor=white"></a>
<a href="https://github.com/RandomNinjaAtk"><img alt="Original AMA" src="https://img.shields.io/badge/Original-AMA-lightgrey?style=flat-square&logo=github"></a>
<a href="https://github.com/bambanah/deemix"><img alt="Deemix" src="https://img.shields.io/badge/Deemix-Direct-purple?style=flat-square&logo=github"></a>
<img alt="Recommended Mode" src="https://img.shields.io/badge/Recommended-deemix__direct-success?style=flat-square">
</p>

---

## Table of Contents

- [What is AMA-Unraid?](#what-is-ama-unraid)
- [Main Features](#main-features)
- [Docker Image and Unraid Template Updates](#docker-image-and-unraid-template-updates)
- [Required and Optional Paths](#required-and-optional-paths)
  - [Recommended Direct-mode paths](#recommended-direct-mode-paths)
  - [Optional Deemix login path](#optional-deemix-login-path)
  - [Legacy API-only path](#legacy-api-only-path)
- [Deemix Login](#deemix-login)
- [Basic Usage](#basic-usage)
- [Artist List Files](#artist-list-files)
- [Artist Mode vs Discography Mode](#artist-mode-vs-discography-mode)
- [Variable Reference](#variable-reference)
  - [Core setup](#core-setup)
  - [Format, quality, and conversion](#format-quality-and-conversion)
  - [Artwork](#artwork)
  - [Library discovery and filtering](#library-discovery-and-filtering)
  - [Post-processing and permissions](#post-processing-and-permissions)
  - [Lidarr](#lidarr)
  - [Plex](#plex)
  - [Optional and legacy Deemix paths](#optional-and-legacy-deemix-paths)
- [Recommended Defaults](#recommended-defaults)
- [Deemix Direct Flow](#deemix-direct-flow)
- [Bitrate Fallback](#bitrate-fallback)
- [Conversion Notes](#conversion-notes)
- [Artist Tag Cleanup](#artist-tag-cleanup)
- [Timed LRC Lyric Fallback](#timed-lrc-lyric-fallback)
- [Plex Scan Path Override](#plex-scan-path-override)
- [Docker Compose Example](#docker-compose-example)
- [Docker CLI Example](#docker-cli-example)
- [Testing Deemix Direct](#testing-deemix-direct)
- [Legacy External Deemix API Mode](#legacy-external-deemix-api-mode)
- [Troubleshooting](#troubleshooting)
  - [Container starts but AMA does not run](#container-starts-but-ama-does-not-run)
  - [Deemix Direct cannot log in](#deemix-direct-cannot-log-in)
  - [FLAC was requested but MP3, M4A, or OPUS was downloaded](#flac-was-requested-but-mp3-m4a-or-opus-was-downloaded)
  - [Lyrics are missing](#lyrics-are-missing)
  - [Permission issues](#permission-issues)
- [Development Notes](#development-notes)
- [Related Projects](#related-projects)
- [Credits](#credits)
- [Funding](#funding)
- [Disclaimer](#disclaimer)

---


## What is AMA-Unraid?

AMA-Unraid is a community-maintained Unraid-focused fork of Automated Music Archiver, originally created by RandomNinjaAtk.

It is designed for Unraid users who want an automated music archiving workflow that can process artist lists, download albums, clean metadata, add lyrics, apply ReplayGain, and notify Plex after imports complete.

The recommended workflow is:

```bash
DOWNLOAD_CLIENT=deemix_direct
```

Deemix Direct runs Deemix inside the AMA-Unraid container. New installs should use Deemix Direct unless they specifically need the older external Deemix API/WebUI container workflow.

Use this container only with accounts, content, and services you are authorized to access.

---

## Main Features

- Internal Deemix Direct download flow.
- Safe per-album temp folder at `/downloads-ama/temp`.
- FLAC-first downloads with configurable fallback behavior.
- Optional conversion to ALAC, AAC, MP3, or OPUS.
- High-quality embedded and local album art.
- Native Deemix synced lyrics plus AMA/LRCLIB `.lrc` fallback.
- Artist tag cleanup for Plex and Roon-friendly libraries.
- ReplayGain tagging.
- Optional Plex library notification.
- Optional Lidarr artist list import.
- Legacy Deemix API mode remains available for advanced users.

---

## Docker Image and Unraid Template Updates

Latest image:

```bash
ghcr.io/crywolf203/ama-unraid:2.5.1latest
```

Versioned image example:

```bash
ghcr.io/crywolf203/ama-unraid:2.5.1
```

Unraid template repository:

```text
https://github.com/crywolf203/unraid-templates
```

The Unraid template keeps these update-tracking fields in place:

```xml
<Repository>ghcr.io/crywolf203/ama-unraid:2.5.1latest</Repository>
<Registry>https://github.com/crywolf203/ama-unraid/pkgs/container/ama-unraid</Registry>
<TemplateURL>https://raw.githubusercontent.com/crywolf203/unraid-templates/main/templates/ama-unraid.xml</TemplateURL>
<Project>https://github.com/crywolf203/ama-unraid</Project>
<Support>https://github.com/crywolf203/unraid-templates/issues</Support>
```

That lets Unraid continue tracking the container image and template metadata.

---

## Required and Optional Paths

### Recommended Direct-mode paths

| Container Path | Example Host Path | Required | Purpose |
|---|---:|:---:|---|
| `/config` | `/mnt/cache/appdata/ama-unraid` | Yes | AMA config, scripts, cache, logs, artist lists, and runtime Deemix Direct config |
| `/downloads-ama` | `/mnt/user/media/music` | Yes | Final processed music library and internal `/downloads-ama/temp` working folder |

Do not map `/downloads-ama/temp` separately. AMA creates, cleans, and manages that folder internally per album.

### Optional Deemix login path

| Container Path | Example Host Path | Required | Purpose |
|---|---:|:---:|---|
| `/deemix-config` | `/mnt/cache/appdata/Deemix-1` | No | Optional `login.json` location if you do not use `ARL_TOKEN` |

New Direct-mode installs can use `ARL_TOKEN` instead of mapping a separate Deemix config folder.

### Legacy API-only path

| Container Path | Example Host Path | Required | Purpose |
|---|---:|:---:|---|
| `/deemix-downloads` | `/mnt/user/media2/deemix-1` | No | Only used by legacy `DOWNLOAD_CLIENT=deemix_api` workflows |

---

## Deemix Login

Deemix Direct needs one of these:

```bash
ARL_TOKEN=your_arl_token_here
```

or:

```bash
/deemix-config/login.json
```

Recommended for new Unraid users:

```bash
ARL_TOKEN=your_arl_token_here
```

Do not publish your `ARL_TOKEN` or `login.json`.

---

## Basic Usage

1. Set `DOWNLOAD_CLIENT=deemix_direct`.
2. Map `/config` to your AMA appdata folder.
3. Map `/downloads-ama` to your final music library.
4. Set `ARL_TOKEN` or provide `/deemix-config/login.json`.
5. Add artist files to `/config/list`.
6. Start AMA manually or enable `AUTOSTART=true`.

Start manually:

```bash
docker exec -it AMA-Unraid bash -lc 'bash /config/scripts/start.bash'
```

Watch Docker logs:

```bash
docker logs -f --tail=300 AMA-Unraid
```

View saved run logs:

```bash
docker exec -it AMA-Unraid bash -lc 'ls -lah /config/logs && tail -f -n 300 "$(ls -t /config/logs/*.log | head -1)"'
```

---

## Artist List Files

AMA processes artists from:

```bash
/config/list
```

Artist files should use this format:

```text
DEEZER_ARTIST_ID-Artist Name.file
```

Examples:

```text
9262400-Jessie Reyez.file
85065212-Leon Thomas.file
5828-DJ Khaled.file
```

To process only one artist from the Unraid host:

```bash
mkdir -p /mnt/cache/appdata/ama-unraid/list
rm -f /mnt/cache/appdata/ama-unraid/list/*
touch "/mnt/cache/appdata/ama-unraid/list/5828-DJ Khaled.file"
```

---

## Artist Mode vs Discography Mode

The existing AMA variable is:

```bash
MODE=artist
```

Supported values:

```text
artist
discography
```

`artist` mode downloads albums listed directly under the selected artist.

`discography` mode downloads albums listed under the selected artist plus albums where that artist appears as a contributor or featured artist.

Recommended default:

```bash
MODE=artist
```

Use `artist` for tighter libraries. Use `discography` when you want the broadest possible collection and do not mind featured-artist or contributor albums being included.

---

## Variable Reference

The table below mirrors the Unraid template order and keeps the app repo and template descriptions in sync.

### Core setup

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `/config` path | `/mnt/cache/appdata/ama-unraid` | Yes | Persistent AMA-Unraid appdata, scripts, logs, cache, lists, and runtime config |
| `/downloads-ama` path | `/mnt/user/media/music` | Yes | Final processed music library and internal temp working folder |
| `DOWNLOAD_CLIENT` | `deemix_direct` | Yes | Recommended backend. Uses internal Deemix Direct. Legacy option: `deemix_api` |
| `MODE` | `artist` | Yes | `artist` or `discography` album discovery behavior |
| `ARL_TOKEN` | empty | No | Recommended Direct-mode login token. Required unless using `/deemix-config/login.json` |
| `AUTOSTART` | `false` | Yes | Run AMA automatically on container startup |
| `SCRIPTINTERVAL` | `7d` | No | Time between automatic runs when autostart is enabled |
| `PUID` | `99` | Yes | Unraid file owner user ID |
| `PGID` | `100` | Yes | Unraid file owner group ID |
| `TZ` | `America/New_York` | No | Container timezone for logs and schedules |

### Format, quality, and conversion

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `FORMAT` | `FLAC` | Yes | Preferred final format. Supported: `FLAC`, `ALAC`, `AAC`, `MP3`, `OPUS` |
| `BITRATE` | `320` | No | Lossy bitrate for MP3, AAC, or OPUS conversion paths |
| `FORCECONVERT` | `false` | No | Force conversion to requested format when supported |
| `POSTPROCESSTHREADS` | `8` | No | Threads used for conversion and post-processing |
| `REQUIRE_QUALITY` | `false` | No | Stricter quality check after download |
| `DEEMIX_FALLBACK_BITRATE` | `true` | No | Allow Deemix Direct to fall back when requested quality is unavailable |
| `DEEMIX_QUEUE_CONCURRENCY` | `1` | No | Internal Deemix Direct queue/download concurrency |

### Artwork

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `DEEMIX_EMBEDDED_ARTWORK_SIZE` | `1400` | No | Embedded artwork size |
| `DEEMIX_LOCAL_ARTWORK_SIZE` | `1400` | No | Local artwork size for files such as `cover.jpg` |
| `DEEMIX_JPEG_IMAGE_QUALITY` | `100` | No | JPEG quality for saved and embedded artwork |
| `EMBEDDED_COVER_QUALITY` | `100` | No | Legacy/fallback artwork quality variable |

### Library discovery and filtering

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `ALBUM_TYPE_FILTER` | `COMPILE` | No | Comma-separated Deezer record types to skip, such as `COMPILE`, `SINGLE`, `ALBUM`, `EP` |
| `IGNORE_ARTIST_WITHOUT_IMAGE` | `true` | No | Skip related/discovered artists with blank/default images |
| `COMPLETE_MY_ARTISTS` | `false` | No | Add artist IDs discovered from your library that are not already listed |
| `RELATED_ARTIST` | `false` | No | Enable related artist discovery |
| `RELATED_ARTIST_RELATED` | `false` | No | Enable recursive related artist discovery |
| `RELATED_COUNT` | `0` | No | Maximum related artists imported per artist |
| `FAN_COUNT` | `10` | No | Minimum Deezer fan count for related artist processing |
| `CONCURRENT_DOWNLOADS` | `1` | No | AMA album-processing concurrency. Recommended `1` for Deemix Direct |

### Post-processing and permissions

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `REPLAYGAIN` | `true` | No | Apply ReplayGain tags after download |
| `ENABLE_ARTIST_TAG_CLEANUP` | `true` | No | Clean artist metadata for FLAC, MP3, M4A, and OPUS files |
| `ENABLE_TAG_NORMALIZER` | `false` | No | Legacy broader tag normalizer. Disabled by default |
| `FILE_PERMISSIONS` | `777` | No | File permissions applied to completed files |
| `FOLDER_PERMISSIONS` | `777` | No | Folder permissions applied to completed folders |

### Lidarr

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `LIDARR_LIST_IMPORT` | `false` | No | Import artist IDs from Lidarr |
| `LIDARR_URL` | empty | No | Lidarr server URL, used only when Lidarr import is enabled |
| `LIDARR_API_KEY` | empty | No | Lidarr API key, used only when Lidarr import is enabled |

### Plex

| Variable | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `NOTIFYPLEX` | `false` | No | Notify Plex after imports complete |
| `PLEXSCANPATH` | empty | No | Optional Plex path override if Plex sees the music path differently than AMA |
| `PLEXLIBRARYNAME` | `Music` | No | Exact Plex music library name |
| `PLEXURL` | empty | No | Plex server URL |
| `PLEXTOKEN` | empty | No | Plex token |

### Optional and legacy Deemix paths

| Variable or path | Default | Required in Unraid template | Description |
|---|---:|:---:|---|
| `DEEMIX_CONFIG_PATH` | `/deemix-config` | No | Optional container path for `login.json` if `ARL_TOKEN` is blank |
| `/deemix-config` path | empty | No | Optional host path containing `login.json` |
| `DEEMIX_API_URL` | empty | No | Legacy/API-only Deemix API URL |
| `DEEMIX_DOWNLOAD_PATH` | `/deemix-downloads` | No | Legacy/API-only container path for external Deemix downloads |
| `/deemix-downloads` path | empty | No | Legacy/API-only host path for external Deemix downloads |

---

## Recommended Defaults

```bash
DOWNLOAD_CLIENT=deemix_direct
MODE=artist
AUTOSTART=false
SCRIPTINTERVAL=7d
FORMAT=FLAC
BITRATE=320
FORCECONVERT=false
REQUIRE_QUALITY=false
DEEMIX_FALLBACK_BITRATE=true
DEEMIX_QUEUE_CONCURRENCY=1
DEEMIX_EMBEDDED_ARTWORK_SIZE=1400
DEEMIX_LOCAL_ARTWORK_SIZE=1400
DEEMIX_JPEG_IMAGE_QUALITY=100
REPLAYGAIN=true
ENABLE_ARTIST_TAG_CLEANUP=true
ENABLE_TAG_NORMALIZER=false
NOTIFYPLEX=false
LIDARR_LIST_IMPORT=false
FILE_PERMISSIONS=777
FOLDER_PERMISSIONS=777
```

---

## Deemix Direct Flow

The safe direct-temp flow works like this:

1. AMA cleans `/downloads-ama/temp` before each album.
2. Deemix downloads the album directly into `/downloads-ama/temp`.
3. AMA finds the downloaded album folder.
4. AMA adds the album ID to the temporary album folder when needed.
5. AMA runs `lrc_fallback.py` with `/downloads-ama/temp` and the album ID.
6. AMA flattens audio files, `.lrc` files, and `cover.jpg` into `/downloads-ama/temp`.
7. AMA continues import, tag cleanup, ReplayGain, permissions, and Plex notification.

Deemix Direct writes its runtime config under:

```bash
/config/deemix/xdg/deemix/config.json
```

It does not need a separate Deemix Downloads folder.

---

## Bitrate Fallback

Deemix Direct supports:

```bash
DEEMIX_FALLBACK_BITRATE=true
```

When enabled, Deemix can fall back to another available quality if the requested quality is unavailable.

Example: if `FORMAT=FLAC` is requested but FLAC is unavailable, Deemix may download MP3, M4A, or OPUS instead of failing the album.

The direct script logs the setting and final file summary:

```text
DEEMIX_DIRECT :: fallbackBitrate=True
DEEMIX_DIRECT :: requested=FLAC actual_summary flac=0 mp3=1 m4a=0 opus=0
DEEMIX_DIRECT :: WARNING fallback format used because requested FLAC was unavailable
```

Use stricter settings if you do not want fallback behavior:

```bash
DEEMIX_FALLBACK_BITRATE=false
REQUIRE_QUALITY=true
```

---

## Conversion Notes

`FORMAT` controls the desired final format.

- `FLAC` keeps lossless files when available.
- `ALAC` converts lossless FLAC to Apple-friendly ALAC/M4A.
- `AAC` converts lossless FLAC to AAC/M4A using `BITRATE`.
- `MP3` downloads or converts to MP3 depending on bitrate and source availability.
- `OPUS` converts lossless FLAC to OPUS using `BITRATE`.

Recommended default:

```bash
FORMAT=FLAC
FORCECONVERT=false
```

Set `FORCECONVERT=true` only when you intentionally want AMA to force the library into the requested output format.

---

## Artist Tag Cleanup

Artist cleanup is enabled by default:

```bash
ENABLE_ARTIST_TAG_CLEANUP=true
```

It keeps featured artists in the track title while keeping `ARTIST` and `ALBUMARTIST` clean.

Supported cleanup formats:

```text
.flac
.mp3
.m4a
.opus
```

Example before cleanup:

```text
TITLE=Crash & Burn (Remix)
ARTIST=Leon Thomas;Blxst
album_artist=Leon Thomas
```

Example after cleanup:

```text
TITLE=Crash & Burn (Remix) (feat. Blxst)
ARTIST=Leon Thomas
ALBUMARTIST=Leon Thomas
```

---

## Timed LRC Lyric Fallback

After Deemix finishes downloading an album, AMA checks for `.lrc` files.

If Deemix does not provide timed lyrics, AMA attempts to find synced lyrics from LRCLIB.

Possible outcomes:

```text
Created timed .lrc from LRCLIB synced
Created plain .lrc from LRCLIB plain
Created plain .lrc from embedded plain lyrics
No lyrics found
```

For Deemix Direct, fallback runs with:

```bash
lrc_fallback.py /downloads-ama/temp ALBUM_ID
```

---

## Plex Scan Path Override

If Plex sees the music path differently than AMA, set:

```bash
PLEXSCANPATH=/media/music
```

Example:

- AMA writes to `/downloads-ama/Artist/Album`.
- Plex sees the same files as `/media/music/Artist/Album`.
- `PLEXSCANPATH=/media/music` tells AMA to notify Plex using the Plex-visible path.

---

## Docker Compose Example

```yaml
services:
  ama-unraid:2.5.1
    image: ghcr.io/crywolf203/ama-unraid:2.5.1latest
    container_name: AMA-Unraid
    restart: unless-stopped
    network_mode: bridge
    environment:
      TZ: "America/New_York"
      PUID: "99"
      PGID: "100"
      AUTOSTART: "false"
      SCRIPTINTERVAL: "7d"
      DOWNLOAD_CLIENT: "deemix_direct"
      MODE: "artist"
      ARL_TOKEN: "YOUR-ARL-TOKEN"
      FORMAT: "FLAC"
      BITRATE: "320"
      FORCECONVERT: "false"
      REQUIRE_QUALITY: "false"
      DEEMIX_FALLBACK_BITRATE: "true"
      DEEMIX_QUEUE_CONCURRENCY: "1"
      DEEMIX_EMBEDDED_ARTWORK_SIZE: "1400"
      DEEMIX_LOCAL_ARTWORK_SIZE: "1400"
      DEEMIX_JPEG_IMAGE_QUALITY: "100"
      REPLAYGAIN: "true"
      ENABLE_ARTIST_TAG_CLEANUP: "true"
      ENABLE_TAG_NORMALIZER: "false"
      NOTIFYPLEX: "false"
      LIDARR_LIST_IMPORT: "false"
      FILE_PERMISSIONS: "777"
      FOLDER_PERMISSIONS: "777"
    volumes:
      - /mnt/cache/appdata/ama-unraid:2.5.1/config:rw
      - /mnt/user/media/music:/downloads-ama:rw
```

Optional `login.json` volume if you do not use `ARL_TOKEN`:

```yaml
      - /mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

---

## Docker CLI Example

```bash
docker run -d \
  --name AMA-Unraid \
  --restart unless-stopped \
  --net bridge \
  -e TZ="America/New_York" \
  -e PUID="99" \
  -e PGID="100" \
  -e AUTOSTART="false" \
  -e SCRIPTINTERVAL="7d" \
  -e DOWNLOAD_CLIENT="deemix_direct" \
  -e MODE="artist" \
  -e ARL_TOKEN="YOUR-ARL-TOKEN" \
  -e FORMAT="FLAC" \
  -e BITRATE="320" \
  -e FORCECONVERT="false" \
  -e REQUIRE_QUALITY="false" \
  -e DEEMIX_FALLBACK_BITRATE="true" \
  -e DEEMIX_QUEUE_CONCURRENCY="1" \
  -e DEEMIX_EMBEDDED_ARTWORK_SIZE="1400" \
  -e DEEMIX_LOCAL_ARTWORK_SIZE="1400" \
  -e DEEMIX_JPEG_IMAGE_QUALITY="100" \
  -e REPLAYGAIN="true" \
  -e ENABLE_ARTIST_TAG_CLEANUP="true" \
  -e ENABLE_TAG_NORMALIZER="false" \
  -e NOTIFYPLEX="false" \
  -e LIDARR_LIST_IMPORT="false" \
  -e FILE_PERMISSIONS="777" \
  -e FOLDER_PERMISSIONS="777" \
  -v /mnt/cache/appdata/ama-unraid:2.5.1/config:rw \
  -v /mnt/user/media/music:/downloads-ama:rw \
  ghcr.io/crywolf203/ama-unraid:2.5.1latest
```

---

## Testing Deemix Direct

Test one album URL:

```bash
docker exec -it AMA-Unraid bash -lc '
DOWNLOAD_CLIENT=deemix_direct \
FORMAT=FLAC \
DEEMIX_FALLBACK_BITRATE=true \
bash /config/scripts/deemix_direct_download.bash "https://www.deezer.com/album/ALBUM_ID"
'
```

Check temp-root output:

```bash
docker exec -it AMA-Unraid bash -lc 'find /downloads-ama/temp -maxdepth 1 -type f | sort'
```

Expected examples:

```text
/downloads-ama/temp/01 - Track.flac
/downloads-ama/temp/01 - Track.lrc
/downloads-ama/temp/cover.jpg
```

If FLAC is unavailable and fallback is enabled, the audio file may be a fallback format:

```text
/downloads-ama/temp/01 - Track.mp3
/downloads-ama/temp/01 - Track.lrc
/downloads-ama/temp/cover.jpg
```

---

## Legacy External Deemix API Mode

The older external Deemix API workflow remains available:

```bash
DOWNLOAD_CLIENT=deemix_api
```

This mode requires a separate running Deemix WebUI/API container.

Legacy variables:

```bash
DEEMIX_API_URL=http://SERVER-IP:6595
DEEMIX_CONFIG_PATH=/deemix-config
DEEMIX_DOWNLOAD_PATH=/deemix-downloads
```

Legacy extra path:

```bash
/mnt/user/media2/deemix-1:/deemix-downloads:rw
```

New installs should prefer Deemix Direct.

---

## Troubleshooting

### Container starts but AMA does not run

If the log shows:

```text
Automatic Start Disabled, manually run using this command:
bash /config/scripts/start.bash
```

Either start manually:

```bash
docker exec -it AMA-Unraid bash -lc 'bash /config/scripts/start.bash'
```

or set:

```bash
AUTOSTART=true
```

### Deemix Direct cannot log in

Confirm one of these is configured:

```bash
ARL_TOKEN=your_arl_token_here
```

or:

```bash
/deemix-config/login.json
```

### FLAC was requested but MP3, M4A, or OPUS was downloaded

This can happen when fallback is enabled and FLAC is unavailable.

Check the Deemix Direct log for:

```text
DEEMIX_DIRECT :: fallbackBitrate=True
DEEMIX_DIRECT :: requested=FLAC actual_summary flac=0 mp3=1 m4a=0 opus=0
```

### Lyrics are missing

Check the direct log:

```bash
docker exec -it AMA-Unraid bash -lc '
grep -nE "Running LRC fallback|LRC summary|Missing LRC|Created timed|Created plain|No lyrics" /config/logs/*.log | tail -n 200
'
```

### Permission issues

Check:

```bash
PUID=99
PGID=100
FILE_PERMISSIONS=777
FOLDER_PERMISSIONS=777
```

Also confirm `/downloads-ama` is mapped read/write.

---

## Development Notes

Useful repo path on Unraid:

```bash
cd /mnt/cache/appdata/ama-unraid
```

Validate the Deemix Direct Bash script:

```bash
bash -n root/scripts/deemix_direct_download.bash
```

Validate the artist cleanup Python script:

```bash
python3 -m py_compile root/scripts/artist_tag_cleanup.py
```

---

## Related Projects

| Project | Link |
|---|---|
| AMA-Unraid maintained fork | `https://github.com/crywolf203/ama-unraid` |
| Unraid template repo | `https://github.com/crywolf203/unraid-templates` |
| Revived Deemix project | `https://github.com/bambanah/deemix` |
| Original AMA creator | `https://github.com/RandomNinjaAtk` |
| LRCLIB | `https://lrclib.net` |
| Plex | `https://www.plex.tv` |
| Roon | `https://roon.app` |

---

## Credits

AMA-Unraid builds on the work of several open-source projects and maintainers.

- RandomNinjaAtk for the original AMA project.
- crywolf203 for maintaining and extending AMA-Unraid.
- bambanah for the revived Deemix project.
- RemixDev for the original Deemix project.
- Bockiii for Deemix Docker inspiration.

---

## Funding

If this Unraid-focused fork, template work, documentation, or troubleshooting saves you time, you can support this maintenance work here:

```text
https://buymeacoffee.com/crywolf203
```

---

## Disclaimer

Use this container only with accounts, content, and services you are authorized to access.

This repository does not claim ownership of upstream projects. It packages, documents, and extends the workflow for Unraid users.
