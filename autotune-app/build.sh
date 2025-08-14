#!/bin/bash

# 🎤 Autotune Karaoke Build Script
# Easy compilation and testing

set -e  # Exit on any error

echo "🎵 Building Autotune Karaoke Application..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "karaoke.cpp" ]; then
    echo "❌ Error: karaoke.cpp not found!"
    echo "   Please run this script from the autotune-app directory"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."

# Check for g++
if ! command -v g++ &> /dev/null; then
    echo "❌ g++ not found! Installing build tools..."
    sudo apt-get update
    sudo apt-get install -y build-essential
fi

# Check for required libraries
echo "📚 Checking audio libraries..."

# PortAudio
if ! pkg-config --exists portaudio-2.0; then
    echo "⚠️  PortAudio not found. Installing..."
    sudo apt-get install -y libportaudio2-dev
fi

# libsndfile
if ! pkg-config --exists sndfile; then
    echo "⚠️  libsndfile not found. Installing..."
    sudo apt-get install -y libsndfile1-dev
fi

# Aubio
if ! pkg-config --exists aubio; then
    echo "⚠️  Aubio not found. Installing..."
    sudo apt-get install -y libaubio-dev
fi

# SDL2
if ! pkg-config --exists sdl2; then
    echo "⚠️  SDL2 not found. Installing..."
    sudo apt-get install -y libsdl2-dev
fi

echo "✅ All dependencies found!"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -f *.o autotune-karaoke

# Build the application
echo "🔨 Compiling..."
g++ -std=c++17 -Wall -Wextra -O2 -I. \
    karaoke.cpp simple_noise_suppression.cpp \
    -o autotune-karaoke \
    -lportaudio -lsndfile -laubio -lSDL2

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "🎵 Executable: autotune-karaoke"
    
    # Check if we can run it
    if [ -x "autotune-karaoke" ]; then
        echo "🚀 Ready to run!"
        echo ""
        echo "📁 Directory Structure:"
        echo "   🎵 Root: Application files (karaoke.cpp, build scripts)"
        echo "   🎼 Melodies: Song data and melody maps"
        echo "   🧪 Tests: Python utilities and test scripts"
        echo ""
        echo "Usage examples:"
        echo "  ./autotune-karaoke blinding_lights"
        echo "  ./autotune-karaoke melodies/my_song.txt"
        echo ""
        echo "🎤 Happy singing!"
    else
        echo "❌ Executable not found after build!"
    fi
else
    echo "❌ Build failed!"
    exit 1
fi
