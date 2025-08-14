# 🎵 Song Usage Guide for C++ Karaoke

This guide explains how to use the song finder scripts to work with the existing C++ karaoke program without modifying the core code.

## 🚀 Quick Start

### 1. List Available Songs
```bash
python3 song_finder.py --list
```

### 2. Find Song Files
```bash
python3 song_finder.py Taylor_Swift_-_Love_Story
python3 song_finder.py The_Weeknd_-_Blinding_Lights
```

### 3. Run Karaoke (Recommended)
```bash
python3 run_karaoke.py Taylor_Swift_-_Love_Story
python3 run_karaoke.py The_Weeknd_-_Blinding_Lights
```

## 📁 Current Song Structure

The songs directory contains:
- **Taylor_Swift_-_Love_Story_f66263_20250811_202548/**
  - `Taylor_Swift_-_Love_Story_melody.txt` - Melody data
  - `Taylor_Swift_-_Love_Story_separated/` - Instrumental audio
- **The_Weeknd_-_Blinding_Lights_Official_Video_b32060_20250811_201649/**
  - `The_Weeknd_-_Blinding_Lights_O_melody.txt` - Melody data
  - `The_Weeknd_-_Blinding_Lights_O_separated/` - Instrumental audio

## 🔧 How It Works

1. **song_finder.py** - Scans the songs directory and finds the correct file paths
2. **run_karaoke.py** - Wrapper that uses song_finder.py and runs the C++ program
3. **karaoke.cpp** - Remains unchanged, handles the audio processing

## 💡 Benefits of This Approach

- ✅ **No changes to core C++ code** - Keeps the heavy audio processing logic clean
- ✅ **Automatic file detection** - Handles complex directory names with timestamps
- ✅ **Flexible input** - Accepts both song names and directory names
- ✅ **Easy to maintain** - Python scripts are lightweight and easy to modify
- ✅ **Backward compatible** - Existing C++ program works as-is

## 🎯 Usage Examples

### Simple song name (recommended):
```bash
python3 run_karaoke.py Taylor_Swift_-_Love_Story
```

### Full directory name (also works):
```bash
python3 run_karaoke.py Taylor_Swift_-_Love_Story_f66263_20250811_202548
```

### Check what files will be used:
```bash
python3 song_finder.py Taylor_Swift_-_Love_Story
```

## 🚨 Troubleshooting

- **"Karaoke executable not found"** - Run `make clean && make` to compile
- **"Song not found"** - Use `python3 song_finder.py --list` to see available songs
- **File path issues** - The scripts automatically handle the complex directory structure

## 🔄 Adding New Songs

1. Create a new directory in `songs/`
2. Add melody files (`.txt` or `.npz`)
3. Add separated audio in a `*_separated/` subdirectory
4. The scripts will automatically detect the new song

The song finder scripts will automatically handle new songs without any code changes!
