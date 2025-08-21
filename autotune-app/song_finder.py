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
    print(f"🔍 DEBUG: Starting song search for: '{song_input}'")
    songs_dir = Path("songs")
    
    if not songs_dir.exists():
        print(f"❌ DEBUG: Songs directory not found at: {songs_dir.absolute()}")
        return None, None, "❌ Songs directory not found!"
    
    print(f"✅ DEBUG: Songs directory found at: {songs_dir.absolute()}")
    
    # Try to find the song directory
    song_dir = None
    song_name = None
    
    # First, try exact directory match
    potential_dir = songs_dir / song_input
    print(f"🔍 DEBUG: Checking exact directory match: {potential_dir}")
    if potential_dir.exists() and potential_dir.is_dir():
        song_dir = potential_dir
        song_name = extract_song_name(song_input)
        print(f"✅ DEBUG: Exact directory match found: {song_dir}")
    else:
        print(f"❌ DEBUG: Exact directory match failed, trying pattern matching...")
        # Try to find by song name (removing timestamps/suffixes)
        clean_input = extract_song_name(song_input)
        print(f"🔍 DEBUG: Clean song name: '{clean_input}'")
        print(f"🔍 DEBUG: Available directories in songs folder:")
        for subdir in songs_dir.iterdir():
            if subdir.is_dir():
                clean_subdir_name = extract_song_name(subdir.name)
                print(f"   📁 {subdir.name} -> '{clean_subdir_name}'")
                if clean_subdir_name == clean_input:
                    song_dir = subdir
                    song_name = clean_input
                    print(f"✅ DEBUG: Pattern match found: {song_dir}")
                    break
    
    if not song_dir:
        print(f"❌ DEBUG: No song directory found for '{song_input}'")
        return None, None, f"❌ Song '{song_input}' not found!"
    
    print(f"🎯 DEBUG: Working with song directory: {song_dir}")
    print(f"🎯 DEBUG: Song name extracted: {song_name}")
    
    # Find melody file
    melody_file = None
    melody_files = list(song_dir.glob("*melody.*"))
    print(f"🔍 DEBUG: Found {len(melody_files)} melody files:")
    for mf in melody_files:
        print(f"   📝 {mf.name} (suffix: {mf.suffix})")
    
    for mf in melody_files:
        if mf.suffix == ".txt":
            melody_file = mf
            print(f"✅ DEBUG: Selected melody file: {mf.name}")
            break
        elif mf.suffix == ".npz" and not melody_file:
            melody_file = mf  # Fallback to .npz if no .txt found
            print(f"⚠️ DEBUG: Fallback melody file: {mf.name}")
    
    if not melody_file:
        print(f"❌ DEBUG: No melody file found in {song_dir.name}")
        return None, None, f"❌ No melody file found in {song_dir.name}"
    
    print(f"✅ DEBUG: Melody file confirmed: {melody_file}")
    
    # Find instrumental file
    instrumental_file = None
    separated_dir = song_dir / f"{song_name}_separated"
    print(f"🔍 DEBUG: Looking for separated directory: {separated_dir}")
    
    if not separated_dir.exists():
        print(f"❌ DEBUG: Primary separated directory not found, searching alternatives...")
        # Try alternative naming patterns
        print(f"🔍 DEBUG: Checking all subdirectories in {song_dir}:")
        for subdir in song_dir.iterdir():
            if subdir.is_dir():
                print(f"   📁 {subdir.name}")
                if "separated" in subdir.name.lower():
                    separated_dir = subdir
                    print(f"✅ DEBUG: Found alternative separated directory: {subdir}")
                    break
    
    if separated_dir.exists():
        print(f"✅ DEBUG: Using separated directory: {separated_dir}")
        # Look for instrumental files
        print(f"🔍 DEBUG: Searching for instrumental files in {separated_dir}:")
        all_files = list(separated_dir.iterdir())
        print(f"   📁 Total files in separated directory: {len(all_files)}")
        
        for inst_file in all_files:
            print(f"   📄 {inst_file.name}")
            if inst_file.is_file() and "instrumental model_bs_roformer_ep_317_sdr_1" in inst_file.name.lower():
                instrumental_file = inst_file
                print(f"✅ DEBUG: Found instrumental file: {inst_file.name}")
                break
            elif inst_file.is_file() and "instrumental" in inst_file.name.lower():
                print(f"⚠️ DEBUG: [Fallback] Found file with 'instrumental' in name: {inst_file.name}")
                if not instrumental_file:  # Use as fallback
                    instrumental_file = inst_file
                    print(f"⚠️ DEBUG: Using as fallback instrumental file: {inst_file.name}")
    else:
        print(f"❌ DEBUG: No separated directory found")
    
    if not instrumental_file:
        print(f"❌ DEBUG: No instrumental file found in {song_dir.name}")
        print(f"🔍 DEBUG: Directory structure of {song_dir}:")
        for item in song_dir.rglob("*"):
            if item.is_file():
                print(f"   📄 {item.relative_to(song_dir)}")
        return None, None, f"❌ No instrumental file found in {song_dir.name}"
    
    print(f"✅ DEBUG: Instrumental file confirmed: {instrumental_file}")
    
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
    print(f"🔍 DEBUG: Songs directory: {songs_dir.absolute()}")
    
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
                for mf in melody_files:
                    print(f"      📝 {mf.name}")
            else:
                print(f"   ❌ No melody files")
                
            if separated_dirs:
                print(f"   ✅ Separated audio: {len(separated_dirs)}")
                for sd in separated_dirs:
                    print(f"      📁 {sd.name}")
                    # Show files in separated directory
                    try:
                        files_in_sep = list(sd.iterdir())
                        print(f"         📄 Files: {len(files_in_sep)}")
                        for f in files_in_sep[:5]:  # Show first 5 files
                            print(f"            {f.name}")
                        if len(files_in_sep) > 5:
                            print(f"            ... and {len(files_in_sep) - 5} more")
                    except PermissionError:
                        print(f"         ❌ Cannot access directory contents")
            else:
                print(f"   ❌ No separated audio")
            
            # Show all files in the song directory for debugging
            print(f"   🔍 DEBUG: All files in directory:")
            try:
                all_files = list(song_dir.rglob("*"))
                for f in all_files[:10]:  # Show first 10 files
                    rel_path = f.relative_to(song_dir)
                    if f.is_file():
                        print(f"      📄 {rel_path}")
                    elif f.is_dir():
                        print(f"      📁 {rel_path}/")
                if len(all_files) > 10:
                    print(f"      ... and {len(all_files) - 10} more items")
            except PermissionError:
                print(f"      ❌ Cannot access directory contents")
            
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

def diagnose_song_directory(song_name):
    """Diagnose the structure of a specific song directory."""
    print(f"🔍 DEBUG: Diagnosing song directory: {song_name}")
    print("=" * 60)
    
    songs_dir = Path("songs")
    if not songs_dir.exists():
        print("❌ Songs directory not found!")
        return
    
    # Find the song directory
    song_dir = None
    for subdir in songs_dir.iterdir():
        if subdir.is_dir():
            clean_subdir_name = extract_song_name(subdir.name)
            if clean_subdir_name == song_name or subdir.name == song_name:
                song_dir = subdir
                break
    
    if not song_dir:
        print(f"❌ Song directory not found for: {song_name}")
        print("Available directories:")
        for subdir in songs_dir.iterdir():
            if subdir.is_dir():
                clean_name = extract_song_name(subdir.name)
                print(f"   📁 {subdir.name} -> '{clean_name}'")
        return
    
    print(f"✅ Found song directory: {song_dir}")
    print(f"📁 Full path: {song_dir.absolute()}")
    print()
    
    # Show directory structure
    print("📂 Directory Structure:")
    print("-" * 40)
    
    def print_tree(path, prefix="", max_depth=3, current_depth=0):
        if current_depth > max_depth:
            print(f"{prefix}... (max depth reached)")
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                if item.is_file():
                    print(f"{prefix}{current_prefix}📄 {item.name}")
                elif item.is_dir():
                    print(f"{prefix}{current_prefix}📁 {item.name}/")
                    if current_depth < max_depth:
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        print_tree(item, new_prefix, max_depth, current_depth + 1)
        except PermissionError:
            print(f"{prefix}❌ Permission denied")
    
    print_tree(song_dir)
    print()
    
    # Check for melody files
    print("🎵 Melody Files:")
    print("-" * 40)
    melody_files = list(song_dir.glob("*melody.*"))
    if melody_files:
        for mf in melody_files:
            print(f"✅ {mf.name} ({mf.suffix})")
    else:
        print("❌ No melody files found")
        # Show all files that might be melody files
        all_files = [f for f in song_dir.iterdir() if f.is_file()]
        melody_candidates = [f for f in all_files if "melody" in f.name.lower()]
        if melody_candidates:
            print("🔍 Potential melody files:")
            for f in melody_candidates:
                print(f"   📝 {f.name}")
    
    print()
    
    # Check for separated audio
    print("🎸 Separated Audio:")
    print("-" * 40)
    separated_dirs = [d for d in song_dir.iterdir() if d.is_dir() and "separated" in d.name.lower()]
    
    if separated_dirs:
        for sd in separated_dirs:
            print(f"📁 {sd.name}/")
            try:
                files_in_sep = list(sd.iterdir())
                instrumental_files = [f for f in files_in_sep if f.is_file() and "instrumental" in f.name.lower()]
                
                if instrumental_files:
                    print(f"   ✅ Found {len(instrumental_files)} instrumental files:")
                    for f in instrumental_files:
                        print(f"      🎸 {f.name}")
                else:
                    print(f"   ❌ No instrumental files found")
                    print(f"   📄 All files in {sd.name}:")
                    for f in files_in_sep[:10]:
                        print(f"      {f.name}")
                    if len(files_in_sep) > 10:
                        print(f"      ... and {len(files_in_sep) - 10} more")
            except PermissionError:
                print(f"   ❌ Cannot access directory contents")
    else:
        print("❌ No separated audio directories found")
        # Check for alternative patterns
        print("🔍 Checking for alternative audio directories:")
        for subdir in song_dir.iterdir():
            if subdir.is_dir():
                print(f"   📁 {subdir.name}/")
                try:
                    files_in_subdir = list(subdir.iterdir())
                    audio_files = [f for f in files_in_subdir if f.is_file() and f.suffix.lower() in ['.wav', '.mp3', '.flac', '.m4a']]
                    if audio_files:
                        print(f"      🎵 Found {len(audio_files)} audio files:")
                        for f in audio_files[:5]:
                            print(f"         {f.name}")
                        if len(audio_files) > 5:
                            print(f"         ... and {len(audio_files) - 5} more")
                except PermissionError:
                    print(f"      ❌ Cannot access directory contents")
    
    print()
    print("=" * 60)

def main():
    print(f"🔍 DEBUG: Script started with {len(sys.argv)} arguments: {sys.argv}")
    
    if len(sys.argv) < 2:
        print("🎵 Song Finder for C++ Karaoke")
        print("📖 Usage:")
        print("   python3 song_finder.py <song_name>")
        print("   python3 song_finder.py --list")
        print("   python3 song_finder.py --auto")
        print("   python3 song_finder.py --debug <song_name>")
        print("   python3 song_finder.py --diagnose <song_name>")
        print("\n💡 Examples:")
        print("   python3 song_finder.py --list  # Show all available songs")
        print("   python3 song_finder.py --auto  # Auto-discover and run first available song")
        print("   python3 song_finder.py <song_name>  # Find specific song")
        print("   python3 song_finder.py --debug <song_name>  # Find with detailed debugging")
        print("   python3 song_finder.py --diagnose <song_name>  # Detailed directory analysis")
        return
    
    if sys.argv[1] == "--list":
        list_available_songs()
        return
    
    if sys.argv[1] == "--auto":
        auto_discover_and_run()
        return
    
    if sys.argv[1] == "--diagnose":
        if len(sys.argv) < 3:
            print("❌ Error: --diagnose requires a song name")
            return
        song_input = sys.argv[2]
        diagnose_song_directory(song_input)
        return
    
    if sys.argv[1] == "--debug":
        if len(sys.argv) < 3:
            print("❌ Error: --debug requires a song name")
            return
        song_input = sys.argv[2]
        print(f"🐛 DEBUG MODE ENABLED for song: {song_input}")
    else:
        song_input = sys.argv[1]
    
    print(f"🎯 DEBUG: Searching for song: '{song_input}'")
    print(f"🎯 DEBUG: Current working directory: {Path.cwd()}")
    
    melody_file, instrumental_file, message = find_song_files(song_input)
    
    print(message)
    
    if melody_file and instrumental_file:
        print(f"\n🎯 File paths for C++ program:")
        print(f"   Melody: {melody_file}")
        print(f"   Instrumental: {instrumental_file}")
        print(f"\n🚀 Run with: ./karaoke {song_input}")
    else:
        print(f"\n❌ DEBUG: Song search failed. Check the debug output above for details.")
        print(f"🔍 DEBUG: You can also try:")
        print(f"   python3 song_finder.py --list")
        print(f"   python3 song_finder.py --diagnose {song_input}")

if __name__ == "__main__":
    main()
