#!/usr/bin/env python3
# convert_melody_to_txt.py
# Converts numpy melody maps to text format for the scalable karaoke system

import numpy as np
import sys
import os

def convert_melody_to_txt(npz_file, output_txt=None):
    """Convert a numpy .npz melody map to text format"""
    
    if not os.path.exists(npz_file):
        print(f"❌ File not found: {npz_file}")
        return False
    
    # Load the numpy melody map
    try:
        data = np.load(npz_file)
        times = data['times']
        freqs = data['freqs']
        print(f"✅ Loaded melody map: {len(times)} points")
    except Exception as e:
        print(f"❌ Error loading {npz_file}: {e}")
        return False
    
    # Generate output filename if not provided
    if output_txt is None:
        base_name = os.path.splitext(npz_file)[0]
        output_txt = f"{base_name}.txt"
    
    # Write to text file
    try:
        with open(output_txt, 'w') as f:
            f.write(f"# Melody Map converted from {npz_file}\n")
            f.write(f"# Format: time(s), frequency(Hz)\n")
            f.write(f"# Total points: {len(times)}\n")
            f.write(f"# Time range: {times[0]:.2f}s to {times[-1]:.2f}s\n")
            f.write(f"# Resolution: {times[1] - times[0]:.3f}s intervals\n\n")
            
            for t, freq in zip(times, freqs):
                f.write(f"{t:.3f}, {freq:.3f}\n")
        
        print(f"✅ Converted to: {output_txt}")
        print(f"📊 {len(times)} melody points written")
        print(f"⏱️  Time range: {times[0]:.2f}s to {times[-1]:.2f}s")
        print(f"🔍 Resolution: {times[1] - times[0]:.3f}s intervals")
        return True
        
    except Exception as e:
        print(f"❌ Error writing {output_txt}: {e}")
        return False

def batch_convert_directory(directory="."):
    """Convert all .npz files in a directory to .txt format"""
    print(f"🔄 Scanning directory: {directory}")
    
    npz_files = [f for f in os.listdir(directory) if f.endswith('.npz')]
    
    if not npz_files:
        print("❌ No .npz files found in directory")
        return
    
    print(f"📁 Found {len(npz_files)} .npz files:")
    for f in npz_files:
        print(f"   - {f}")
    
    print("\n🔄 Converting files...")
    success_count = 0
    
    for npz_file in npz_files:
        print(f"\n🎵 Converting: {npz_file}")
        if convert_melody_to_txt(npz_file):
            success_count += 1
    
    print(f"\n✅ Conversion complete: {success_count}/{len(npz_files)} files converted")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - convert all .npz files in current directory
        batch_convert_directory()
    elif len(sys.argv) == 2:
        # Single file conversion
        npz_file = sys.argv[1]
        convert_melody_to_txt(npz_file)
    elif len(sys.argv) == 3:
        # File conversion with custom output name
        npz_file = sys.argv[1]
        output_txt = sys.argv[2]
        convert_melody_to_txt(npz_file, output_txt)
    else:
        print("📖 Usage:")
        print("  python3 convert_melody_to_txt.py                    # Convert all .npz files")
        print("  python3 convert_melody_to_txt.py song.npz          # Convert specific file")
        print("  python3 convert_melody_to_txt.py song.npz song.txt # Convert with custom output")
        print("\n💡 Examples:")
        print("  python3 convert_melody_to_txt.py blinding_lights_melody_map_continuous.npz")
        print("  python3 convert_melody_to_txt.py my_song.npz my_song.txt")
