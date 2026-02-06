# YouTube Playlist Audio Sync (ytldsh)

A macOS-focused tool that automatically syncs YouTube playlists to local audio files with smart duplicate detection and notification support. Trigger syncs via Apple Shortcuts, Spotlight, Siri, or keyboard shortcuts.

## Features

- 🎵 **Automatic playlist syncing** - Downloads audio from YouTube playlists
- ✅ **Smart duplicate detection** - Skips already-downloaded videos
- 📝 **CSV tracking** - Maintains a human-readable list of all videos
- 🔔 **macOS notifications** - Progress updates for each download
- 🎯 **Multiple trigger methods** - Spotlight, Siri, menu bar, or keyboard shortcuts
- 🔐 **Private playlist support** - Works with private/unlisted playlists using browser cookies
- 🎛️ **Configurable quality** - Choose audio format and bitrate

## Requirements

- macOS (tested on macOS Sonoma and later)
- [Homebrew](https://brew.sh) package manager
- Python 3.x
- yt-dlp (YouTube downloader)
- FFmpeg (audio processing)

## Installation

### 1. Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Dependencies

```bash
# Install required tools
brew install python ffmpeg yt-dlp

# Install Python crypto library for Chrome cookie decryption
python3 -m pip install --break-system-packages pycryptodomex
```

### 3. Clone or Download This Repository

```bash
# Clone the repository
git clone <repository-url> ~/ytldsh
cd ~/ytldsh

# Make scripts executable
chmod +x sync_youtube_playlist.sh
```

### 4. Configure Your Playlist

Edit `sync_youtube_playlist.sh` and update these variables:

```bash
PLAYLIST_ID="YOUR_PLAYLIST_ID_HERE"           # e.g., PLXx-Kw123abc...
OUTPUT_DIR="$HOME/Music/YouTube Playlist"      # Where to save files
AUDIO_FORMAT="m4a"                             # mp3, m4a, flac, etc.
AUDIO_QUALITY="192"                            # kbps (128, 192, 320)
PYTHON_SCRIPT="$HOME/ytldsh/yt_playlist_sync.py"
COOKIES_BROWSER="chrome"                       # chrome, firefox, safari, edge
```

**Finding your Playlist ID:**
1. Open the playlist on YouTube
2. Look at the URL: `youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx`
3. Copy everything after `list=` — that's your playlist ID

### 5. Grant Full Disk Access (Required for Private Playlists)

If using browser cookies to access private playlists:

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click **+** and add **Terminal** (`/System/Applications/Utilities/Terminal.app`)
3. Enable the checkbox next to Terminal
4. Restart Terminal

### 6. Test the Script

```bash
~/ytldsh/sync_youtube_playlist.sh
```

You should see notifications and songs downloading to your output folder.

## Setting Up Apple Shortcut

### Create the Shortcut

1. Open the **Shortcuts** app (Spotlight → type "Shortcuts")

2. Click **+** (top right) to create a new Shortcut

3. Search for **"Run Shell Script"** and drag it to the workflow area

4. Configure the action:
   - **Shell**: `/bin/bash`
   - **Script**:
     ```bash
     ~/ytldsh/sync_youtube_playlist.sh
     ```

5. Click **"New Shortcut"** at the top and rename it to: **"Sync YouTube Playlist"**

### Optional Enhancements

**Add to Menu Bar:**
1. Click the **(i)** info button on your shortcut
2. Enable **"Pin in Menu Bar"**

**Add Keyboard Shortcut:**
1. Click the **(i)** info button
2. Click **"Add Keyboard Shortcut"**
3. Press your preferred keys (e.g., `⌘⇧Y`)

**Add to Dock:**
1. Right-click your shortcut
2. Select **"Add to Dock"**

### Running the Shortcut

| Method | How |
|--------|-----|
| **Spotlight** | Press `⌘Space`, type "Sync YouTube Playlist", press Enter |
| **Siri** | "Hey Siri, run Sync YouTube Playlist" |
| **Menu Bar** | Click Shortcuts icon → select it |
| **Keyboard** | Press your custom shortcut (if set) |

## Usage

### Command Line

```bash
# Run full sync
~/ytldsh/sync_youtube_playlist.sh

# Or use Python directly
python3 yt_playlist_sync.py "PLxxxxx" --output ~/Music/Playlist --notify

# Test playlist extraction only (no download)
python3 yt_playlist_sync.py "PLxxxxx" --no-download --verbose

# Force re-download everything
python3 yt_playlist_sync.py "PLxxxxx" --no-skip

# Download specific format/quality
python3 yt_playlist_sync.py "PLxxxxx" -f m4a -q 320

# Private playlist (needs cookies)
python3 yt_playlist_sync.py "PLxxxxx" --cookies-from-browser chrome
```

### Python Script Options

```
  --output, -o DIR          Output directory (default: ./downloads)
  --audio-format, -f FMT    Audio format: mp3, m4a, aac, flac, opus, wav
  --audio-quality, -q KBPS  Audio quality in kbps (default: 192)
  --cookies-from-browser B  Browser for cookies: chrome, firefox, safari, edge
  --cookies, -c FILE        Path to cookies.txt file
  --no-download             Only update CSV, do not download
  --no-skip                 Re-download all videos (ignore archive)
  --notify, -n              Show macOS notifications
  --verbose, -v             Show detailed output
```

## File Structure

After running, your output directory will contain:

```
OUTPUT_DIR/
├── playlist_videos.csv        # Master list of all videos (human-readable)
├── .download_archive.txt      # yt-dlp's download tracking (video IDs)
├── Song Title 1.m4a          # Downloaded audio files
├── Song Title 2.m4a
└── ...
```

### Files Explained

- **`playlist_videos.csv`**: Complete list with video metadata (title, uploader, duration, download status)
- **`.download_archive.txt`**: yt-dlp's format for tracking downloaded videos (prevents duplicates)
- **Audio files**: Your downloaded songs in the specified format

## How It Works

### Architecture

1. **Playlist Extraction** (with cookies for private playlists)
   - Uses `yt-dlp --flat-playlist` to get video metadata
   - Cookies authenticate access to private/unlisted playlists

2. **CSV Tracking**
   - Updates `playlist_videos.csv` with new videos
   - Preserves history of all videos ever in playlist
   - Marks videos as downloaded when complete

3. **Download Archive**
   - Uses `.download_archive.txt` (yt-dlp's native format)
   - Source of truth for what's been downloaded
   - Prevents duplicate downloads

4. **Audio Download** (WITHOUT cookies)
   - Downloads only new/pending videos
   - Cookies are NOT used for individual downloads (they break YouTube's API)
   - Uses `yt-dlp -x` to extract audio

### Cookie Usage (Important!)

**Cookies are ONLY used for playlist extraction, NOT for downloading individual videos.**

- ✅ Playlist extraction: Uses cookies to access private playlists
- ❌ Video downloads: Does NOT use cookies (even if provided)
- Why? YouTube's cookie-authenticated API returns degraded responses with only thumbnails

## Notifications

| Stage | Notification |
|-------|--------------|
| Start | 🎵 "Starting" - Extracting playlist... |
| Loaded | 🎵 "Playlist loaded" - Found X videos |
| Each download | 🎵 "Downloaded (1/5)" - Song Title |
| Failed | 🎵 "Failed (2/5)" - Problem Song |
| Complete | 🎵 "Complete ✓" - Downloaded X songs |
| Up to date | 🎵 "Up to date ✓" - No new songs |

## Troubleshooting

### "HTTP Error 403: Forbidden"

**Solution:** Update yt-dlp (YouTube changes frequently)

```bash
brew upgrade yt-dlp
# or
pip3 install -U yt-dlp
```

### "The playlist does not exist" (but it does)

**Cause:** Cookie authentication failing

**Solutions:**
1. Grant Terminal **Full Disk Access** in System Settings
2. Install crypto library: `python3 -m pip install --break-system-packages pycryptodomex`
3. Make sure you're logged into YouTube in the browser specified in `COOKIES_BROWSER`

### "Command not found: yt-dlp"

**Solution:** Install yt-dlp

```bash
brew install yt-dlp
# or
pip3 install yt-dlp
```

### "Command not found: python3"

**Solution:** Install Python

```bash
brew install python
```

### Downloads work in Terminal but not via Apple Shortcut

**Cause:** Apple Shortcuts may need separate Full Disk Access

**Solution:** The shortcut runs through `/bin/bash` which inherits Terminal's permissions. If issues persist, check the log file:

```bash
cat ~/Scripts/sync_youtube.log
```

### No notifications appearing

**Solution:** Enable notifications for Terminal/Script Editor

1. **System Settings** → **Notifications** → **Terminal** (allow)
2. **System Settings** → **Notifications** → **Script Editor** (allow)

## Maintenance

### Keep yt-dlp Updated

YouTube frequently changes their API. Update monthly:

```bash
brew upgrade yt-dlp
# or
pip3 install -U yt-dlp
```

### Multiple Playlists

To sync multiple playlists, create separate shell scripts:

```bash
# Copy the script
cp sync_youtube_playlist.sh sync_jazz_playlist.sh
cp sync_youtube_playlist.sh sync_workout_playlist.sh

# Edit each with different PLAYLIST_ID and OUTPUT_DIR
nano sync_jazz_playlist.sh

# Create separate Shortcuts for each
```

## Logs

All output is logged to: `~/Scripts/sync_youtube.log`

```bash
# View recent activity
tail -f ~/Scripts/sync_youtube.log

# Search for errors
grep -i error ~/Scripts/sync_youtube.log
```

## Contributing

Feel free to submit issues or pull requests for improvements!

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful YouTube downloader
- [FFmpeg](https://ffmpeg.org) - Audio/video processing
