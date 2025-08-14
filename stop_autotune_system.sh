#!/bin/bash

# 🎤 Autotune Karaoke System Stop Script
# This script gracefully shuts down the autotune karaoke system

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🛑 Stopping Autotune Karaoke System..."
echo "======================================"

# Function to stop processes by port
stop_by_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "🛑 Stopping $service_name on port $port..."
        local pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
        for pid in $pids; do
            echo "   Killing process $pid"
            kill $pid 2>/dev/null
        done
        
        # Wait a moment and check if still running
        sleep 1
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "   Force killing remaining processes on port $port"
            local remaining_pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
            for pid in $remaining_pids; do
                kill -9 $pid 2>/dev/null
            done
        fi
        
        echo "✅ $service_name stopped"
    else
        echo "✅ $service_name not running on port $port"
    fi
}

# Function to stop processes by name
stop_by_name() {
    local process_name=$1
    local display_name=$2
    
    if pgrep -f "$process_name" >/dev/null; then
        echo "🛑 Stopping $display_name..."
        pkill -f "$process_name"
        
        # Wait a moment and check if still running
        sleep 1
        if pgrep -f "$process_name" >/dev/null; then
            echo "   Force killing remaining $display_name processes"
            pkill -9 -f "$process_name"
        fi
        
        echo "✅ $display_name stopped"
    else
        echo "✅ $display_name not running"
    fi
}

# Stop services by port
stop_by_port 8765 "WebSocket Backend Server"
stop_by_port 8766 "Devices Server"
stop_by_port 3000 "HTTP Frontend Server"

# Stop processes by name (backup method)
stop_by_name "autotune_backend_server.js" "Node.js Backend"
stop_by_name "devices_server.py" "Python Devices Server"
stop_by_name "http.server" "Python HTTP Server"

# Stop any remaining autotune processes
echo "🛑 Checking for any remaining autotune processes..."
if pgrep -f "autotune" >/dev/null; then
    echo "   Found remaining autotune processes, stopping them..."
    pkill -f "autotune"
    sleep 1
    if pgrep -f "autotune" >/dev/null; then
        echo "   Force killing remaining autotune processes..."
        pkill -9 -f "autotune"
    fi
fi

echo ""
echo "🎉 Autotune Karaoke System stopped successfully!"
echo "================================================"
echo "💡 To restart the system, run: ./start_autotune_system.sh"
