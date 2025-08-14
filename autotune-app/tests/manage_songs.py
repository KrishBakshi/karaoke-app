#!/usr/bin/env python3
# manage_songs.py
# Song management system for the scalable karaoke

import os
import shutil
import subprocess
import sys

def create_song_structure():
    """Create the song directory structure"""
    songs_dir = "songs"
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
        print(f"📁 Created songs directory: {songs_dir}")
    
    # Create subdirectories for each song
    song_dirs = {
        "blinding_lights": {
            "melody": "blinding_lights_melody_map_continuous.txt",
            "instrumental": "blinding_lights_instrumental.wav",
            "description": "The Weeknd - Blinding Lights"
        }
    }
    
    for song_name, song_info in song_dirs.items():
        song_path = os.path.join(songs_dir, song_name)
        if not os.path.exists(song_path):
            os.makedirs(song_path)
            print(f"📁 Created song directory: {song_path}")
        
        # Copy files if they exist
        if os.path.exists(song_info["melody"]):
            dest_melody = os.path.join(song_path, "melody.txt")
            shutil.copy2(song_info["melody"], dest_melody)
            print(f"📋 Copied melody: {dest_melody}")
        
        if os.path.exists(song_info["instrumental"]):
            dest_instrumental = os.path.join(song_path, "instrumental.wav")
            shutil.copy2(song_info["instrumental"], dest_instrumental)
            print(f"🎵 Copied instrumental: {dest_instrumental}")

def list_available_songs():
    """List all available songs"""
    songs_dir = "songs"
    if not os.path.exists(songs_dir):
        print("❌ No songs directory found. Run 'python3 manage_songs.py setup' first.")
        return
    
    print("🎵 Available Songs:")
    print("=" * 50)
    
    for song_dir in sorted(os.listdir(songs_dir)):
        song_path = os.path.join(songs_dir, song_dir)
        if os.path.isdir(song_path):
            melody_file = os.path.join(song_path, "melody.txt")
            instrumental_file = os.path.join(song_path, "instrumental.wav")
            
            print(f"\n🎤 {song_dir.replace('_', ' ').title()}")
            
            if os.path.exists(melody_file):
                print(f"   ✅ Melody: melody.txt")
            else:
                print(f"   ❌ Melody: missing")
            
            if os.path.exists(instrumental_file):
                print(f"   ✅ Instrumental: instrumental.wav")
            else:
                print(f"   ❌ Instrumental: missing")
            
            # Check if ready to use
            if os.path.exists(melody_file) and os.path.exists(instrumental_file):
                print(f"   🚀 Status: Ready to use")
            else:
                print(f"   ⚠️  Status: Incomplete")

def add_new_song(song_name, melody_file, instrumental_file):
    """Add a new song to the system"""
    songs_dir = "songs"
    song_path = os.path.join(songs_dir, song_name)
    
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
    
    if not os.path.exists(song_path):
        os.makedirs(song_path)
    
    # Copy melody file
    if os.path.exists(melody_file):
        dest_melody = os.path.join(song_path, "melody.txt")
        shutil.copy2(melody_file, dest_melody)
        print(f"✅ Added melody: {dest_melody}")
    else:
        print(f"❌ Melody file not found: {melody_file}")
        return False
    
    # Copy instrumental file
    if os.path.exists(instrumental_file):
        dest_instrumental = os.path.join(song_path, "instrumental.wav")
        shutil.copy2(instrumental_file, dest_instrumental)
        print(f"✅ Added instrumental: {dest_instrumental}")
    else:
        print(f"❌ Instrumental file not found: {instrumental_file}")
        return False
    
    print(f"🎉 Successfully added song: {song_name}")
    return True

def show_usage():
    """Show how to use the karaoke system"""
    print("🎵 Karaoke System Usage:")
    print("=" * 50)
    print("\n1. Setup songs:")
    print("   python3 manage_songs.py setup")
    print("\n2. List available songs:")
    print("   python3 manage_songs.py list")
    print("\n3. Add new song:")
    print("   python3 manage_songs.py add <song_name> <melody.txt> <instrumental.wav>")
    print("\n4. Convert numpy melody to text:")
    print("   python3 convert_melody_to_txt.py song.npz")
    print("\n5. Run karaoke with song:")
    print("   ./karaoke blinding_lights")
    print("   ./karaoke songs/my_song/melody.txt")
    print("\n💡 Example workflow:")
    print("   1. Extract melody: python3 extract_melody_continuous.py")
    print("   2. Convert to text: python3 convert_melody_to_txt.py song.npz")
    print("   3. Add to system: python3 manage_songs.py add my_song melody.txt instrumental.wav")
    print("   4. Run karaoke: ./karaoke my_song")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_usage()
    elif sys.argv[1] == "setup":
        create_song_structure()
    elif sys.argv[1] == "list":
        list_available_songs()
    elif sys.argv[1] == "add" and len(sys.argv) == 5:
        song_name = sys.argv[2]
        melody_file = sys.argv[3]
        instrumental_file = sys.argv[4]
        add_new_song(song_name, melody_file, instrumental_file)
    else:
        show_usage()
