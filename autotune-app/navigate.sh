#!/bin/bash

# 🧭 Autotune App Navigation Helper
# Shows the directory structure and helps navigate

echo "🧭 Autotune App Directory Navigator"
echo "==================================="
echo ""

# Show current directory structure
echo "📁 Current Directory Structure:"
echo "   🎵 Root (Current): Application files and build scripts"
echo "   🎼 melodies/: Song data and melody maps"
echo "   🧪 tests/: Python utilities and test scripts"
echo ""

# Show what's in each directory
echo "🎵 Root Directory Contents:"
ls -1 | grep -E '\.(cpp|h|sh|txt|md|cmake|makefile)' | sed 's/^/   /' || echo "   No core files found"
echo ""

echo "🎼 Melodies Directory Contents:"
if [ -d "melodies" ]; then
    ls -1 melodies/ | sed 's/^/   /' || echo "   No melody files found"
else
    echo "   melodies/ directory not found"
fi
echo ""

echo "🧪 Tests Directory Contents:"
if [ -d "tests" ]; then
    ls -1 tests/ | head -10 | sed 's/^/   /'
    if [ $(ls tests/ | wc -l) -gt 10 ]; then
        echo "   ... and $(($(ls tests/ | wc -l) - 10)) more files"
    fi
else
    echo "   tests/ directory not found"
fi
echo ""

# Navigation help
echo "🧭 Navigation Commands:"
echo "   cd melodies/          # Go to melodies directory"
echo "   cd tests/             # Go to tests directory"
echo "   cd ..                 # Go back to root"
echo "   ./build.sh            # Build the application"
echo "   ./run.sh              # Run karaoke"
echo "   make help             # Show make options"
echo ""

# Quick actions
echo "🚀 Quick Actions:"
echo "   1. Build application"
echo "   2. Run karaoke"
echo "   3. Go to melodies directory"
echo "   4. Go to tests directory"
echo "   5. Exit"
echo ""

read -p "🎯 Choose action (1-5): " choice

case $choice in
    1)
        echo "🔨 Building application..."
        ./build.sh
        ;;
    2)
        echo "🎵 Running karaoke..."
        ./run.sh
        ;;
    3)
        echo "🎼 Going to melodies directory..."
        cd melodies
        echo "📁 Now in melodies/ directory"
        echo "💡 Use 'cd ..' to go back to root"
        ;;
    4)
        echo "🧪 Going to tests directory..."
        cd tests
        echo "📁 Now in tests/ directory"
        echo "💡 Use 'cd ..' to go back to root"
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac
