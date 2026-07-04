<p align="center">
  <img src="https://raw.githubusercontent.com/crywolf203/unraid-templates/main/ama-unraid-icon.png?v=2026-05-26" alt="AMA-Unraid icon" width="160">
</p>

<h1 align="center">AMA-Unraid</h1>

<p align="center">
  <strong>Unraid-friendly Automated Music Archiver with Deemix Direct support, synced lyrics, ReplayGain, Plex/Roon-friendly metadata cleanup, and clean post-processing.</strong>
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
    <img alt="Deemix" src="https://img.shields.io/badge/Deemix-Direct%20Mode-purple?style=flat-square">
  </a>
</p>

---

## What is AMA-Unraid?

**AMA-Unraid** is a community-maintained Unraid-focused fork of **Automated Music Archiver**, originally created by **RandomNinjaAtk**.

This fork is designed for Unraid users who want an automated music archiving workflow that can:

* Monitor artist list files
* Find artist albums from Deezer artist IDs
* Download albums using internal **Deemix Direct** mode
* Use a safe direct-temp workflow through `/downloads-ama/temp`
* Add or fetch `.lrc` synced lyrics
* Clean metadata for Plex and Roon
* Apply ReplayGain
* Notify Plex to scan the finished album folder
* Save useful logs for future debugging

The recommended workflow is **Deemix Direct**:

```text
DOWNLOAD_CLIENT=deemix_direct
```

Legacy external Deemix API mode is still available with:

```text
DOWNLOAD_CLIENT=deemix_api
```

New installs should use **Deemix Direct** unless you specifically need the older external API container workflow.

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

Recommended download client:

```text
DOWNLOAD_CLIENT=deemix_direct
```

Unraid template repository:

```text
https://github.com/crywolf203/unraid-templates
```

---

## Recommended Mode: Deemix Direct

Set:

```text
DOWNLOAD_CLIENT=deemix_direct
```

Deemix Direct runs Deemix inside the AMA-Unraid container instead of sending albums to a separate Deemix WebUI/API container.

The safe direct-temp flow is:

```text
1. Clean /downloads-ama/temp before each album
2. Let deemix download directly into /downloads-ama/temp
3. Find the downloaded album folder
4. Add the album ID to the temporary album folder when needed
5. Run lrc_fallback.py with /downloads-ama/temp and the album ID
6. Flatten audio files, .lrc files, and cover.jpg into /downloads-ama/temp
7. Let AMA continue normal import, tagging, ReplayGain, permissions, and Plex notification
```

There is currently **no separate staging folder required**.

The internal working folder is:

```text
/downloads-ama/temp
```

AMA cleans that temp folder before each album, uses it as the safe Deemix download area, then flattens the album files into the temp root so normal AMA post-processing can continue.

---

## Required Paths

| Container Path   | Example Host Path               |     Access | Purpose                                                        |
| ---------------- | ------------------------------- | ---------: | -------------------------------------------------------------- |
| `/config`        | `/mnt/cache/appdata/ama-unraid` | Read/Write | AMA config, scripts, cache, logs, and artist list files        |
| `/downloads-ama` | `/mnt/user/media/music`         | Read/Write | Final processed music library and internal temp working folder |
| `/deemix-config` | `/mnt/cache/appdata/Deemix-1`   | Read/Write | Deemix login/config folder containing `login.json`             |

Example mappings:

```text
/mnt/cache/appdata/ama-unraid:/config:rw
/mnt/user/media/music:/downloads-ama:rw
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

`/downloads-ama/temp` is created and managed internally by AMA-Unraid. Do not map it separately.

---

## Deemix Login

Deemix Direct needs either:

```text
/deemix-config/login.json
```

or:

```text
ARL_TOKEN=your_arl_token_here
```

Recommended method:

```text
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

The mapped folder should contain:

```text
/deemix-config/login.json
```

If Deemix is not logged in, log into the Deemix WebUI first, force update the ARL if needed, then restart AMA-Unraid.

Do not publish your `login.json` or ARL token.

---

## Basic Usage

1. Configure the container with `DOWNLOAD_CLIENT=deemix_direct`.
2. Make sure `/config`, `/downloads-ama`, and `/deemix-config` are mapped read/write.
3. Make sure `/deemix-config/login.json` exists, or set `ARL_TOKEN`.
4. Add one or more artist files to `/config/list`.
5. Start AMA manually or enable autostart.
6. AMA will process the artist list, download albums with Deemix Direct, post-process the files, and notify Plex if enabled.

Start manually:

```bash
docker exec -it AMA-Unraid bash -lc 'bash /config/scripts/start.bash'
```

Watch Docker logs:

```bash
docker logs -f --tail=300 AMA-Unraid
```

View saved AMA run logs from the host:

```bash
ls -lah /mnt/cache/appdata/ama-unraid/logs

tail -f -n 300 "$(ls -t /mnt/cache/appdata/ama-unraid/logs/*.log | head -1)"
```

View saved logs from inside the container:

```bash
docker exec -it AMA-Unraid bash -lc 'ls -lah /config/logs && tail -f -n 300 "$(ls -t /config/logs/*.log | head -1)"'
```

---

## Artist List Files

AMA processes artists from the `/config/list` folder.

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

To process only one artist, clear the list folder and add one `.file` entry.

Example from the Unraid host:

```bash
mkdir -p /mnt/cache/appdata/ama-unraid/list
rm -f /mnt/cache/appdata/ama-unraid/list/*
touch "/mnt/cache/appdata/ama-unraid/list/5828-DJ Khaled.file"
```

---

## Recommended Deemix Direct Settings

Deemix Direct writes its own runtime config for the internal Deemix CLI so the album download lands directly in:

```text
/downloads-ama/temp
```

The direct script sets these internal Deemix options during the run:

```text
downloadLocation=/downloads-ama/temp
albumTracknameTemplate=%discnumber%%tracknumber% - %title%
tracknameTemplate=%discnumber%%tracknumber% - %title%
createSingleFolder=true
queueConcurrency=1
```

You can adjust direct Deemix concurrency with:

```text
DEEMIX_QUEUE_CONCURRENCY=1
```

The recommended value is `1` because AMA processes albums one at a time and the temp folder is cleaned before each album.

---

## Environment Variables

### Core Variables

| Variable          |        Recommended | Description                                             |
| ----------------- | -----------------: | ------------------------------------------------------- |
| `PUID`            |               `99` | Runs files as the Unraid `nobody` user                  |
| `PGID`            |              `100` | Runs files as the Unraid `users` group                  |
| `TZ`              | `America/New_York` | Container timezone                                      |
| `AUTOSTART`       |  `false` or `true` | Automatically run AMA when the container starts         |
| `SCRIPTINTERVAL`  |               `7d` | Interval between runs when autostart looping is enabled |
| `MODE`            |           `artist` | Artist-list processing mode                             |
| `DOWNLOAD_CLIENT` |    `deemix_direct` | Recommended download backend                            |

### Deemix Direct Variables

| Variable                   |         Recommended | Description                                  |
| -------------------------- | ------------------: | -------------------------------------------- |
| `DOWNLOAD_CLIENT`          |     `deemix_direct` | Uses the internal Deemix Direct workflow     |
| `DEEMIX_CONFIG_PATH`       |    `/deemix-config` | Container path to Deemix `login.json` folder |
| `ARL_TOKEN`                | empty or your token | Optional fallback login method               |
| `DEEMIX_QUEUE_CONCURRENCY` |                 `1` | Internal Deemix direct download concurrency  |

### Download and Post-Processing Variables

| Variable                 | Recommended | Description                                     |
| ------------------------ | ----------: | ----------------------------------------------- |
| `FORMAT`                 |      `FLAC` | Desired output format                           |
| `BITRATE`                |       `320` | Bitrate setting used for MP3-style output paths |
| `FORCECONVERT`           |     `false` | Recommended false for Deemix Direct             |
| `REPLAYGAIN`             |      `true` | Adds ReplayGain tags after download             |
| `POSTPROCESSTHREADS`     |         `8` | Number of post-processing threads               |
| `EMBEDDED_COVER_QUALITY` |       `100` | Embedded cover quality percentage               |
| `REQUIRE_QUALITY`        |     `false` | Require requested quality before processing     |

### Tag and Metadata Variables

| Variable                    | Recommended | Description                                              |
| --------------------------- | ----------: | -------------------------------------------------------- |
| `ENABLE_ARTIST_TAG_CLEANUP` |      `true` | Keeps featured artists in title and primary artist clean |
| `ENABLE_TAG_NORMALIZER`     |     `false` | Legacy broader tag normalizer. Disabled by default       |

### Album Filtering Variables

| Variable                      | Recommended | Description                       |
| ----------------------------- | ----------: | --------------------------------- |
| `ALBUM_TYPE_FILTER`           |   `COMPILE` | Album filtering mode              |
| `IGNORE_ARTIST_WITHOUT_IMAGE` |      `true` | Ignore artists without images     |
| `RELATED_ARTIST`              |     `false` | Import related artists            |
| `RELATED_ARTIST_RELATED`      |     `false` | Related artist loop mode          |
| `RELATED_COUNT`               |         `0` | Maximum related artists to import |
| `FAN_COUNT`                   |        `10` | Minimum fan count threshold       |
| `COMPLETE_MY_ARTISTS`         |     `false` | Complete known artists            |

### Plex Variables

| Variable          |              Recommended | Description                   |
| ----------------- | -----------------------: | ----------------------------- |
| `NOTIFYPLEX`      |                   `true` | Notify Plex after each album  |
| `PLEXLIBRARYNAME` |                  `Music` | Plex music library name       |
| `PLEXURL`         | `http://SERVER-IP:32400` | Plex server URL               |
| `PLEXTOKEN`       |               Your token | Plex authentication token     |
| `PLEXSCANPATH`    |           `/media/music` | Plex's view of the music path |

### Lidarr Variables

| Variable             |  Recommended | Description                     |
| -------------------- | -----------: | ------------------------------- |
| `LIDARR_LIST_IMPORT` |      `false` | Import artists from Lidarr list |
| `LIDARR_URL`         | empty or URL | Lidarr server URL               |
| `LIDARR_API_KEY`     | empty or key | Lidarr API key                  |

### File Permission Variables

| Variable             |    Recommended | Description                                    |
| -------------------- | -------------: | ---------------------------------------------- |
| `FILE_PERMISSIONS`   | `777` or `644` | File permissions for completed music files     |
| `FOLDER_PERMISSIONS` | `777` or `755` | Folder permissions for completed music folders |

---

## Deemix Direct Log Flow

When Deemix Direct is working correctly, the log flow should look similar to this:

```text
AMA: Download Client: Deemix Direct Internal
Sending "https://deezer.com/album/ALBUM_ID" to download client...
DEEMIX_DIRECT :: Log file: /config/logs/deemix-direct-ALBUM_ID-YYYYMMDD-HHMMSS.log
DEEMIX_DIRECT :: Album URL: https://deezer.com/album/ALBUM_ID
DEEMIX_DIRECT :: Album ID:  ALBUM_ID
DEEMIX_DIRECT :: Temp dir:   /downloads-ama/temp
DEEMIX_DIRECT :: Flow:       direct-temp
DEEMIX_DIRECT :: Cleaning AMA temp before album
DEEMIX_DIRECT :: Wrote Deemix config: /config/deemix/xdg/deemix/config.json
DEEMIX_DIRECT :: Album folder before LRC ID check: /downloads-ama/temp/Artist/Album
DEEMIX_DIRECT :: Adding album ID to folder for LRC fallback: /downloads-ama/temp/Artist/Album [ALBUM_ID]
DEEMIX_DIRECT :: Running LRC fallback root: /downloads-ama/temp
DEEMIX_DIRECT :: Running LRC fallback album ID: ALBUM_ID
Created timed .lrc from LRCLIB synced
DEEMIX_DIRECT :: LRC summary: audio=12 lrc_found=12 lrc_missing=0
DEEMIX_DIRECT :: Flattening downloaded files into AMA temp root
DEEMIX_DIRECT :: Moved media/LRC files into AMA temp: 24
DEEMIX_DIRECT :: Temp audio count: 12
DEEMIX_DIRECT :: Temp LRC count:   12
DEEMIX_DIRECT :: Temp cover count: 1
DEEMIX_DIRECT :: Done
ARTIST_CLEANUP :: processed=12
Adding ReplayGain tags using rsgain
Plex Scan notification sent!
```

The most important Deemix Direct checks are:

```text
DEEMIX_DIRECT :: Running LRC fallback root: /downloads-ama/temp
DEEMIX_DIRECT :: Running LRC fallback album ID: ALBUM_ID
DEEMIX_DIRECT :: Temp audio count: greater than 0
```

The direct LRC fallback call should use the temp root plus album ID, not the temporary album subfolder.

---

## Full Run Logs

AMA-Unraid saves run logs in:

```text
/config/logs
```

From the Unraid host, this usually maps to:

```text
/mnt/cache/appdata/ama-unraid/logs
```

Main AMA run logs look like:

```text
/config/logs/script_run_1_YYYY_MM_DD_HH_MM_AM.log
```

Deemix Direct per-album logs look like:

```text
/config/logs/deemix-direct-ALBUM_ID-YYYYMMDD-HHMMSS.log
```

Useful log commands:

```bash
# Follow container stdout/stderr
docker logs -f --tail=300 AMA-Unraid

# List saved logs
docker exec -it AMA-Unraid bash -lc 'ls -lah /config/logs'

# Tail the newest saved log
docker exec -it AMA-Unraid bash -lc 'tail -f -n 300 "$(ls -t /config/logs/*.log | head -1)"'

# Focus only on Deemix Direct and common error lines
docker exec -it AMA-Unraid bash -lc '
grep -nE "DEEMIX_DIRECT|lrc_fallback|LRC|lyrics|Flattening|TEMP DEBUG|ERROR|Traceback|Exception|failed|Failed" /config/logs/*.log | tail -n 300
'
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

      DOWNLOAD_CLIENT: "deemix_direct"
      DEEMIX_CONFIG_PATH: "/deemix-config"
      DEEMIX_QUEUE_CONCURRENCY: "1"

      FORMAT: "FLAC"
      BITRATE: "320"
      FORCECONVERT: "false"
      REPLAYGAIN: "true"
      POSTPROCESSTHREADS: "8"
      EMBEDDED_COVER_QUALITY: "100"
      REQUIRE_QUALITY: "false"

      ENABLE_ARTIST_TAG_CLEANUP: "true"
      ENABLE_TAG_NORMALIZER: "false"

      ALBUM_TYPE_FILTER: "COMPILE"
      IGNORE_ARTIST_WITHOUT_IMAGE: "true"
      RELATED_ARTIST: "false"
      RELATED_ARTIST_RELATED: "false"
      RELATED_COUNT: "0"
      FAN_COUNT: "10"
      COMPLETE_MY_ARTISTS: "false"

      NOTIFYPLEX: "true"
      PLEXLIBRARYNAME: "Music"
      PLEXURL: "http://SERVER-IP:32400"
      PLEXTOKEN: "YOUR-PLEX-TOKEN"
      PLEXSCANPATH: "/media/music"

      LIDARR_LIST_IMPORT: "false"
      LIDARR_URL: ""
      LIDARR_API_KEY: ""

      FILE_PERMISSIONS: "777"
      FOLDER_PERMISSIONS: "777"

    volumes:
      - /mnt/cache/appdata/ama-unraid:/config:rw
      - /mnt/user/media/music:/downloads-ama:rw
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
  -e MODE="artist" \
  -e DOWNLOAD_CLIENT="deemix_direct" \
  -e DEEMIX_CONFIG_PATH="/deemix-config" \
  -e DEEMIX_QUEUE_CONCURRENCY="1" \
  -e FORMAT="FLAC" \
  -e BITRATE="320" \
  -e FORCECONVERT="false" \
  -e REPLAYGAIN="true" \
  -e POSTPROCESSTHREADS="8" \
  -e EMBEDDED_COVER_QUALITY="100" \
  -e REQUIRE_QUALITY="false" \
  -e ENABLE_ARTIST_TAG_CLEANUP="true" \
  -e ENABLE_TAG_NORMALIZER="false" \
  -e ALBUM_TYPE_FILTER="COMPILE" \
  -e IGNORE_ARTIST_WITHOUT_IMAGE="true" \
  -e RELATED_ARTIST="false" \
  -e RELATED_ARTIST_RELATED="false" \
  -e RELATED_COUNT="0" \
  -e FAN_COUNT="10" \
  -e COMPLETE_MY_ARTISTS="false" \
  -e NOTIFYPLEX="true" \
  -e PLEXLIBRARYNAME="Music" \
  -e PLEXURL="http://SERVER-IP:32400" \
  -e PLEXTOKEN="YOUR-PLEX-TOKEN" \
  -e PLEXSCANPATH="/media/music" \
  -e LIDARR_LIST_IMPORT="false" \
  -e LIDARR_URL="" \
  -e LIDARR_API_KEY="" \
  -e FILE_PERMISSIONS="777" \
  -e FOLDER_PERMISSIONS="777" \
  -v /mnt/cache/appdata/ama-unraid:/config:rw \
  -v /mnt/user/media/music:/downloads-ama:rw \
  -v /mnt/cache/appdata/Deemix-1:/deemix-config:rw \
  ghcr.io/crywolf203/ama-unraid:latest
```

---

## Testing Deemix Direct Manually

You can test the Deemix Direct script with a single album URL:

```bash
docker exec -it AMA-Unraid bash -lc '
DOWNLOAD_CLIENT=deemix_direct \
DEEMIX_CONFIG_PATH=/deemix-config \
FORMAT=FLAC \
bash /config/scripts/deemix_direct_download.bash "https://www.deezer.com/album/ALBUM_ID"
'
```

Then check the temp root:

```bash
docker exec -it AMA-Unraid bash -lc '
find /downloads-ama/temp -maxdepth 1 -type f | sort
'
```

Expected temp-root output should include audio files, matching `.lrc` files when lyrics are found, and `cover.jpg`:

```text
/downloads-ama/temp/01 - Track.flac
/downloads-ama/temp/01 - Track.lrc
/downloads-ama/temp/cover.jpg
```

---

## Artist Tag Cleanup

AMA-Unraid includes a safe artist cleanup step designed for Plex and Roon.

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

The older tag normalizer is optional and disabled by default:

```text
ENABLE_TAG_NORMALIZER=false
```

Expected clean tag output:

```text
TITLE=Song Name (feat. Featured Artist)
ARTIST=Album Artist
ALBUMARTIST=Album Artist
```

The `ARTIST` field should not contain semicolon-separated featured artists, such as:

```text
ARTIST=Album Artist;Featured Artist
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

For Deemix Direct, the fallback is run with:

```text
lrc_fallback.py /downloads-ama/temp ALBUM_ID
```

That allows the fallback script to find the temporary album folder by album ID and write sidecar `.lrc` files before AMA flattens the temp folder.

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

## Legacy Mode: External Deemix API

The older external Deemix API workflow is still available:

```text
DOWNLOAD_CLIENT=deemix_api
```

This mode requires a separate running Deemix WebUI/API container.

Required variables:

```text
DOWNLOAD_CLIENT=deemix_api
DEEMIX_API_URL=http://SERVER-IP:6595
DEEMIX_CONFIG_PATH=/deemix-config
DEEMIX_DOWNLOAD_PATH=/deemix-downloads
```

Required extra path:

| Container Path      | Example Host Path           |     Access | Purpose                                                                    |
| ------------------- | --------------------------- | ---------: | -------------------------------------------------------------------------- |
| `/deemix-downloads` | `/mnt/user/media2/deemix-1` | Read/Write | Deemix completed download folder used by the external Deemix API container |

Example mapping:

```text
/mnt/user/media2/deemix-1:/deemix-downloads:rw
```

New installs should prefer Deemix Direct unless there is a specific reason to keep an external Deemix API container in the workflow.

---

## Troubleshooting Deemix Direct

### Container starts but AMA does not run

If the log shows:

```text
Automatic Start Disabled, manually run using this command:
bash /config/scripts/start.bash
```

then either enable:

```text
AUTOSTART=true
```

or start manually:

```bash
docker exec -it AMA-Unraid bash -lc 'bash /config/scripts/start.bash'
```

### Deemix Direct cannot log in

Confirm one of these exists:

```text
/deemix-config/login.json
```

or:

```text
ARL_TOKEN=your_arl_token_here
```

Also confirm the path mapping is read/write:

```text
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

### Lyrics are missing

Check the Deemix Direct log:

```bash
docker exec -it AMA-Unraid bash -lc '
grep -nE "Running LRC fallback|LRC summary|Missing LRC|Created timed|Created plain|No lyrics" /config/logs/*.log | tail -n 200
'
```

For Deemix Direct, the log should show:

```text
DEEMIX_DIRECT :: Running LRC fallback root: /downloads-ama/temp
DEEMIX_DIRECT :: Running LRC fallback album ID: ALBUM_ID
```

### Temp folder is not flattened

After a direct test, this should show files directly in `/downloads-ama/temp`:

```bash
docker exec -it AMA-Unraid bash -lc 'find /downloads-ama/temp -maxdepth 1 -type f | sort'
```

Expected examples:

```text
/downloads-ama/temp/01 - Track.flac
/downloads-ama/temp/01 - Track.lrc
/downloads-ama/temp/cover.jpg
```

If files are still inside a nested album folder after the script says it is done, review:

```bash
docker exec -it AMA-Unraid bash -lc '
grep -nE "Flattening|Moved media|Temp audio count|Temp LRC count|ERROR" /config/logs/*.log | tail -n 200
'
```

### Albums show as already downloaded after deleting files

AMA and Deemix can both keep cache/queue state.

For a clean redownload, clear the affected artist or album from the relevant locations:

```text
/config/cache
/config/list
/downloads-ama/Artist/Album
/downloads-ama/temp
```

If using legacy external Deemix API mode, also clear:

```text
/deemix-config/queue
/deemix-downloads
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

| Project                    | Link                                           |
| -------------------------- | ---------------------------------------------- |
| AMA-Unraid maintained fork | https://github.com/crywolf203/ama-unraid       |
| Unraid template repo       | https://github.com/crywolf203/unraid-templates |
| Revived Deemix project     | https://github.com/bambanah/deemix             |
| Original AMA creator       | https://github.com/RandomNinjaAtk              |
| LRCLIB                     | https://lrclib.net                             |
| Plex                       | https://www.plex.tv                            |
| Roon                       | https://roon.app                               |

---

## Credits and Acknowledgements

AMA-Unraid builds on the work of several open-source projects and maintainers.

### Original AMA Project

AMA, Automated Music Archiver, was originally created by **RandomNinjaAtk**.

* Original AMA script/project: `RandomNinjaAtk/ama`
* Original Docker-based AMA project: `RandomNinjaAtk/docker-ama`
* AMA-Unraid maintained fork: `crywolf203/ama-unraid`

This maintained AMA-Unraid fork continues the original goal of automatically archiving music for use in applications such as Plex, Kodi, Jellyfin, and Emby.

### AMA-Unraid Maintained Fork

This fork is maintained by **crywolf203**.

AMA-Unraid 2.0 adds Deemix Direct, the safe direct-temp download flow, timed LRC fallback handling, safer Plex/Roon metadata cleanup, ReplayGain support, Plex scan path overrides, and updated Unraid template support.

### Deemix

The Deemix Direct mode uses the revived Deemix project maintained at:

```text
https://github.com/bambanah/deemix
```

The revived Deemix project is maintained by **bambanah** and credits the original Deemix project as being created by **RemixDev**.

The Deemix project provides the pieces used by the direct workflow, including:

* `deezer-sdk`
* `deemix`
* `webui`
* `gui`

### Thank You

Special thanks to:

* **RandomNinjaAtk** for the original AMA project
* **crywolf203** for maintaining and extending AMA-Unraid
* **bambanah** for the revived Deemix project
* **RemixDev** for the original Deemix project
* **Bockiii** for Deemix Docker inspiration

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
