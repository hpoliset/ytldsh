#!/bin/bash
#
# YouTube Playlist Audio Sync - For Apple Shortcuts
# 
# Setup:
# 1. Edit configuration below
# 2. chmod +x ~/Scripts/sync_youtube_playlist.sh
# 3. Create Shortcut (see instructions at bottom)
#

# =============================================================================
# ENVIRONMENT SETUP (needed for Shortcuts - it doesn't inherit your PATH)
# =============================================================================

# Add common paths for Homebrew, Python, etc.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$HOME/.local/bin:$HOME/Library/Python/3.9/bin:$HOME/Library/Python/3.10/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.12/bin:$PATH"

# For Apple Silicon Macs
if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# For Intel Macs
if [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# =============================================================================
# CONFIGURATION - EDIT THESE
# =============================================================================

PLAYLIST_ID="PLXx0GjECc_WXCHTQenReX8sZg5R633-Kw"
OUTPUT_DIR="$HOME/Music/YouTube Playlist"
AUDIO_FORMAT="m4a"
AUDIO_QUALITY="192"
PYTHON_SCRIPT="$HOME/ytldsh/yt_playlist_sync.py"
COOKIES_BROWSER="chrome"

# Set to "true" if video titles follow "Artist - Song Title" format
PARSE_TITLE_ARTIST="false"

# =============================================================================
# LOGGING (for debugging)
# =============================================================================

LOG_FILE="$HOME/Scripts/sync_youtube.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo ""
echo "=========================================="
echo "Sync started: $(date)"
echo "=========================================="

# =============================================================================
# SCRIPT
# =============================================================================

mkdir -p "$OUTPUT_DIR"

# Check dependencies with helpful error messages
if ! command -v yt-dlp &> /dev/null; then
    echo "ERROR: yt-dlp not found!"
    echo "PATH is: $PATH"
    echo "Install with: pip3 install yt-dlp"
    osascript -e 'display notification "yt-dlp not found! Run: pip3 install yt-dlp" with title "🎵 YouTube Sync" subtitle "Error" sound name "Basso"'
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found!"
    echo "PATH is: $PATH"
    osascript -e 'display notification "python3 not found! Install Python first." with title "🎵 YouTube Sync" subtitle "Error" sound name "Basso"'
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Sync script not found at $PYTHON_SCRIPT"
    osascript -e "display notification \"Sync script not found\" with title \"🎵 YouTube Sync\" subtitle \"Error\" sound name \"Basso\""
    exit 1
fi

echo "Using python3: $(which python3)"
echo "Using yt-dlp: $(which yt-dlp)"
echo "Python script: $PYTHON_SCRIPT"

# Build optional flags
EXTRA_FLAGS=""
if [ "$PARSE_TITLE_ARTIST" = "true" ]; then
    EXTRA_FLAGS="$EXTRA_FLAGS --parse-title-artist"
fi

# Run sync with notifications and metadata embedding enabled
python3 "$PYTHON_SCRIPT" \
    "$PLAYLIST_ID" \
    --cookies-from-browser "$COOKIES_BROWSER" \
    --audio-format "$AUDIO_FORMAT" \
    --audio-quality "$AUDIO_QUALITY" \
    --output "$OUTPUT_DIR" \
    --notify \
    $EXTRA_FLAGS

EXIT_CODE=$?
echo "Sync finished with exit code: $EXIT_CODE"
echo ""

exit $EXIT_CODE


# =============================================================================
# APPLE SHORTCUTS SETUP
# =============================================================================
#
# 1. Save this script:
#    mkdir -p ~/Scripts
#    mv sync_youtube_playlist.sh ~/Scripts/
#    chmod +x ~/Scripts/sync_youtube_playlist.sh
#
# 2. Open Shortcuts app (Spotlight → "Shortcuts")
#
# 3. Click + to create new Shortcut
#
# 4. Search for "Run Shell Script" and add it
#
# 5. Configure:
#    - Shell: /bin/bash
#    - Input: (leave as default)
#    - Paste this in the script box:
#      /Users/KDP/Scripts/sync_youtube_playlist.sh
#
# 6. Click the name at top, rename to "Sync YouTube Playlist"
#
# 7. Optional - Add to Menu Bar:
#    - Click (i) icon → "Pin in Menu Bar"
#
# 8. Optional - Keyboard Shortcut:
#    - Click (i) icon → "Add Keyboard Shortcut"
#
# Now you can run it via:
#    - Spotlight: type "Sync YouTube Playlist"
#    - Menu bar: click Shortcuts icon
#    - Siri: "Run Sync YouTube Playlist"
#    - Keyboard shortcut (if set)
#
# =============================================================================
