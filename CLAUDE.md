# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Playlist Audio Sync (`ytldsh`) - A macOS-focused tool for syncing YouTube playlists to local audio files with notification support. The tool downloads audio from YouTube playlists, tracks what's been downloaded, and can be triggered via Apple Shortcuts, Spotlight, Siri, or keyboard shortcuts.

## Core Components

### 1. `yt_playlist_sync.py` - Main Python Script
The core sync engine that handles:
- **Playlist extraction**: Uses `yt-dlp --flat-playlist --dump-json` to get video metadata
- **CSV tracking**: Maintains `playlist_videos.csv` with all videos (new and existing)
- **Download archive**: Uses `.download_archive.txt` (yt-dlp format) to skip already-downloaded videos
- **Audio download**: Calls `yt-dlp -x` to extract audio from individual videos
- **macOS notifications**: Uses AppleScript `osascript` to send notifications

### 2. `sync_youtube_playlist.sh` - Wrapper Script
Shell wrapper designed for Apple Shortcuts integration:
- Sets up PATH environment (Shortcuts doesn't inherit user PATH)
- Handles both Apple Silicon (`/opt/homebrew`) and Intel Macs (`/usr/local/bin`)
- Provides dependency checking with user-friendly error messages
- Logs to `~/Scripts/sync_youtube.log`
- Configurable playlist ID, output directory, audio format, quality, and browser for cookies

## Key Architecture Decisions

### Cookie Usage (IMPORTANT)
**As of mid-2026, cookies are needed for BOTH playlist extraction AND downloading individual videos.**

- Playlist extraction uses cookies to access private playlists
- Individual video downloads use cookies only when `--use-cookies-for-download` is passed; `sync_youtube_playlist.sh` sets this by default
- **Why**: YouTube rolled out SABR-only streaming with a PO-token requirement on cookie-free download requests (tracked upstream in [yt-dlp#12482](https://github.com/yt-dlp/yt-dlp/issues/12482)). Unauthenticated downloads now fail with `HTTP Error 403: Forbidden` on every video. An authenticated (cookie-bearing) session avoids this.
- **Historical note**: earlier versions of this doc said the opposite - that cookies caused a degraded, thumbnail-only response on download. That was true at the time but YouTube's behavior has since flipped; if downloads start failing with 403 again in the future, re-verify this assumption with a direct `yt-dlp -v` test (with and without `--cookies-from-browser`) rather than trusting either direction blindly.
- This is a critical, YouTube-behavior-dependent design decision - do not change without testing against real download failures

### File Tracking System
The tool uses TWO tracking mechanisms:
1. **CSV file** (`playlist_videos.csv`): Human-readable master list with fields:
   - `video_id`, `title`, `url`, `duration`, `uploader`, `added_date`, `downloaded`
   - Preserves history of all videos ever in the playlist
   - Updates `downloaded` field to 'yes' when download succeeds

2. **Download archive** (`.download_archive.txt`): yt-dlp's native format
   - Format: `youtube VIDEO_ID` (one per line)
   - Used by yt-dlp's `--download-archive` flag to skip downloads
   - Source of truth for what's been downloaded

### Workflow
1. Extract playlist metadata using cookies (if needed for private playlists)
2. Update CSV with new videos while preserving existing entries
3. Identify pending downloads (videos in CSV but not in archive)
4. Download audio for pending videos WITHOUT cookies
5. Mark as downloaded in both archive and CSV

## Common Commands

### Run Full Sync
```bash
# Via shell script (recommended for Shortcuts)
~/Scripts/sync_youtube_playlist.sh

# Via Python directly
python3 yt_playlist_sync.py "PLxxxxx" --output ~/Music/Playlist --notify
```

### Testing and Development
```bash
# Test playlist extraction only (no download)
python3 yt_playlist_sync.py "PLxxxxx" --no-download --verbose

# Force re-download everything
python3 yt_playlist_sync.py "PLxxxxx" --no-skip

# Download specific format/quality
python3 yt_playlist_sync.py "PLxxxxx" -f m4a -q 320

# Private playlist (needs cookies)
python3 yt_playlist_sync.py "PLxxxxx" --cookies-from-browser chrome

# For playlists where video titles are "Artist - Song Title" format
python3 yt_playlist_sync.py "PLxxxxx" --parse-title-artist
```

### Debugging
```bash
# Check dependencies
which yt-dlp python3 ffmpeg

# View shell script logs
tail -f ~/Scripts/sync_youtube.log

# Test yt-dlp directly
yt-dlp --flat-playlist --dump-json "https://youtube.com/playlist?list=PLxxxxx"

# Check what's pending download
python3 -c "
import csv
pending = []
with open('downloads/playlist_videos.csv') as f:
    for row in csv.DictReader(f):
        if row['downloaded'] != 'yes':
            pending.append(row['title'])
print(f'Pending: {len(pending)}')
"
```

## Dependencies

Required system dependencies (install via Homebrew):
- `yt-dlp` - YouTube downloader (CLI tool, not Python library)
- `ffmpeg` - Audio/video processing (used by yt-dlp for audio extraction)
- `python3` - Python 3.x

The scripts use subprocess calls to `yt-dlp` CLI, not the Python library.

## Configuration

Shell script configuration variables (in `sync_youtube_playlist.sh`):
- `PLAYLIST_ID` - YouTube playlist ID (everything after `list=` in URL)
- `OUTPUT_DIR` - Where to save audio files
- `AUDIO_FORMAT` - Format: mp3, m4a, aac, flac, opus, wav
- `AUDIO_QUALITY` - Quality in kbps (e.g., 192, 320)
- `PYTHON_SCRIPT` - Path to `yt_playlist_sync.py`
- `COOKIES_BROWSER` - Browser to extract cookies from (chrome, firefox, safari, edge)

## Apple Shortcuts Integration

The shell script is designed to be called from Apple Shortcuts:
- Sets up PATH explicitly (Shortcuts doesn't inherit environment)
- Handles both Apple Silicon and Intel Mac paths
- Provides notifications for progress tracking
- Logs all output to file for debugging

## File Output Structure

After running, the output directory contains:
```
OUTPUT_DIR/
├── playlist_videos.csv        # Master list of all videos
├── .download_archive.txt      # yt-dlp's download tracking
├── Song Title 1.m4a          # Audio files
├── Song Title 2.m4a
└── ...
```

## Error Handling

Common issues and their causes:
- **"Requested format is not available"** - yt-dlp needs updating
- **"No videos found in playlist"** - Wrong playlist ID or needs cookies for private playlist
- **"Command not found: yt-dlp"** - yt-dlp not installed or not in PATH
- **Downloads fail with `HTTP Error 403: Forbidden` (no cookies)** - YouTube now requires an authenticated session for downloads too; add `--use-cookies-for-download` (see "Cookie Usage" above)
- **Downloads fail even with `--use-cookies-for-download`** - yt-dlp may be out of date; `brew upgrade yt-dlp` and retry

## Maintenance

Keep yt-dlp updated monthly (YouTube changes frequently):
```bash
brew upgrade yt-dlp
# or
pip3 install -U yt-dlp
```
