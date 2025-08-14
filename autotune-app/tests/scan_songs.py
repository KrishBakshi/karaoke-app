#!/usr/bin/env python3
"""
Script to scan the songs directory and analyze the structure
to help fix the C++ input path logic.
"""

import os
import re
from pathlib import Path

def scan_songs_directory():
    """Scan the songs directory and analyze the structure."""
    songs_dir = Path("songs")
    
    if not songs_dir.exists():
        print("❌ Songs directory not found!")
        return
    
    print("🎵 Scanning songs directory...")
    print("=" * 60)
    
    songs_info = []
    
    for song_dir in songs_dir.iterdir():
        if not song_dir.is_dir():
            continue
            
        print(f"\n📁 Song directory: {song_dir.name}")
        
        # Extract song name (remove timestamp and other suffixes)
        song_name = extract_song_name(song_dir.name)
        print(f"   🎼 Extracted name: {song_name}")
        
        # Look for melody files
        melody_files = list(song_dir.glob("*melody.*"))
        melody_txt = None
        melody_npz = None
        
        for melody_file in melody_files:
            if melody_file.suffix == ".txt":
                melody_txt = melody_file
            elif melody_file.suffix == ".npz":
                melody_npz = melody_file
        
        print(f"   📝 Melody .txt: {melody_txt.name if melody_txt else 'NOT FOUND'}")
        print(f"   📦 Melody .npz: {melody_npz.name if melody_npz else 'NOT FOUND'}")
        
        # Look for instrumental files
        separated_dir = song_dir / f"{song_name}_separated"
        if not separated_dir.exists():
            # Try alternative naming patterns
            for subdir in song_dir.iterdir():
                if subdir.is_dir() and "separated" in subdir.name.lower():
                    separated_dir = subdir
                    break
        
        instrumental_files = []
        if separated_dir.exists():
            print(f"   🎵 Separated dir: {separated_dir.name}")
            
            # Look for instrumental files
            for inst_file in separated_dir.iterdir():
                if inst_file.is_file() and "instrumental" in inst_file.name.lower():
                    instrumental_files.append(inst_file)
                    print(f"      🎸 Instrumental: {inst_file.name}")
        else:
            print(f"   ❌ Separated directory not found!")
        
        # Look for lyrics
        lyrics_files = list(song_dir.glob("*lyrics.txt"))
        lyrics_file = lyrics_files[0] if lyrics_files else None
        print(f"   📜 Lyrics: {lyrics_file.name if lyrics_file else 'NOT FOUND'}")
        
        songs_info.append({
            'directory': song_dir.name,
            'song_name': song_name,
            'melody_txt': melody_txt,
            'melody_npz': melody_npz,
            'instrumental_files': instrumental_files,
            'lyrics_file': lyrics_file
        })
        
        print("-" * 40)
    
    return songs_info

def extract_song_name(directory_name):
    """Extract a clean song name from directory name."""
    # Remove timestamp patterns like _f66263_20250811_202548
    # Remove "Official_Video" and similar suffixes
    # Keep the main artist and song name
    
    # Pattern to match timestamps and suffixes
    timestamp_pattern = r'_[a-f0-9]+_\d{8}_\d{6}$'
    official_pattern = r'_Official_Video$'
    
    # Remove patterns
    clean_name = re.sub(timestamp_pattern, '', directory_name)
    clean_name = re.sub(official_pattern, '', clean_name)
    
    return clean_name

def generate_cpp_suggestions(songs_info):
    """Generate suggestions for fixing the C++ code."""
    print("\n🔧 C++ Code Fix Suggestions:")
    print("=" * 60)
    
    print("\n1. Update the song name extraction logic:")
    print("   - Current: expects simple song names")
    print("   - Needed: handle complex directory names with timestamps")
    
    print("\n2. Fix instrumental file path construction:")
    print("   - Current: songs/<song_name>/<song_name>_seperated/...")
    print("   - Issues: typo '_seperated', wrong filename pattern")
    print("   - Actual: songs/<complex_dir>/<song_name>_separated/...")
    
    print("\n3. Update melody file loading:")
    print("   - Support both .txt and .npz files")
    print("   - Handle the actual file naming patterns")
    
    print("\n4. Suggested command line usage:")
    for song_info in songs_info:
        print(f"   ./karaoke {song_info['song_name']}")
        print(f"   ./karaoke {song_info['directory']}")
    
    print("\n5. File path patterns to support:")
    for song_info in songs_info:
        if song_info['melody_txt']:
            print(f"   Melody: {song_info['melody_txt']}")
        if song_info['instrumental_files']:
            print(f"   Instrumental: {song_info['instrumental_files'][0]}")

if __name__ == "__main__":
    songs_info = scan_songs_directory()
    if songs_info:
        generate_cpp_suggestions(songs_info)
        
        print(f"\n✅ Found {len(songs_info)} songs:")
        for song_info in songs_info:
            print(f"   - {song_info['song_name']} (from {song_info['directory']})")
    else:
        print("❌ No songs found!")
