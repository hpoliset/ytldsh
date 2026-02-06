#!/usr/bin/env python3
"""
YouTube Playlist Audio Sync

A complete tool to sync a YouTube playlist to local audio files:
1. Extracts all video URLs from a playlist (uses cookies for private playlists)
2. Updates a CSV file with any new videos
3. Downloads audio only for new/undownloaded videos (NO cookies - they break downloads!)

IMPORTANT: Cookies are ONLY used for playlist extraction (to access private playlists).
Individual video downloads do NOT use cookies because YouTube's cookie-authenticated API
returns a degraded response with only thumbnails, not actual audio/video streams.

Setup:
    brew install yt-dlp ffmpeg
    # OR
    pip install yt-dlp

Usage:
    # Basic: sync playlist to ./downloads folder
    python yt_playlist_sync.py "https://youtube.com/playlist?list=PLxxxxx"
    
    # Custom output folder
    python yt_playlist_sync.py PLxxxxx --output ./my_music
    
    # Private playlist (cookies only used for playlist extraction)
    python yt_playlist_sync.py PLxxxxx --cookies-from-browser chrome
    
    # Different audio format
    python yt_playlist_sync.py PLxxxxx --audio-format m4a -q 320
    
    # With macOS notifications for each download
    python yt_playlist_sync.py PLxxxxx --notify
    
    # Just update CSV without downloading
    python yt_playlist_sync.py PLxxxxx --no-download
    
    # Force re-download everything
    python yt_playlist_sync.py PLxxxxx --no-skip
"""

import sys
import os
import csv
import json
import argparse
import platform
import subprocess
import shutil
from datetime import datetime
from pathlib import Path


# =============================================================================
# CHECK DEPENDENCIES
# =============================================================================

def check_dependencies():
    """Check that yt-dlp CLI is available."""
    if not shutil.which('yt-dlp'):
        print("Error: yt-dlp is not installed.")
        print("Install it with: brew install yt-dlp")
        print("            or: pip install yt-dlp")
        sys.exit(1)


# =============================================================================
# NOTIFICATIONS (macOS)
# =============================================================================

def notify(title, message, sound="default"):
    """Send macOS notification. Silently fails on other platforms."""
    if platform.system() != "Darwin":
        return
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "🎵 YouTube Sync" subtitle "{title}" sound name "{sound}"'
        ], capture_output=True, timeout=5)
    except:
        pass  # Notifications are optional, don't fail the script


# =============================================================================
# STEP 1: Extract playlist URLs
# =============================================================================

def extract_playlist(playlist_url, cookies_from_browser=None, cookies_file=None, verbose=False):
    """
    Extract all video URLs from a YouTube playlist using yt-dlp CLI.
    
    Returns:
        Tuple of (playlist_info dict, list of video dicts)
    """
    # Normalize playlist URL
    if not playlist_url.startswith('http'):
        playlist_url = f'https://www.youtube.com/playlist?list={playlist_url}'
    
    print(f"\n📋 Extracting playlist: {playlist_url}")
    print("-" * 60)
    
    # Build yt-dlp command to extract playlist info as JSON
    cmd = [
        'yt-dlp',
        '--flat-playlist',      # Don't download, just get info
        '--dump-json',          # Output as JSON
        '--no-warnings',
        playlist_url
    ]
    
    if cookies_from_browser:
        cmd.extend(['--cookies-from-browser', cookies_from_browser])
    elif cookies_file:
        cmd.extend(['--cookies', cookies_file])
    
    if verbose:
        print(f"  Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for playlist extraction
        )
        
        if result.returncode != 0:
            print(f"Error: yt-dlp failed")
            if result.stderr:
                print(f"  {result.stderr[:200]}")
            return None, []
        
        # Parse JSON output (one JSON object per line)
        videos = []
        playlist_info = {}
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                entry = json.loads(line)
                
                # First entry might have playlist info
                if not playlist_info and entry.get('playlist_title'):
                    playlist_info = {
                        'id': entry.get('playlist_id', ''),
                        'title': entry.get('playlist_title', 'Unknown'),
                        'uploader': entry.get('playlist_uploader', 'Unknown'),
                    }
                
                video_id = entry.get('id', '')
                title = entry.get('title', 'Unknown')
                
                if video_id:
                    video_info = {
                        'video_id': video_id,
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader', entry.get('channel', '')),
                    }
                    videos.append(video_info)
                    
            except json.JSONDecodeError:
                continue
        
        # Set video count
        playlist_info['video_count'] = len(videos)
        
        if playlist_info:
            print(f"Playlist: {playlist_info.get('title', 'Unknown')}")
            print(f"Uploader: {playlist_info.get('uploader', 'Unknown')}")
            print(f"Videos: {playlist_info['video_count']}")
        
        return playlist_info, videos
        
    except subprocess.TimeoutExpired:
        print("Error: Playlist extraction timed out")
        return None, []
    except Exception as e:
        print(f"Error extracting playlist: {e}")
        return None, []


# =============================================================================
# STEP 2: Update CSV file
# =============================================================================

def load_existing_csv(csv_path):
    """Load existing video IDs from CSV file."""
    existing = {}
    
    if not os.path.exists(csv_path):
        return existing
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            video_id = row.get('video_id', '')
            if video_id:
                existing[video_id] = row
    
    return existing


def update_csv(csv_path, videos, playlist_info):
    """
    Update CSV file with new videos from playlist.
    
    Returns:
        Tuple of (new_videos list, total_count)
    """
    existing = load_existing_csv(csv_path)
    existing_ids = set(existing.keys())
    
    new_videos = []
    all_videos = []
    
    for video in videos:
        video_id = video['video_id']
        
        if video_id not in existing_ids:
            video['added_date'] = datetime.now().isoformat()
            video['downloaded'] = 'no'
            new_videos.append(video)
            all_videos.append(video)
        else:
            # Keep existing entry (preserves downloaded status, added_date)
            all_videos.append(existing[video_id])
    
    # Write updated CSV
    fieldnames = ['video_id', 'title', 'url', 'duration', 'uploader', 'added_date', 'downloaded']
    
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_videos)
    
    return new_videos, len(all_videos)


def mark_downloaded_in_csv(csv_path, video_id):
    """Mark a video as downloaded in the CSV."""
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get('video_id') == video_id:
                row['downloaded'] = 'yes'
            rows.append(row)
    
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# STEP 3: Download audio
# =============================================================================

def get_pending_downloads(csv_path, archive_path):
    """Get list of videos that haven't been downloaded yet."""
    pending = []
    
    # Load archive file (yt-dlp format: "youtube VIDEO_ID")
    archived_ids = set()
    if os.path.exists(archive_path):
        with open(archive_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    archived_ids.add(parts[1])
    
    # Load CSV and find pending
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_id = row.get('video_id', '')
                if video_id and video_id not in archived_ids:
                    pending.append(row)
    
    return pending


def download_audio(videos, output_dir, audio_format='mp3', audio_quality='192',
                  cookies_from_browser=None, cookies_file=None, verbose=False,
                  archive_path=None, csv_path=None, use_cookies_for_download=False,
                  send_notifications=False):
    """Download audio for videos not yet in archive using yt-dlp CLI."""
    
    results = {'success': [], 'failed': [], 'skipped': []}
    total = len(videos)
    
    print(f"\n🎵 Downloading audio for {total} videos...")
    print(f"Format: {audio_format.upper()} @ {audio_quality}kbps")
    print("=" * 60)
    
    if send_notifications:
        notify("Downloading", f"Starting download of {total} songs...")
    
    for idx, video in enumerate(videos, 1):
        url = video.get('url', '')
        video_id = video.get('video_id', '')
        title = video.get('title', 'Unknown')
        
        print(f"\n[{idx}/{total}] {title[:50]}...")
        
        # Build yt-dlp command line
        # NOTE: Do NOT use --cookies-from-browser here - it causes YouTube to serve
        # a degraded API that only returns thumbnails. Cookies are only needed for
        # private playlist extraction, not for downloading individual videos.
        cmd = [
            'yt-dlp',
            '-x',  # Extract audio (handles format selection automatically)
            '--audio-format', audio_format,
            '--audio-quality', audio_quality,
            '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
            '--no-playlist',
        ]
        
        if archive_path:
            cmd.extend(['--download-archive', archive_path])
        
        # Only use cookies for download if explicitly requested
        # Usually NOT needed and causes issues (degraded API response)
        if use_cookies_for_download:
            if cookies_from_browser:
                cmd.extend(['--cookies-from-browser', cookies_from_browser])
            elif cookies_file:
                cmd.extend(['--cookies', cookies_file])
        
        cmd.append(url)
        
        # Show command in verbose mode
        if verbose:
            print(f"  Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per video
            )
            
            if result.returncode == 0:
                results['success'].append(video)
                print(f"  ✓ Downloaded: {title[:50]}")
                if send_notifications:
                    notify(f"Downloaded ({idx}/{total})", title[:50], "Pop")
                if csv_path:
                    mark_downloaded_in_csv(csv_path, video_id)
            else:
                # Check if it was skipped (already in archive)
                if 'has already been recorded in the archive' in result.stderr:
                    results['skipped'].append(video)
                    print(f"  ⊘ Skipped (already downloaded)")
                else:
                    results['failed'].append(video)
                    if send_notifications:
                        notify(f"Failed ({idx}/{total})", title[:40], "Basso")
                    error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else 'Unknown error'
                    print(f"  ✗ Failed: {error_msg[:70]}")
                    if verbose:
                        print(f"    STDOUT: {result.stdout}")
                        print(f"    STDERR: {result.stderr}")
                        
        except subprocess.TimeoutExpired:
            results['failed'].append(video)
            print(f"  ✗ Failed: Timeout after 5 minutes")
        except Exception as e:
            results['failed'].append(video)
            print(f"  ✗ Error: {str(e)[:50]}")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Sync a YouTube playlist to local audio files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "https://youtube.com/playlist?list=PLxxxxx"
  %(prog)s PLxxxxx --output ./music
  %(prog)s PLxxxxx --audio-format m4a -q 320
  %(prog)s PLxxxxx --cookies-from-browser chrome
  %(prog)s PLxxxxx --no-download              # Just update CSV
  %(prog)s PLxxxxx --no-skip                  # Re-download all

Workflow:
  1. Extracts all video URLs from the playlist
  2. Updates a CSV file (adds new videos, preserves existing)
  3. Downloads audio only for new/undownloaded videos
  
Files created in output directory:
  - playlist_videos.csv     (master list of all videos)
  - .download_archive.txt   (tracks downloaded video IDs)
  - *.mp3 / *.m4a / etc     (audio files)
        '''
    )
    
    parser.add_argument('playlist', nargs='?', help='Playlist URL or ID')
    parser.add_argument('--output', '-o', default='./downloads',
                        help='Output directory (default: ./downloads)')
    parser.add_argument('--audio-format', '-f', default='mp3',
                        choices=['mp3', 'm4a', 'aac', 'flac', 'opus', 'wav'],
                        help='Audio format (default: mp3)')
    parser.add_argument('--audio-quality', '-q', default='192',
                        help='Audio quality in kbps (default: 192)')
    parser.add_argument('--cookies-from-browser', '-b', metavar='BROWSER',
                        help='Browser to extract cookies from (chrome, firefox, edge, etc.)')
    parser.add_argument('--cookies', '-c', metavar='FILE',
                        help='Path to cookies.txt file')
    parser.add_argument('--no-download', action='store_true',
                        help='Only update CSV, do not download')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-download all videos (ignore archive)')
    parser.add_argument('--download-all', action='store_true',
                        help='Download all videos in CSV, not just new ones')
    parser.add_argument('--use-cookies-for-download', action='store_true',
                        help='Also use cookies when downloading (usually not needed, may cause issues)')
    parser.add_argument('--notify', '-n', action='store_true',
                        help='Show macOS notifications for each download')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed yt-dlp output')
    
    args = parser.parse_args()
    
    # Check yt-dlp is available
    check_dependencies()
    
    # Get playlist URL
    if args.playlist:
        playlist_url = args.playlist
    else:
        print("\n🎵 YouTube Playlist Audio Sync")
        print("=" * 40)
        playlist_url = input("Enter Playlist URL or ID: ").strip()
    
    if not playlist_url:
        print("Error: Playlist URL or ID is required")
        sys.exit(1)
    
    # Clean up playlist ID if full URL was provided
    playlist_id = playlist_url
    if 'list=' in playlist_url:
        playlist_id = playlist_url.split('list=')[1].split('&')[0]
    
    # Setup paths
    output_dir = args.output
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    csv_path = os.path.join(output_dir, 'playlist_videos.csv')
    archive_path = os.path.join(output_dir, '.download_archive.txt')
    
    # Clear archive if --no-skip
    if args.no_skip and os.path.exists(archive_path):
        os.remove(archive_path)
        print("🗑️  Cleared download archive (will re-download all)")
    
    # ==========================================================================
    # STEP 1: Extract playlist
    # ==========================================================================
    if args.notify:
        notify("Starting", "Extracting playlist...")
    
    playlist_info, videos = extract_playlist(
        playlist_url,
        cookies_from_browser=args.cookies_from_browser,
        cookies_file=args.cookies,
        verbose=args.verbose
    )
    
    if not videos:
        print("\n❌ No videos found in playlist.")
        if args.notify:
            notify("Error", "No videos found in playlist", "Basso")
        sys.exit(1)
    
    print(f"\n✓ Found {len(videos)} videos in playlist")
    if args.notify:
        notify("Playlist loaded", f"Found {len(videos)} videos")
    
    # ==========================================================================
    # STEP 2: Update CSV
    # ==========================================================================
    print(f"\n📝 Updating CSV: {csv_path}")
    
    new_videos, total_count = update_csv(csv_path, videos, playlist_info)
    
    print(f"  Total videos in CSV: {total_count}")
    print(f"  New videos added: {len(new_videos)}")
    
    if new_videos:
        print("\n  New videos:")
        for v in new_videos[:5]:
            print(f"    + {v['title'][:50]}")
        if len(new_videos) > 5:
            print(f"    ... and {len(new_videos) - 5} more")
    
    # ==========================================================================
    # STEP 3: Download audio
    # ==========================================================================
    if args.no_download:
        print("\n⏭️  Skipping download (--no-download)")
    else:
        # Determine what to download
        if args.download_all:
            to_download = [{'video_id': v['video_id'], 'title': v['title'], 
                          'url': v['url']} for v in videos]
            print(f"\n📥 Downloading all {len(to_download)} videos...")
        else:
            to_download = get_pending_downloads(csv_path, archive_path)
            if not to_download:
                print("\n✓ All videos already downloaded!")
            else:
                print(f"\n📥 {len(to_download)} videos pending download...")
        
        if to_download:
            results = download_audio(
                to_download,
                output_dir=output_dir,
                audio_format=args.audio_format,
                audio_quality=args.audio_quality,
                cookies_from_browser=args.cookies_from_browser,
                cookies_file=args.cookies,
                verbose=args.verbose,
                archive_path=archive_path,
                csv_path=csv_path,
                use_cookies_for_download=args.use_cookies_for_download,
                send_notifications=args.notify
            )
            
            print("\n" + "=" * 60)
            print("📊 SYNC COMPLETE")
            print("=" * 60)
            print(f"  ✓ Downloaded: {len(results['success'])}")
            print(f"  ✗ Failed: {len(results['failed'])}")
            
            # Final summary notification
            if args.notify:
                if results['success']:
                    notify("Complete ✓", f"Downloaded {len(results['success'])} songs", "Glass")
                elif results['failed']:
                    notify("Complete with errors", f"{len(results['failed'])} failed", "Basso")
        else:
            if args.notify:
                notify("Up to date ✓", "No new songs to download", "Pop")
    
    # ==========================================================================
    # Summary
    # ==========================================================================
    print(f"\n📁 Output directory: {os.path.abspath(output_dir)}")
    print(f"📋 Video list: {csv_path}")
    
    # Count audio files
    audio_extensions = {'.mp3', '.m4a', '.aac', '.flac', '.opus', '.wav'}
    audio_files = [f for f in os.listdir(output_dir) 
                   if os.path.splitext(f)[1].lower() in audio_extensions]
    print(f"🎵 Audio files: {len(audio_files)}")


if __name__ == '__main__':
    main()
