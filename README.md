<p align="center">
  <img src="https://raw.githubusercontent.com/crywolf203/unraid-templates/main/ama-unraid-icon.png?v=2026-05-26" alt="AMA-Unraid icon" width="160">
</p>

<h1 align="center">AMA-Unraid</h1>

<p align="center">
  <strong>Unraid-friendly Automated Music Archiver with Deemix API support, Plex/Roon-focused metadata cleanup, synced lyrics, ReplayGain, and clean post-processing.</strong>
</p>

<p align="center">
  <a href="https://unraid.net">
    <img alt="Unraid" src="https://img.shields.io/badge/Unraid-Community%20Template-f15a24?style=for-the-badge">
  </a>
  <a href="https://github.com/crywolf203/ama-unraid/pkgs/container/ama-unraid">
    <img alt="GHCR Image" src="https://img.shields.io/badge/GHCR-ama--unraid-blue?style=for-the-badge&logo=github">
  </a>
  <a href="https://github.com/crywolf203/ama-unraid/blob/master/LICENSE">
    <img alt="License" src="https://img.shields.io/badge/License-GPLv3-green?style=for-the-badge">
  </a>
  <a href="https://buymeacoffee.com/crywolf203">
    <img alt="Buy Me a Coffee" src="https://img.shields.io/badge/Support-Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge">
  </a>
</p>

<p align="center">
  <a href="https://github.com/crywolf203/unraid-templates">
    <img alt="Unraid Template Repo" src="https://img.shields.io/badge/Template%20Repo-crywolf203%2Funraid--templates-orange?style=flat-square">
  </a>
  <a href="https://github.com/RandomNinjaAtk">
    <img alt="Original AMA Creator" src="https://img.shields.io/badge/Original%20AMA-RandomNinjaAtk-lightgrey?style=flat-square">
  </a>
  <a href="https://github.com/bambanah/deemix">
    <img alt="Deemix" src="https://img.shields.io/badge/Deemix-API%20Mode-purple?style=flat-square">
  </a>
</p>

---

## What is AMA-Unraid?

**AMA-Unraid** is a community-maintained Unraid-focused fork of **Automated Music Archiver**, originally created by **RandomNinjaAtk**.

This fork is designed for Unraid users who want an automated music archiving workflow that can:

- Monitor artist list files
- Find artist albums
- Send albums to a Deemix WebUI/API container
- Wait for downloads to finish
- Copy completed albums into AMA processing
- Add or fetch `.lrc` lyrics
- Clean metadata for Plex and Roon
- Apply ReplayGain
- Notify Plex to scan the finished album folder

The current 2.0.0 workflow focuses on **Deemix API Mode**, where AMA-Unraid works alongside a separate Deemix WebUI/API container.

---

## Docker Image

```text
ghcr.io/crywolf203/ama-unraid:latest
```

Versioned tags may also be available:

```text
ghcr.io/crywolf203/ama-unraid:2.0.0
```

---

## Important Note

Deemix API Mode currently requires a separate running Deemix WebUI/API container.

The next development phase is planned to test folding the Deemix API directly into AMA-Unraid as an internal service. Until that work is complete, use the external Deemix API container method described below.

---

## Major Features

- Deemix API download client support
- Timed `.lrc` lyric fallback using LRCLIB
- Safe artist tag cleanup for Plex/Roon-friendly metadata
- ReplayGain support after Deemix API downloads
- Plex scan path override support
- Improved Deemix API queue wait handling
- Full AMA run log output on script exit
- Optional legacy tag normalizer, disabled by default
- Updated Unraid template variables for Deemix API mode

---

## Recommended Unraid Install

Install from **Unraid Community Applications** when available.

Search for:

```text
AMA-Unraid
```

Manual Docker image value:

```text
ghcr.io/crywolf203/ama-unraid:latest
```

Recommended mode for 2.0.0:

```text
DOWNLOAD_CLIENT=deemix_api
```

Unraid template repository:

```text
https://github.com/crywolf203/unraid-templates
```

---

## Deemix API Mode

Set:

```text
DOWNLOAD_CLIENT=deemix_api
```

AMA will send album URLs to the configured Deemix API, wait for Deemix to finish downloading, copy the completed files into AMA's temporary processing folder, then continue normal AMA post-processing.

### Required Deemix API Variables

```text
DOWNLOAD_CLIENT=deemix_api
DEEMIX_API_URL=http://SERVER-IP:6595
DEEMIX_CONFIG_PATH=/deemix-config
DEEMIX_DOWNLOAD_PATH=/deemix-downloads
```

Example:

```text
DOWNLOAD_CLIENT=deemix_api
DEEMIX_API_URL=http://10.13.1.138:6595
DEEMIX_CONFIG_PATH=/deemix-config
DEEMIX_DOWNLOAD_PATH=/deemix-downloads
```

### Required Deemix API Paths

The AMA container needs access to the same Deemix config and download folders used by the Deemix WebUI/API container.

| Container Path | Example Host Path | Access | Purpose |
|---|---|---:|---|
| `/deemix-config` | `/mnt/cache/appdata/Deemix-1` | Read/Write | Deemix config folder containing `login.json` |
| `/deemix-downloads` | `/mnt/user/media2/deemix-1` | Read/Write | Deemix completed download folder |

Example mappings:

```text
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
/mnt/user/media2/deemix-1:/deemix-downloads:rw
```

The Deemix config folder must contain a valid login session, usually:

```text
/deemix-config/login.json
```

If Deemix is not logged in, log into the Deemix WebUI first, force update the ARL if needed, then restart Deemix.

---

## Required AMA Paths

| Container Path | Example Host Path | Access | Purpose |
|---|---|---:|---|
| `/config` | `/mnt/cache/appdata/ama-unraid` | Read/Write | AMA config, scripts, cache, logs, and list files |
| `/downloads-ama` | `/mnt/user/media/music` | Read/Write | Final processed music library |

### `/config`

This should point to persistent appdata.

Recommended:

```text
/mnt/cache/appdata/ama-unraid
```

### `/downloads-ama`

This should point to your final music library.

Example:

```text
/mnt/user/media/music
```

AMA writes completed artist and album folders here.

---

## Artist List Files

AMA processes artists from the `/config/list` folder.

Artist files should use this format:

```text
DEEZE_ARTIST_ID-Artist Name.file
```

Examples:

```text
9262400-Jessie Reyez.file
85065212-Leon Thomas.file
5828-DJ Khaled.file
```

To process only one artist, clear the list folder and add one `.file` entry.

Example:

```bash
mkdir -p /mnt/cache/appdata/ama-unraid/list
rm -f /mnt/cache/appdata/ama-unraid/list/*
touch "/mnt/cache/appdata/ama-unraid/list/5828-DJ Khaled.file"
```

---

## Recommended Deemix Settings

For clean Plex/Roon-friendly tags, configure Deemix so featured artists are handled consistently.

Recommended settings:

```text
Tags:
- Keep normal music tags enabled
- Disable copyright
- Disable source
- Disable song ID / Deezer ID style tags
- Enable remove duplicate artists
- Enable single album artist

Other:
- Illegal Character Replacer: single space
- Artist separator: Standard Specification
```

AMA's artist tag cleanup can then safely move featured artists into the title and keep the primary artist tag clean.

---

## Environment Variables

### Core Variables

| Variable | Recommended | Description |
|---|---:|---|
| `PUID` | `99` | Runs files as the Unraid `nobody` user |
| `PGID` | `100` | Runs files as the Unraid `users` group |
| `TZ` | `America/New_York` | Container timezone |
| `AUTOSTART` | `false` or `true` | Automatically run AMA when the container starts |
| `SCRIPTINTERVAL` | `7d` | Interval between runs when autostart looping is enabled |
| `MODE` | `artist` | Artist-list processing mode |
| `DOWNLOAD_CLIENT` | `deemix_api` | Download backend |

### Deemix API Variables

| Variable | Recommended | Description |
|---|---:|---|
| `DEEMIX_API_URL` | `http://SERVER-IP:6595` | URL for the running Deemix WebUI/API container |
| `DEEMIX_CONFIG_PATH` | `/deemix-config` | Container path to Deemix config/login folder |
| `DEEMIX_DOWNLOAD_PATH` | `/deemix-downloads` | Container path to Deemix download folder |
| `DEEMIX_API_MAX_POLLS` | `8` | Short polling/stability window after files begin appearing |
| `DEEMIX_API_QUEUE_MAX_POLLS` | `120` | Longer wait while Deemix still reports the album as queued |

### Download and Post-Processing Variables

| Variable | Recommended | Description |
|---|---:|---|
| `FORMAT` | `FLAC` | Desired output format |
| `BITRATE` | `320` | Bitrate setting used by legacy paths; FLAC mode uses lossless |
| `FORCECONVERT` | `false` | Recommended false for Deemix API mode |
| `REPLAYGAIN` | `true` | Adds ReplayGain tags after download |
| `POSTPROCESSTHREADS` | `8` | Number of post-processing threads |
| `EMBEDDED_COVER_QUALITY` | `100` | Embedded cover quality percentage |
| `REQUIRE_QUALITY` | `false` | Require requested quality before processing |

### Tag and Metadata Variables

| Variable | Recommended | Description |
|---|---:|---|
| `ENABLE_ARTIST_TAG_CLEANUP` | `true` | Keeps featured artists in title and primary artist clean |
| `ENABLE_TAG_NORMALIZER` | `false` | Legacy broader tag normalizer. Disabled by default |

### Album Filtering Variables

| Variable | Recommended | Description |
|---|---:|---|
| `ALBUM_TYPE_FILTER` | `COMPILE` | Album filtering mode |
| `IGNORE_ARTIST_WITHOUT_IMAGE` | `true` | Ignore artists without images |
| `RELATED_ARTIST` | `false` | Import related artists |
| `RELATED_ARTIST_RELATED` | `false` | Related artist loop mode |
| `RELATED_COUNT` | `0` | Maximum related artists to import |
| `FAN_COUNT` | `10` | Minimum fan count threshold |
| `COMPLETE_MY_ARTISTS` | `false` | Complete known artists |

### Plex Variables

| Variable | Recommended | Description |
|---|---:|---|
| `NOTIFYPLEX` | `true` | Notify Plex after each album |
| `PLEXLIBRARYNAME` | `Music` | Plex music library name |
| `PLEXURL` | `http://SERVER-IP:32400` | Plex server URL |
| `PLEXTOKEN` | Your token | Plex authentication token |
| `PLEXSCANPATH` | `/media/music` | Plex's view of the music path |

### Lidarr Variables

| Variable | Recommended | Description |
|---|---:|---|
| `LIDARR_LIST_IMPORT` | `false` | Import artists from Lidarr list |
| `LIDARR_URL` | empty or URL | Lidarr server URL |
| `LIDARR_API_KEY` | empty or key | Lidarr API key |

### File Permission Variables

| Variable | Recommended | Description |
|---|---:|---|
| `FILE_PERMISSIONS` | `777` or `644` | File permissions for completed music files |
| `FOLDER_PERMISSIONS` | `777` or `755` | Folder permissions for completed music folders |

---

## Artist Tag Cleanup

AMA-Unraid 2.0.0 includes a safe artist cleanup step designed for Plex and Roon.

It keeps featured artists in the track title while keeping the `ARTIST` and `ALBUMARTIST` tags clean.

### Example 1: Featured artist already in title

Before cleanup:

```text
TITLE=FAR FETCHED (feat. Ty Dolla $ign)
ARTIST=Leon Thomas;Ty Dolla $ign
album_artist=Leon Thomas
```

After cleanup:

```text
TITLE=FAR FETCHED (feat. Ty Dolla $ign)
ARTIST=Leon Thomas
ALBUMARTIST=Leon Thomas
```

### Example 2: Featured artist only in ARTIST tag

Before cleanup:

```text
TITLE=Crash & Burn (Remix)
ARTIST=Leon Thomas;Blxst
album_artist=Leon Thomas
```

After cleanup:

```text
TITLE=Crash & Burn (Remix) (feat. Blxst)
ARTIST=Leon Thomas
ALBUMARTIST=Leon Thomas
```

This is enabled by default:

```text
ENABLE_ARTIST_TAG_CLEANUP=true
```

To disable it:

```text
ENABLE_ARTIST_TAG_CLEANUP=false
```

The older tag normalizer is optional and disabled by default:

```text
ENABLE_TAG_NORMALIZER=false
```

### Expected Clean Tag Output

A featured track should look like this after AMA processing:

```text
TITLE=Crash & Burn (Remix) (feat. Blxst)
ARTIST=Leon Thomas
ALBUMARTIST=Leon Thomas
```

A heavy-feature album such as a DJ Khaled release should look like this:

```text
TITLE=Song Name (feat. Featured Artist 1 & Featured Artist 2)
ARTIST=DJ Khaled
ALBUMARTIST=DJ Khaled
```

The `ARTIST` field should not contain semicolon-separated featured artists, such as:

```text
ARTIST=DJ Khaled;Featured Artist
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

If no lyrics exist from Deemix, LRCLIB, or embedded metadata, AMA leaves the track without an `.lrc` file.

---

## Deemix API Queue Wait

Some large albums may remain in Deemix's queue before files begin appearing. AMA waits longer while Deemix reports the album as queued, then uses a shorter file-stability check after audio files appear.

Useful variables:

```text
DEEMIX_API_MAX_POLLS=8
DEEMIX_API_QUEUE_MAX_POLLS=120
```

`DEEMIX_API_QUEUE_MAX_POLLS` controls how long AMA waits while Deemix still has the album queued.

`DEEMIX_API_MAX_POLLS` controls the shorter normal polling/stability behavior after the album begins producing files.

### Example Deemix API Flow

When working correctly, the log flow should look similar to this:

```text
Sending "https://deezer.com/album/ALBUM_ID" to download client...
DEEMIX_API :: Album URL: https://deezer.com/album/ALBUM_ID
DEEMIX_API :: Login OK
DEEMIX_API :: Album accepted by Deemix
DEEMIX_API :: Max polls: 8
DEEMIX_API :: Queue max polls: 120
DEEMIX_API :: Check 1 status=inQueue audio=0 lrc=0 stable=0
DEEMIX_API :: Check 2 status=inQueue audio=0 lrc=0 stable=0
DEEMIX_API :: Check 3 status=completed audio=12 lrc=0 stable=0
Processing album folder: /deemix-downloads/Artist/Album
Created timed .lrc from LRCLIB synced
DEEMIX_API :: Copying files into AMA temp folder
ARTIST_CLEANUP :: processed=12
CONVERSION :: SKIPPED :: Deemix API already provided downloaded files
Adding Replaygain Tags using r128gain
Plex Scan notification sent!
```

---

## Plex Scan Path Override

If Plex sees the music path differently than AMA, set:

```text
PLEXSCANPATH=/media/music
```

Example:

AMA container path:

```text
/downloads-ama
```

Plex library path:

```text
/media/music
```

With `PLEXSCANPATH=/media/music`, AMA sends Plex the corrected scan path:

```text
/media/music/Artist/Album
```

instead of:

```text
/downloads-ama/Artist/Album
```

---

## Full Run Log Output

AMA-Unraid 2.0.0 saves the full run log and prints the full log when the script exits.

The saved run log is written to:

```text
/config/logs
```

Example:

```text
/config/logs/ama-run-YYYYMMDD-HHMMSS.log
```

This makes it easier to review the complete run after the terminal window closes.

---

## Basic Usage

1. Make sure your Deemix WebUI/API container is running and logged in.
2. Make sure AMA has access to the Deemix config and download folders.
3. Add one or more artist files to `/config/list`.
4. Start the AMA script.
5. AMA will process the artist list, send albums to Deemix API, post-process the files, and notify Plex if enabled.

Start manually:

```bash
docker exec -it AMA-Unraid bash /config/scripts/start.bash
```

Watch logs:

```bash
docker logs -f --tail=300 AMA-Unraid
```

---

## Docker Compose Example

```yaml
services:
  ama-unraid:
    image: ghcr.io/crywolf203/ama-unraid:latest
    container_name: AMA-Unraid
    restart: unless-stopped
    network_mode: bridge
    environment:
      TZ: "America/New_York"
      PUID: "99"
      PGID: "100"

      AUTOSTART: "false"
      SCRIPTINTERVAL: "7d"
      MODE: "artist"

      DOWNLOAD_CLIENT: "deemix_api"
      DEEMIX_API_URL: "http://10.13.1.138:6595"
      DEEMIX_CONFIG_PATH: "/deemix-config"
      DEEMIX_DOWNLOAD_PATH: "/deemix-downloads"
      DEEMIX_API_MAX_POLLS: "8"
      DEEMIX_API_QUEUE_MAX_POLLS: "120"

      FORMAT: "FLAC"
      FORCECONVERT: "false"
      REPLAYGAIN: "true"
      POSTPROCESSTHREADS: "8"
      EMBEDDED_COVER_QUALITY: "100"

      ENABLE_ARTIST_TAG_CLEANUP: "true"
      ENABLE_TAG_NORMALIZER: "false"

      NOTIFYPLEX: "true"
      PLEXLIBRARYNAME: "Music"
      PLEXURL: "http://10.13.1.138:32400"
      PLEXTOKEN: "YOUR-PLEX-TOKEN"
      PLEXSCANPATH: "/media/music"

      FILE_PERMISSIONS: "777"
      FOLDER_PERMISSIONS: "777"

    volumes:
      - /mnt/cache/appdata/ama-unraid:/config
      - /mnt/user/media/music:/downloads-ama
      - /mnt/cache/appdata/Deemix-1:/deemix-config
      - /mnt/user/media2/deemix-1:/deemix-downloads
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
  -e MODE="artist" \
  -e DOWNLOAD_CLIENT="deemix_api" \
  -e DEEMIX_API_URL="http://10.13.1.138:6595" \
  -e DEEMIX_CONFIG_PATH="/deemix-config" \
  -e DEEMIX_DOWNLOAD_PATH="/deemix-downloads" \
  -e DEEMIX_API_MAX_POLLS="8" \
  -e DEEMIX_API_QUEUE_MAX_POLLS="120" \
  -e FORMAT="FLAC" \
  -e FORCECONVERT="false" \
  -e REPLAYGAIN="true" \
  -e POSTPROCESSTHREADS="8" \
  -e EMBEDDED_COVER_QUALITY="100" \
  -e ENABLE_ARTIST_TAG_CLEANUP="true" \
  -e ENABLE_TAG_NORMALIZER="false" \
  -e NOTIFYPLEX="true" \
  -e PLEXLIBRARYNAME="Music" \
  -e PLEXURL="http://10.13.1.138:32400" \
  -e PLEXTOKEN="YOUR-PLEX-TOKEN" \
  -e PLEXSCANPATH="/media/music" \
  -e FILE_PERMISSIONS="777" \
  -e FOLDER_PERMISSIONS="777" \
  -v /mnt/cache/appdata/ama-unraid:/config:rw \
  -v /mnt/user/media/music:/downloads-ama:rw \
  -v /mnt/cache/appdata/Deemix-1:/deemix-config:rw \
  -v /mnt/user/media2/deemix-1:/deemix-downloads:rw \
  ghcr.io/crywolf203/ama-unraid:latest
```

---

## Troubleshooting Deemix API Mode

### Deemix API says files were not found

If the log shows:

```text
DEEMIX_API :: Check 1 status=inQueue audio=0
```

then Deemix accepted the album but has not started writing files yet.

Increase:

```text
DEEMIX_API_QUEUE_MAX_POLLS
```

This is especially helpful for large albums or when several albums are queued.

### Albums show as already downloaded even after deleting files

AMA and Deemix both keep cache/queue state.

Clear the relevant artist or album from:

```text
/config/cache
/config/list
/deemix-config/queue
/deemix-downloads
/downloads-ama
```

### Tags show featured artists as primary artists

Confirm:

```text
ENABLE_ARTIST_TAG_CLEANUP=true
```

Expected clean result:

```text
TITLE=Song Name (feat. Featured Artist)
ARTIST=Album Artist
ALBUMARTIST=Album Artist
```

### Featured artists disappear from the title

This usually means a previous cleanup removed the featured artist from the `ARTIST` tag before it was moved into the title.

For a clean redownload, clear the affected album from:

```text
/downloads-ama
/deemix-downloads
/deemix-config/queue
/config/cache
```

Then redownload with:

```text
ENABLE_ARTIST_TAG_CLEANUP=true
```

### Plex does not update after tags are fixed

Refresh metadata in Plex for the affected artist or album after files are retagged.

```text
Plex Artist Page → three dots → Refresh Metadata
```

For stubborn cases, empty trash and rescan the music library.

### Roon does not update after tags are fixed

Force a rescan in Roon.

```text
Settings → Storage → three dots on the music folder → Force Rescan
```

For stubborn albums, remove and re-add the album or adjust Roon's album edit settings to prefer file metadata.

### Permission issues

Check:

```text
PUID=99
PGID=100
FILE_PERMISSIONS=777
FOLDER_PERMISSIONS=777
```

Also confirm your `/downloads-ama` mapping is Read/Write.

---

## Related Projects

| Project | Link |
|---|---|
| AMA-Unraid maintained fork | https://github.com/crywolf203/ama-unraid |
| Unraid template repo | https://github.com/crywolf203/unraid-templates |
| Revived Deemix project | https://github.com/bambanah/deemix |
| Original AMA creator | https://github.com/RandomNinjaAtk |
| LRCLIB | https://lrclib.net |
| Plex | https://www.plex.tv |
| Roon | https://roon.app |

---

## Credits and Acknowledgements

AMA-Unraid builds on the work of several open-source projects and maintainers.

### Original AMA Project

AMA, Automated Music Archiver, was originally created by **RandomNinjaAtk**.

- Original AMA script/project: `RandomNinjaAtk/ama`
- Original Docker-based AMA project: `RandomNinjaAtk/docker-ama`
- AMA-Unraid maintained fork: `crywolf203/ama-unraid`

This maintained AMA-Unraid fork continues the original goal of automatically archiving music for use in applications such as Plex, Kodi, Jellyfin, and Emby.

### AMA-Unraid Maintained Fork

This fork is maintained by **crywolf203**.

AMA-Unraid 2.0.0 adds the Deemix API download path, timed LRC fallback handling, safer Plex/Roon metadata cleanup, improved Deemix API queue waiting, Plex scan path overrides, and updated Unraid template support.

### Deemix

The Deemix API mode uses the revived Deemix project maintained at:

```text
https://github.com/bambanah/deemix
```

The revived Deemix project is maintained by **bambanah** and credits the original Deemix project as being created by **RemixDev**.

The Deemix project provides the pieces used by the Deemix API workflow, including:

- `deezer-sdk`
- `deemix`
- `webui`
- `gui`

### Thank You

Special thanks to:

- **RandomNinjaAtk** for the original AMA project
- **crywolf203** for maintaining and extending AMA-Unraid
- **bambanah** for the revived Deemix project
- **RemixDev** for the original Deemix project
- **Bockiii** for Deemix Docker inspiration

---

## Funding

This project is a community-maintained Unraid fork and integration wrapper around upstream/open-source tools.

If you find the upstream projects useful, consider supporting the original developers and maintainers first.

If this Unraid-focused fork, template work, documentation, or troubleshooting saves you time, you can support this maintenance work here:

<p align="center">
  <a href="https://buymeacoffee.com/crywolf203">
    <img alt="Buy Me a Coffee" src="https://img.shields.io/badge/Support-Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge">
  </a>
</p>

```text
https://buymeacoffee.com/crywolf203
```

---

## Disclaimer

Use this container only with accounts, content, and services you are authorized to access.

This repository does not claim ownership of upstream projects. It packages, documents, and extends the workflow for Unraid users.
