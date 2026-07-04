# AMA-Unraid

Unraid-friendly Automated Music Archiver with **Deemix Direct**, synced `.lrc` lyrics, ReplayGain, Plex/Roon-friendly metadata cleanup, high-quality album art, and clean post-processing.

AMA-Unraid is a community-maintained Unraid-focused fork of Automated Music Archiver, originally created by RandomNinjaAtk.

---

## What AMA-Unraid Does

AMA-Unraid automates a music archiving workflow for Unraid users.

It can:

* Monitor artist list files
* Find albums from Deezer artist IDs
* Download albums using internal Deemix Direct mode
* Use a safe temporary workflow through `/downloads-ama/temp`
* Embed high-quality album artwork
* Save high-quality local `cover.jpg` artwork
* Fall back to another audio format when FLAC is unavailable
* Add or fetch synced `.lrc` lyrics
* Clean artist tags for Plex and Roon
* Apply ReplayGain
* Notify Plex to scan the completed album folder
* Save logs for troubleshooting

The recommended workflow is:

```bash
DOWNLOAD_CLIENT=deemix_direct
```

Legacy external Deemix API mode is still available:

```bash
DOWNLOAD_CLIENT=deemix_api
```

New installs should use **Deemix Direct** unless you specifically need the older external Deemix API container workflow.

---

## Docker Image

```bash
ghcr.io/crywolf203/ama-unraid:latest
```

Versioned tag:

```bash
ghcr.io/crywolf203/ama-unraid:2.0.0
```

---

## Recommended Unraid Install

Install from Unraid Community Applications when available.

Search for:

```text
AMA-Unraid
```

Manual Docker image value:

```bash
ghcr.io/crywolf203/ama-unraid:latest
```

Recommended download client:

```bash
DOWNLOAD_CLIENT=deemix_direct
```

Unraid template repository:

```text
https://github.com/crywolf203/unraid-templates
```

---

## Recommended Mode: Deemix Direct

Set:

```bash
DOWNLOAD_CLIENT=deemix_direct
```

Deemix Direct runs Deemix inside the AMA-Unraid container instead of sending albums to a separate Deemix WebUI/API container.

### Deemix Direct Flow

The safe direct-temp flow works like this:

1. AMA cleans `/downloads-ama/temp` before each album.
2. Deemix downloads the album directly into `/downloads-ama/temp`.
3. AMA finds the temporary downloaded album folder.
4. AMA adds the album ID to the temporary album folder when needed.
5. AMA runs `lrc_fallback.py` using `/downloads-ama/temp` and the album ID.
6. AMA flattens audio files, `.lrc` files, and `cover.jpg` into `/downloads-ama/temp`.
7. AMA continues normal import, tag cleanup, ReplayGain, permissions, and Plex notification.

The internal working folder is:

```bash
/downloads-ama/temp
```

Do not map `/downloads-ama/temp` separately. It is created and managed internally by AMA-Unraid.

---

## Required Paths

| Container Path   | Example Host Path               |     Access | Purpose                                                        |
| ---------------- | ------------------------------- | ---------: | -------------------------------------------------------------- |
| `/config`        | `/mnt/cache/appdata/ama-unraid` | Read/Write | AMA config, scripts, cache, logs, and artist list files        |
| `/downloads-ama` | `/mnt/user/media/music`         | Read/Write | Final processed music library and internal temp working folder |
| `/deemix-config` | `/mnt/cache/appdata/Deemix-1`   | Read/Write | Deemix login/config folder containing `login.json`             |

Example mappings:

```bash
/mnt/cache/appdata/ama-unraid:/config:rw
/mnt/user/media/music:/downloads-ama:rw
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

---

## Deemix Login

Deemix Direct needs either a valid Deemix login file:

```bash
/deemix-config/login.json
```

Or an ARL token:

```bash
ARL_TOKEN=your_arl_token_here
```

Recommended method:

```bash
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

The mapped folder should contain:

```bash
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
6. AMA processes the artist list, downloads albums with Deemix Direct, post-processes the files, and notifies Plex if enabled.

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

## Deemix Direct Runtime Settings

Deemix Direct writes its own runtime config for the internal Deemix CLI so each album downloads directly into:

```bash
/downloads-ama/temp
```

The direct script sets these internal Deemix options during the run:

```text
downloadLocation=/downloads-ama/temp
albumTracknameTemplate=%discnumber%%tracknumber% - %title%
tracknameTemplate=%discnumber%%tracknumber% - %title%
createSingleFolder=true
queueConcurrency=1
fallbackBitrate=True
embeddedArtworkSize=1400
localArtworkSize=1400
jpegImageQuality=100
embeddedArtworkPNG=False
tags.cover=True
```

You can adjust direct Deemix concurrency with:

```bash
DEEMIX_QUEUE_CONCURRENCY=1
```

The recommended value is `1` because AMA processes albums one at a time and the temp folder is cleaned before each album.

---

## Bitrate Fallback Behavior

AMA-Unraid currently enables Deemix bitrate fallback:

```python
config["fallbackBitrate"] = True
```

This means if `FORMAT=FLAC` is requested but FLAC is not available for a release, Deemix may fall back to a lower available format instead of failing the download.

Example log behavior:

```text
Desired bitrate not found, falling back to lower bitrate
```

Possible fallback formats include:

```text
.mp3
.m4a
.opus
```

This is helpful when you want the album to download even if lossless quality is unavailable.

Important note:

* Current fallback behavior is enabled in the script.
* A future improvement may add a variable such as `DEEMIX_FALLBACK_BITRATE=true/false`.
* If you need strict FLAC-only behavior, watch the output format carefully until fallback handling is made configurable.

---

## High-Quality Album Artwork

AMA-Unraid configures Deemix to use high-quality artwork.

Current artwork behavior:

```python
config["embeddedArtworkSize"] = 1400
config["localArtworkSize"] = 1400
config["jpegImageQuality"] = 100
config["embeddedArtworkPNG"] = False
config["tags"]["cover"] = True
```

This means:

* Embedded artwork is requested at 1400px.
* Local artwork such as `cover.jpg` is requested at 1400px.
* JPEG artwork quality is set to 100.
* Embedded artwork uses JPEG instead of PNG.
* Cover artwork tagging is enabled.

The goal is high-quality artwork without unnecessarily large embedded PNG files.

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

---

### Deemix Direct Variables

| Variable                   |         Recommended | Description                                      |
| -------------------------- | ------------------: | ------------------------------------------------ |
| `DOWNLOAD_CLIENT`          |     `deemix_direct` | Uses the internal Deemix Direct workflow         |
| `DEEMIX_CONFIG_PATH`       |    `/deemix-config` | Container path to the Deemix login/config folder |
| `ARL_TOKEN`                | empty or your token | Optional fallback login method                   |
| `DEEMIX_QUEUE_CONCURRENCY` |                 `1` | Internal Deemix direct download concurrency      |

---

### Artwork Variables

| Variable                       | Recommended | Description                                   |
| ------------------------------ | ----------: | --------------------------------------------- |
| `DEEMIX_EMBEDDED_ARTWORK_SIZE` |      `1400` | Embedded album artwork size                   |
| `DEEMIX_LOCAL_ARTWORK_SIZE`    |      `1400` | Local album artwork size, such as `cover.jpg` |
| `DEEMIX_JPEG_IMAGE_QUALITY`    |       `100` | JPEG artwork quality                          |
| `EMBEDDED_COVER_QUALITY`       |       `100` | Legacy/fallback artwork quality variable      |

Recommended artwork settings:

```bash
DEEMIX_EMBEDDED_ARTWORK_SIZE=1400
DEEMIX_LOCAL_ARTWORK_SIZE=1400
DEEMIX_JPEG_IMAGE_QUALITY=100
```

`EMBEDDED_COVER_QUALITY` is still supported as a fallback, but `DEEMIX_JPEG_IMAGE_QUALITY` is preferred for Deemix Direct artwork quality.

---

### Download and Post-Processing Variables

| Variable             | Recommended | Description                                     |
| -------------------- | ----------: | ----------------------------------------------- |
| `FORMAT`             |      `FLAC` | Desired output format                           |
| `BITRATE`            |       `320` | Bitrate setting used for MP3-style output paths |
| `FORCECONVERT`       |     `false` | Recommended false for Deemix Direct             |
| `REPLAYGAIN`         |      `true` | Adds ReplayGain tags after download             |
| `POSTPROCESSTHREADS` |         `8` | Number of post-processing threads               |
| `REQUIRE_QUALITY`    |     `false` | Require requested quality before processing     |

Recommended:

```bash
FORMAT=FLAC
BITRATE=320
FORCECONVERT=false
REPLAYGAIN=true
REQUIRE_QUALITY=false
```

Note about `REQUIRE_QUALITY`:

Current Deemix Direct fallback behavior may allow a lower available format when FLAC is unavailable. A future update should make fallback behavior stricter when `REQUIRE_QUALITY=true`.

---

### Tag and Metadata Variables

| Variable                    | Recommended | Description                                                  |
| --------------------------- | ----------: | ------------------------------------------------------------ |
| `ENABLE_ARTIST_TAG_CLEANUP` |      `true` | Keeps featured artists in the title and primary artist clean |
| `ENABLE_TAG_NORMALIZER`     |     `false` | Legacy broader tag normalizer. Disabled by default           |

Recommended:

```bash
ENABLE_ARTIST_TAG_CLEANUP=true
ENABLE_TAG_NORMALIZER=false
```

---

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

---

### Plex Variables

| Variable          |              Recommended | Description                   |
| ----------------- | -----------------------: | ----------------------------- |
| `NOTIFYPLEX`      |                   `true` | Notify Plex after each album  |
| `PLEXLIBRARYNAME` |                  `Music` | Plex music library name       |
| `PLEXURL`         | `http://SERVER-IP:32400` | Plex server URL               |
| `PLEXTOKEN`       |               your token | Plex authentication token     |
| `PLEXSCANPATH`    |           `/media/music` | Plex's view of the music path |

---

### Lidarr Variables

| Variable             |  Recommended | Description                     |
| -------------------- | -----------: | ------------------------------- |
| `LIDARR_LIST_IMPORT` |      `false` | Import artists from Lidarr list |
| `LIDARR_URL`         | empty or URL | Lidarr server URL               |
| `LIDARR_API_KEY`     | empty or key | Lidarr API key                  |

---

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

The LRC fallback call should use the temp root plus album ID, not the temporary album subfolder.

Correct:

```bash
lrc_fallback.py /downloads-ama/temp ALBUM_ID
```

---

## Full Run Logs

AMA-Unraid saves run logs in:

```bash
/config/logs
```

From the Unraid host, this usually maps to:

```bash
/mnt/cache/appdata/ama-unraid/logs
```

Main AMA run logs look like:

```bash
/config/logs/script_run_1_YYYY_MM_DD_HH_MM_AM.log
```

Deemix Direct per-album logs look like:

```bash
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
grep -nE "DEEMIX_DIRECT|lrc_fallback|LRC|lyrics|Flattening|ERROR|Traceback|Exception|failed|Failed" /config/logs/*.log | tail -n 300
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
      REQUIRE_QUALITY: "false"

      DEEMIX_EMBEDDED_ARTWORK_SIZE: "1400"
      DEEMIX_LOCAL_ARTWORK_SIZE: "1400"
      DEEMIX_JPEG_IMAGE_QUALITY: "100"

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
  -e REQUIRE_QUALITY="false" \
  -e DEEMIX_EMBEDDED_ARTWORK_SIZE="1400" \
  -e DEEMIX_LOCAL_ARTWORK_SIZE="1400" \
  -e DEEMIX_JPEG_IMAGE_QUALITY="100" \
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

If FLAC is unavailable and bitrate fallback is used, the audio file may be a fallback format:

```text
/downloads-ama/temp/01 - Track.mp3
/downloads-ama/temp/01 - Track.lrc
/downloads-ama/temp/cover.jpg
```

---

## Artist Tag Cleanup

AMA-Unraid includes a safe artist cleanup step designed for Plex and Roon.

It keeps featured artists in the track title while keeping the `ARTIST` and `ALBUMARTIST` tags clean.

The cleanup script currently supports these audio formats:

```text
.flac
.mp3
.m4a
.opus
```

This matters because Deemix bitrate fallback may produce MP3, M4A, or OPUS files when FLAC is unavailable.

### Example 1: Featured Artist Already in Title

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

### Example 2: Featured Artist Only in ARTIST Tag

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

Artist cleanup is enabled by default:

```bash
ENABLE_ARTIST_TAG_CLEANUP=true
```

The older tag normalizer is optional and disabled by default:

```bash
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

```bash
lrc_fallback.py /downloads-ama/temp ALBUM_ID
```

That allows the fallback script to find the temporary album folder by album ID and write sidecar `.lrc` files before AMA flattens the temp folder.

---

## ReplayGain

AMA-Unraid can apply ReplayGain tags after download.

Enable with:

```bash
REPLAYGAIN=true
```

ReplayGain helps normalize playback volume across tracks and albums without permanently changing the audio.

---

## Plex Scan Path Override

If Plex sees the music path differently than AMA, set:

```bash
PLEXSCANPATH=/media/music
```

Example:

AMA container path:

```bash
/downloads-ama
```

Plex library path:

```bash
/media/music
```

With `PLEXSCANPATH=/media/music`, AMA sends Plex the corrected scan path:

```bash
/media/music/Artist/Album
```

Instead of:

```bash
/downloads-ama/Artist/Album
```

---

## Legacy Mode: External Deemix API

The older external Deemix API workflow is still available:

```bash
DOWNLOAD_CLIENT=deemix_api
```

This mode requires a separate running Deemix WebUI/API container.

Required variables:

```bash
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

```bash
/mnt/user/media2/deemix-1:/deemix-downloads:rw
```

New installs should prefer Deemix Direct unless there is a specific reason to keep an external Deemix API container in the workflow.

---

## Troubleshooting Deemix Direct

### Container Starts but AMA Does Not Run

If the log shows:

```text
Automatic Start Disabled, manually run using this command:
bash /config/scripts/start.bash
```

Then either enable:

```bash
AUTOSTART=true
```

Or start manually:

```bash
docker exec -it AMA-Unraid bash -lc 'bash /config/scripts/start.bash'
```

---

### Deemix Direct Cannot Log In

Confirm one of these exists:

```bash
/deemix-config/login.json
```

Or:

```bash
ARL_TOKEN=your_arl_token_here
```

Also confirm the path mapping is read/write:

```bash
/mnt/cache/appdata/Deemix-1:/deemix-config:rw
```

---

### FLAC Was Requested but MP3 Was Downloaded

This can happen when FLAC is unavailable and Deemix bitrate fallback is used.

Look for a log line like:

```text
Desired bitrate not found, falling back to lower bitrate
```

Current behavior allows fallback so the album can still complete.

A future improvement may make this behavior configurable.

---

### Lyrics Are Missing

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

---

### Temp Folder Is Not Flattened

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

---

### Albums Show as Already Downloaded After Deleting Files

AMA and Deemix can both keep cache or queue state.

For a clean redownload, clear the affected artist or album from the relevant locations:

```bash
/config/cache
/config/list
/downloads-ama/Artist/Album
/downloads-ama/temp
```

If using legacy external Deemix API mode, also clear:

```bash
/deemix-config/queue
/deemix-downloads
```

---

### Tags Show Featured Artists as Primary Artists

Confirm:

```bash
ENABLE_ARTIST_TAG_CLEANUP=true
```

Expected clean result:

```text
TITLE=Song Name (feat. Featured Artist)
ARTIST=Album Artist
ALBUMARTIST=Album Artist
```

---

### Plex Does Not Update After Tags Are Fixed

Refresh metadata in Plex for the affected artist or album after files are retagged.

```text
Plex Artist Page → three dots → Refresh Metadata
```

For stubborn cases, empty trash and rescan the music library.

---

### Roon Does Not Update After Tags Are Fixed

Force a rescan in Roon.

```text
Settings → Storage → three dots on the music folder → Force Rescan
```

For stubborn albums, remove and re-add the album or adjust Roon's album edit settings to prefer file metadata.

---

### Permission Issues

Check:

```bash
PUID=99
PGID=100
FILE_PERMISSIONS=777
FOLDER_PERMISSIONS=777
```

Also confirm your `/downloads-ama` mapping is read/write.

---

## Development Notes

Useful repo path on Unraid:

```bash
/mnt/cache/appdata/ama-unraid
```

Example:

```bash
cd /mnt/cache/appdata/ama-unraid
git status --short
```

Useful validation commands:

```bash
bash -n root/scripts/deemix_direct_download.bash
python3 -m py_compile root/scripts/artist_tag_cleanup.py
```

Recommended `.gitignore` entries:

```gitignore
__pycache__/
*.pyc
*.bak-*
```

---

## Recent Improvements

### High-Quality Deemix Album Art

Added high-quality Deemix album artwork settings:

```python
config["embeddedArtworkSize"] = 1400
config["localArtworkSize"] = 1400
config["jpegImageQuality"] = 100
config["embeddedArtworkPNG"] = False
config["tags"]["cover"] = True
```

Commit:

```text
0421acb Embed high quality Deemix album art
```

---

### Deemix Bitrate Fallback

Enabled Deemix bitrate fallback:

```python
config["fallbackBitrate"] = True
```

This allows Deemix to fall back to a lower available bitrate when the desired quality is unavailable.

---

### Artist Cleanup for Fallback Audio Formats

Updated artist cleanup so it is no longer FLAC-only.

Supported cleanup formats:

```text
.flac
.mp3
.m4a
.opus
```

The cleanup script uses Mutagen’s generic loader so fallback formats can still be processed after download.

Commit:

```text
c2e0a61 Fix artist cleanup for fallback audio formats
```

---

## Planned Improvements

These improvements are planned but may not be implemented yet.

### Configurable Bitrate Fallback

Planned variable:

```bash
DEEMIX_FALLBACK_BITRATE=true
```

Expected behavior:

```bash
DEEMIX_FALLBACK_BITRATE=true
```

Fallback enabled.

```bash
DEEMIX_FALLBACK_BITRATE=false
```

Fallback disabled.

Default should remain enabled so current behavior does not change.

---

### Bitrate Fallback Logging

Planned log example:

```text
DEEMIX_DIRECT :: fallbackBitrate=True
```

Or:

```text
DEEMIX_DIRECT :: fallbackBitrate=False
```

---

### Requested vs Actual Format Summary

Planned summary example:

```text
DEEMIX_DIRECT :: requested=flac actual_summary flac=0 mp3=1 m4a=0 opus=0
```

If fallback is used, the script should log a warning.

Example:

```text
DEEMIX_DIRECT :: WARNING fallback format used because requested FLAC was unavailable
```

---

### Artist Cleanup Extension Summary

Planned cleanup summary example:

```text
ARTIST_CLEANUP :: processed=1 flac=0 mp3=1 m4a=0 opus=0
```

---

### Respect Strict Quality Requirements

If strict quality is enabled later, bitrate fallback should probably be disabled or treated as a failure condition.

Expected behavior:

* If strict quality is disabled, fallback can be allowed.
* If strict quality is enabled, fallback should either be disabled or the download should fail when the requested quality is unavailable.

---

## Related Projects

| Project                    | Link                                             |
| -------------------------- | ------------------------------------------------ |
| AMA-Unraid maintained fork | `https://github.com/crywolf203/ama-unraid`       |
| Unraid template repo       | `https://github.com/crywolf203/unraid-templates` |
| Revived Deemix project     | `https://github.com/bambanah/deemix`             |
| Original AMA creator       | `https://github.com/RandomNinjaAtk`              |
| LRCLIB                     | `https://lrclib.net`                             |
| Plex                       | `https://www.plex.tv`                            |
| Roon                       | `https://roon.app`                               |

---

## Credits and Acknowledgements

AMA-Unraid builds on the work of several open-source projects and maintainers.

### Original AMA Project

AMA, Automated Music Archiver, was originally created by RandomNinjaAtk.

* Original AMA script/project: `RandomNinjaAtk/ama`
* Original Docker-based AMA project: `RandomNinjaAtk/docker-ama`
* AMA-Unraid maintained fork: `crywolf203/ama-unraid`

This maintained AMA-Unraid fork continues the original goal of automatically archiving music for use in applications such as Plex, Kodi, Jellyfin, and Emby.

### AMA-Unraid Maintained Fork

This fork is maintained by crywolf203.

AMA-Unraid 2.0 adds Deemix Direct, the safe direct-temp download flow, timed LRC fallback handling, safer Plex/Roon metadata cleanup, ReplayGain support, Plex scan path overrides, high-quality album artwork handling, fallback audio format cleanup, and updated Unraid template support.

### Deemix

The Deemix Direct mode uses the revived Deemix project maintained at:

```text
https://github.com/bambanah/deemix
```

The revived Deemix project is maintained by bambanah and credits the original Deemix project as being created by RemixDev.

The Deemix project provides the pieces used by the direct workflow, including:

* `deezer-sdk`
* `deemix`
* `webui`
* `gui`

### Thank You

Special thanks to:

* RandomNinjaAtk for the original AMA project
* crywolf203 for maintaining and extending AMA-Unraid
* bambanah for the revived Deemix project
* RemixDev for the original Deemix project
* Bockiii for Deemix Docker inspiration

---

## Funding

This project is a community-maintained Unraid fork and integration wrapper around upstream/open-source tools.

If you find the upstream projects useful, consider supporting the original developers and maintainers first.

If this Unraid-focused fork, template work, documentation, or troubleshooting saves you time, you can support this maintenance work here:

```text
https://buymeacoffee.com/crywolf203
```

---

## Disclaimer

Use this container only with accounts, content, and services you are authorized to access.

This repository does not claim ownership of upstream projects. It packages, documents, and extends the workflow for Unraid users.
