#!/bin/bash

# 🎤 Autotune Karaoke Run Script
# Easy execution with song selection

echo "🎵 Autotune Karaoke System"
echo "=========================="

# Check if executable exists
if [ ! -x "autotune-karaoke" ]; then
    echo "❌ Executable not found! Building first..."
    if [ -f "build.sh" ]; then
        chmod +x build.sh
        ./build.sh
    else
        echo "❌ Build script not found! Please build manually:"
        echo "   make all"
        echo "   or"
        echo "   g++ -std=c++17 -Wall -Wextra -O2 -I. karaoke.cpp simple_noise_suppression.cpp -o autotune-karaoke -lportaudio -lsndfile -laubio -lSDL2"
        exit 1
    fi
fi

# Check if executable was built successfully
if [ ! -x "autotune-karaoke" ]; then
    echo "❌ Build failed! Please check for errors above."
    exit 1
fi

# Show available songs
echo "🎼 Available songs:"
echo "   1. blinding_lights (The Weeknd - Blinding Lights)"
echo "   2. custom_song.txt (Custom melody file from melodies/ directory)"
echo "   3. Exit"

# Get user choice
read -p "🎤 Choose a song (1-3): " choice

case $choice in
    1)
        echo "🎵 Loading: The Weeknd - Blinding Lights"
        ./autotune-karaoke blinding_lights
        ;;
    2)
        echo "📁 Available melody files in melodies/ directory:"
        ls -1 melodies/*.txt 2>/dev/null | sed 's|melodies/||' | nl || echo "   No .txt files found"
        echo ""
        read -p "📁 Enter melody file name (from melodies/): " melody_file
        if [ -f "melodies/$melody_file" ]; then
            echo "🎵 Loading custom song: melodies/$melody_file"
            ./autotune-karaoke "melodies/$melody_file"
        else
            echo "❌ File not found: melodies/$melody_file"
            echo "💡 Available files:"
            ls -1 melodies/*.txt 2>/dev/null | sed 's|melodies/|   /|' || echo "   No .txt files found"
            exit 1
        fi
        ;;
    3)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac
