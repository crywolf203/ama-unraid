---

# AMA-Unraid 2.0.0 - Deemix API Mode

AMA-Unraid 2.0.0 adds a Deemix API download path for users who want AMA to use a running Deemix WebUI/API container instead of the legacy direct Deemix download flow.

## Major 2.0.0 Features

- Deemix API download client support
- Timed `.lrc` lyric fallback using LRCLIB when Deemix does not provide synced lyrics
- Safe artist tag cleanup for Plex/Roon-friendly metadata
- ReplayGain support after Deemix API downloads
- Plex scan path override support
- Improved Deemix API queue wait handling
- Full AMA run log output on script exit
- Optional legacy tag normalizer, disabled by default

---

## Deemix API Mode

Set:

```text
DOWNLOAD_CLIENT=deemix_api
```

AMA will send album URLs to the configured Deemix API, wait for Deemix to finish downloading, copy the completed files into AMA's temporary processing folder, then continue normal AMA post-processing.

### Required Variables

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

### Required Paths

The AMA container needs access to the same Deemix config and download folders used by the Deemix WebUI/API container.

Example:

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

---

## Artist Tag Cleanup

AMA-Unraid 2.0.0 includes a safe artist cleanup step designed for Plex and Roon.

It keeps featured artists in the track title while keeping the `ARTIST` and `ALBUMARTIST` tags clean.

Example before cleanup:

```text
TITLE=FAR FETCHED (feat. Ty Dolla $ign)
ARTIST=Leon Thomas;Ty Dolla $ign
album_artist=Leon Thomas
```

Example after cleanup:

```text
TITLE=FAR FETCHED (feat. Ty Dolla $ign)
ARTIST=Leon Thomas
ALBUMARTIST=Leon Thomas
```

For tracks where Deemix stores the featured artist only in the `ARTIST` tag, AMA moves the featured artist into the title.

Example:

```text
Before:
TITLE=Crash & Burn (Remix)
ARTIST=Leon Thomas;Blxst
album_artist=Leon Thomas

After:
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

### Docker Inspiration for Deemix

The revived Deemix project also credits **Bockiii** for Docker image inspiration.

### Thank You

Special thanks to:

- **RandomNinjaAtk** for the original AMA project
- **crywolf203** for maintaining and extending AMA-Unraid
- **bambanah** for the revived Deemix project
- **RemixDev** for the original Deemix project
- **Bockiii** for Deemix Docker image inspiration

---
