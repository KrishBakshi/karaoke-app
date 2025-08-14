#!/usr/bin/env python3
"""
Lightweight song finder script for the C++ karaoke program.
This script scans the songs directory and provides the correct file paths.
"""

import os
import sys
import re
from pathlib import Path

def find_song_files(song_input):
    """
    Find song files based on input (can be song name or directory name).
    Returns a tuple of (melody_file, instrumental_file, success_message)
    """
    songs_dir = Path("songs")
    
    if not songs_dir.exists():
        return None, None, "❌ Songs directory not found!"
    
    # Try to find the song directory
    song_dir = None
    song_name = None
    
    # First, try exact directory match
    potential_dir = songs_dir / song_input
    if potential_dir.exists() and potential_dir.is_dir():
        song_dir = potential_dir
        song_name = extract_song_name(song_input)
    else:
        # Try to find by song name (removing timestamps/suffixes)
        clean_input = extract_song_name(song_input)
        for subdir in songs_dir.iterdir():
            if subdir.is_dir():
                if extract_song_name(subdir.name) == clean_input:
                    song_dir = subdir
                    song_name = clean_input
                    break
    
    if not song_dir:
        return None, None, f"❌ Song '{song_input}' not found!"
    
    # Find melody file
    melody_file = None
    melody_files = list(song_dir.glob("*melody.*"))
    for mf in melody_files:
        if mf.suffix == ".txt":
            melody_file = mf
            break
        elif mf.suffix == ".npz" and not melody_file:
            melody_file = mf  # Fallback to .npz if no .txt found
    
    if not melody_file:
        return None, None, f"❌ No melody file found in {song_dir.name}"
    
    # Find instrumental file
    instrumental_file = None
    separated_dir = song_dir / f"{song_name}_separated"
    if not separated_dir.exists():
        # Try alternative naming patterns
        for subdir in song_dir.iterdir():
            if subdir.is_dir() and "separated" in subdir.name.lower():
                separated_dir = subdir
                break
    
    if separated_dir.exists():
        # Look for instrumental files
        for inst_file in separated_dir.iterdir():
            if inst_file.is_file() and "instrumental" in inst_file.name.lower():
                instrumental_file = inst_file
                break
    
    if not instrumental_file:
        return None, None, f"❌ No instrumental file found in {song_dir.name}"
    
    success_msg = f"✅ Found song: {song_name}\n"
    success_msg += f"   📝 Melody: {melody_file.name}\n"
    success_msg += f"   🎸 Instrumental: {instrumental_file.name}"
    
    return str(melody_file), str(instrumental_file), success_msg

def extract_song_name(directory_name):
    """Extract a clean song name from directory name."""
    # Remove timestamp patterns like _f66263_20250811_202548
    # Remove "Official_Video" and similar suffixes
    timestamp_pattern = r'_[a-f0-9]+_\d{8}_\d{6}$'
    official_pattern = r'_Official_Video$'
    
    clean_name = re.sub(timestamp_pattern, '', directory_name)
    clean_name = re.sub(official_pattern, '', clean_name)
    
    return clean_name

def list_available_songs():
    """List all available songs for the user."""
    songs_dir = Path("songs")
    
    if not songs_dir.exists():
        print("❌ Songs directory not found!")
        return
    
    print("🎵 Available songs:")
    print("=" * 50)
    
    for song_dir in songs_dir.iterdir():
        if song_dir.is_dir():
            song_name = extract_song_name(song_dir.name)
            print(f"🎼 {song_name}")
            print(f"   📁 Directory: {song_dir.name}")
            
            # Check if files exist
            melody_files = list(song_dir.glob("*melody.*"))
            separated_dirs = [d for d in song_dir.iterdir() if d.is_dir() and "separated" in d.name.lower()]
            
            if melody_files:
                print(f"   ✅ Melody files: {len(melody_files)}")
            else:
                print(f"   ❌ No melody files")
                
            if separated_dirs:
                print(f"   ✅ Separated audio: {len(separated_dirs)}")
            else:
                print(f"   ❌ No separated audio")
            
            print()

def auto_discover_and_run():
    """Auto-discover available songs and run the first one found."""
    songs_dir = Path("songs")
    
    if not songs_dir.exists():
        print("❌ Songs directory not found!")
        return
    
    print("🔍 Auto-discovering available songs...")
    
    available_songs = []
    
    for song_dir in songs_dir.iterdir():
        if not song_dir.is_dir():
            continue
            
        song_name = extract_song_name(song_dir.name)
        
        # Check if this song has the required files
        melody_file, instrumental_file, _ = find_song_files(song_name)
        
        if melody_file and instrumental_file:
            available_songs.append({
                'name': song_name,
                'directory': song_dir.name,
                'melody_file': melody_file,
                'instrumental_file': instrumental_file
            })
    
    if not available_songs:
        print("❌ No songs found with required files!")
        return
    
    print(f"✅ Found {len(available_songs)} available songs:")
    for i, song in enumerate(available_songs, 1):
        print(f"   {i}. {song['name']} (from {song['directory']})")
    
    # Use the first available song
    selected_song = available_songs[0]
    print(f"\n🚀 Auto-selecting first song: {selected_song['name']}")
    
    # Run the karaoke program with the exact file paths
    try:
        import subprocess
        print(f"🎵 Starting karaoke with:")
        print(f"   📝 Melody: {selected_song['melody_file']}")
        print(f"   🎸 Instrumental: {selected_song['instrumental_file']}")
        result = subprocess.run(["./autotune-karaoke", selected_song['melody_file'], selected_song['instrumental_file']], check=True)
        print("\n✅ Karaoke session completed!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Karaoke program failed with exit code: {e.returncode}")
    except FileNotFoundError:
        print("\n❌ Karaoke executable not found! Make sure to compile the C++ program first.")
        print("💡 Run: make clean && make")
    except KeyboardInterrupt:
        print("\n\n🛑 Karaoke session interrupted by user.")

def main():
    if len(sys.argv) < 2:
        print("🎵 Song Finder for C++ Karaoke")
        print("📖 Usage:")
        print("   python3 song_finder.py <song_name>")
        print("   python3 song_finder.py --list")
        print("   python3 song_finder.py --auto")
        print("\n💡 Examples:")
        print("   python3 song_finder.py --list  # Show all available songs")
        print("   python3 song_finder.py --auto  # Auto-discover and run first available song")
        print("   python3 song_finder.py <song_name>  # Find specific song")
        return
    
    if sys.argv[1] == "--list":
        list_available_songs()
        return
    
    if sys.argv[1] == "--auto":
        auto_discover_and_run()
        return
    
    song_input = sys.argv[1]
    melody_file, instrumental_file, message = find_song_files(song_input)
    
    print(message)
    
    if melody_file and instrumental_file:
        print(f"\n🎯 File paths for C++ program:")
        print(f"   Melody: {melody_file}")
        print(f"   Instrumental: {instrumental_file}")
        print(f"\n🚀 Run with: ./karaoke {song_input}")

if __name__ == "__main__":
    main()
