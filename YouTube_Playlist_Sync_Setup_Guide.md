# YouTube Playlist Audio Sync - Mac Setup Guide

A complete guide to set up automatic YouTube playlist audio syncing on a new Mac.

---

## What You'll Get

- A tool that downloads audio from any YouTube playlist
- Automatically skips already-downloaded songs
- macOS notifications for each download
- One-click sync via Spotlight, Siri, menu bar, or keyboard shortcut

---

## Step 1: Install Homebrew (if not installed)

Homebrew is a package manager for Mac. Open **Terminal** (Spotlight → type "Terminal") and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts. When done, **close and reopen Terminal**.

---

## Step 2: Install Python and FFmpeg

```bash
brew install python ffmpeg
```

Verify installation:
```bash
python3 --version    # Should show Python 3.x
ffmpeg -version      # Should show FFmpeg version
```

---

## Step 3: Install yt-dlp

**Option A: Via Homebrew (recommended)**
```bash
brew install yt-dlp
```

**Option B: Via pip**
```bash
pip3 install yt-dlp
```

Either works — the script uses the command-line tool, not the Python library.

Verify:
```bash
yt-dlp --version
```

---

## Step 4: Download the Sync Scripts

### Option A: If you have the files from Claude

Move the files to their proper locations:

```bash
# Create Scripts folder
mkdir -p ~/Scripts

# Move the Python script to Downloads (or wherever you prefer)
mv ~/Downloads/yt_playlist_sync.py ~/Downloads/

# Move the shell script to Scripts
mv ~/Downloads/sync_youtube_playlist.sh ~/Scripts/

# Make it executable
chmod +x ~/Scripts/sync_youtube_playlist.sh
```

### Option B: Download fresh (if needed)

If you need to download the scripts again, save them from Claude to your Downloads folder, then run the commands above.

---

## Step 5: Configure Your Playlist

Edit the shell script with your playlist details:

```bash
nano ~/Scripts/sync_youtube_playlist.sh
```

Change these lines at the top:

```bash
PLAYLIST_ID="YOUR_PLAYLIST_ID_HERE"           # e.g., PLXx-Kw123abc...
OUTPUT_DIR="$HOME/Music/YouTube Playlist"      # Where to save files
AUDIO_FORMAT="m4a"                             # mp3, m4a, flac, etc.
AUDIO_QUALITY="192"                            # kbps
PYTHON_SCRIPT="$HOME/Downloads/yt_playlist_sync.py"
COOKIES_BROWSER="chrome"                       # chrome, firefox, safari, edge
```

**How to find your Playlist ID:**
1. Open the playlist on YouTube
2. Look at the URL: `youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx`
3. Copy everything after `list=` — that's your playlist ID

Save and exit: Press `Ctrl+X`, then `Y`, then `Enter`

---

## Step 6: Test the Script

Run it manually first to make sure everything works:

```bash
~/Scripts/sync_youtube_playlist.sh
```

You should see:
- Notifications appearing in the top-right corner
- Songs downloading to your output folder
- A "Complete ✓" notification when done

**Troubleshooting:**
- If you get "permission denied": `chmod +x ~/Scripts/sync_youtube_playlist.sh`
- If yt-dlp not found: `pip3 install yt-dlp`
- If ffmpeg not found: `brew install ffmpeg`

---

## Step 7: Create Apple Shortcut

1. Open **Shortcuts** app (Spotlight → type "Shortcuts")

2. Click **+** (top right) to create a new Shortcut

3. In the search bar on the right, type **"Run Shell Script"**

4. Drag **Run Shell Script** to the workflow area

5. Configure the action:
   - **Shell**: `/bin/bash`
   - **Input**: No Input (or leave default)
   - **Pass Input**: (leave default)
   - In the script text box, paste:
     ```
     ~/Scripts/sync_youtube_playlist.sh
     ```

6. Click **"New Shortcut"** at the top and rename it to:
   ```
   Sync YouTube Playlist
   ```

7. Done! Close the Shortcuts app.

---

## Step 8: Optional Enhancements

### Add to Menu Bar
1. In Shortcuts, find your shortcut
2. Right-click → **Open**
3. Click the **(i)** info button (top right)
4. Enable **"Pin in Menu Bar"**

Now you'll see a Shortcuts icon in your menu bar with quick access.

### Add Keyboard Shortcut
1. Open your shortcut's info (same as above)
2. Click **"Add Keyboard Shortcut"**
3. Press your preferred keys (e.g., `⌘⇧Y`)

### Add to Dock
1. In Shortcuts app, right-click your shortcut
2. **Add to Dock**

---

## How to Use

| Method | How |
|--------|-----|
| **Spotlight** | Press `⌘Space`, type "Sync YouTube Playlist", press Enter |
| **Siri** | "Hey Siri, run Sync YouTube Playlist" |
| **Menu Bar** | Click Shortcuts icon → select it |
| **Keyboard** | Press your custom shortcut (if set) |
| **Terminal** | `~/Scripts/sync_youtube_playlist.sh` |

---

## Notifications You'll See

| Stage | Notification |
|-------|--------------|
| Start | 🎵 "Starting" - Extracting playlist... |
| Loaded | 🎵 "Playlist loaded" - Found 57 videos |
| Each download | 🎵 "Downloaded (1/5)" - Song Title |
| Failed | 🎵 "Failed (2/5)" - Problem Song |
| Complete | 🎵 "Complete ✓" - Downloaded 5 songs |
| Up to date | 🎵 "Up to date ✓" - No new songs |

---

## Files Created

After running, your output folder will contain:

```
~/Music/YouTube Playlist/
├── playlist_videos.csv          # List of all videos in playlist
├── .download_archive.txt        # Tracks downloaded video IDs
├── Song Title 1.m4a
├── Song Title 2.m4a
└── ...
```

---

## Keeping yt-dlp Updated

YouTube frequently changes things. Keep yt-dlp updated:

```bash
# If installed via Homebrew:
brew upgrade yt-dlp

# If installed via pip:
pip3 install -U yt-dlp
```

Run this monthly or whenever downloads start failing.

---

## Multiple Playlists

To sync multiple playlists, create separate shell scripts:

```bash
# Copy the script
cp ~/Scripts/sync_youtube_playlist.sh ~/Scripts/sync_jazz_playlist.sh
cp ~/Scripts/sync_youtube_playlist.sh ~/Scripts/sync_workout_playlist.sh

# Edit each one with different PLAYLIST_ID and OUTPUT_DIR
nano ~/Scripts/sync_jazz_playlist.sh
```

Then create separate Shortcuts for each.

---

## Troubleshooting

### "Requested format is not available"
This usually means yt-dlp needs updating:
```bash
brew upgrade yt-dlp
# or if installed via pip:
pip3 install -U yt-dlp
```

### "Command not found: python3"
Install Python via Homebrew:
```bash
brew install python
```

### "Command not found: yt-dlp"
```bash
brew install yt-dlp
# or
pip3 install yt-dlp
```

### "No videos found in playlist"
- Check your playlist ID is correct
- For private playlists, make sure `COOKIES_BROWSER` matches your logged-in browser
- Try a different browser: `chrome`, `firefox`, `safari`, `edge`

### Notifications not appearing
- Check System Preferences → Notifications → Script Editor (allow)
- Check System Preferences → Notifications → Terminal (allow)

### Script runs but no output
Make sure the Python script path is correct:
```bash
ls -la ~/Downloads/yt_playlist_sync.py
```

---

## Quick Reference Card

```bash
# Manual sync with notifications
python3 ~/Downloads/yt_playlist_sync.py PLAYLIST_ID --cookies-from-browser chrome --notify --audio-format m4a

# Update yt-dlp (choose one)
brew upgrade yt-dlp
pip3 install -U yt-dlp

# Test shell script
~/Scripts/sync_youtube_playlist.sh

# Edit configuration
nano ~/Scripts/sync_youtube_playlist.sh

# Check log if Shortcut fails
cat ~/Scripts/sync_youtube.log
```

---

## Summary Checklist

- [ ] Homebrew installed
- [ ] Python 3 installed (`brew install python`)
- [ ] FFmpeg installed (`brew install ffmpeg`)
- [ ] yt-dlp installed (`brew install yt-dlp` or `pip3 install yt-dlp`)
- [ ] `yt_playlist_sync.py` saved to `~/Downloads/`
- [ ] `sync_youtube_playlist.sh` saved to `~/Scripts/` and made executable
- [ ] Playlist ID configured in shell script
- [ ] Output directory configured
- [ ] Manual test successful
- [ ] Apple Shortcut created
- [ ] (Optional) Pinned to menu bar / keyboard shortcut added

🎉 **You're all set!** Run "Sync YouTube Playlist" anytime to grab new songs.
