#!/bin/bash

echo "🎤 Starting Autotune Karaoke System..."
echo "======================================"

# Check if we're in the right directory
if [ ! -f "autotune_backend_server.js" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: autotune_backend_server.js, autotune-app/"
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if conda environment exists
if ! conda env list | grep -q "k-gen"; then
    echo "❌ Conda environment 'k-gen' not found. Please create it first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Activate conda environment
echo "🐍 Activating conda environment 'base'..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate base

# Check if C++ executable exists, build if needed
if [ ! -f "autotune-app/autotune-karaoke" ]; then
    echo "🔨 C++ executable not found. Building..."
    cd autotune-app
    if [ -f "Makefile" ]; then
        make all
    elif [ -f "CMakeLists.txt" ]; then
        mkdir -p build
        cd build
        cmake ..
        make
        cd ..
    else
        echo "❌ No build system found. Please check autotune-app/ directory."
        exit 1
    fi
    cd ..
else
    echo "✅ C++ executable found"
fi

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies found"
fi

# Check port availability
echo "🔌 Checking port availability..."

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use by $service"
        echo "   Please stop the service or choose a different port"
        exit 1
    fi
}

check_port 8765 "WebSocket server"
check_port 8766 "Devices server"
check_port 3000 "HTTP frontend server"

echo "✅ All ports are available"

# Start the system components
echo "🚀 Starting system components..."

# Start Node.js backend server (WebSocket)
echo "🎤 Starting Node.js backend server..."
node autotune_backend_server.js &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start devices server
echo "🎤 Starting devices server..."
cd autotune-app
python3 devices_server.py &
DEVICES_PID=$!
cd ..
echo "   Devices server PID: $DEVICES_PID"

# Wait a moment for servers to start
sleep 2

# Start Python HTTP frontend server
echo "🌐 Starting Python HTTP frontend server..."
python3 -m http.server 3000 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait a moment for all servers to start
sleep 3

# Check if all servers are running
echo "🔍 Checking server status..."

check_server() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ $service is running on port $port"
    else
        echo "❌ $service is not running on port $port"
    fi
}

check_server 8765 "WebSocket Backend"
check_server 8766 "Devices Server"
check_server 3000 "HTTP Frontend"

echo ""
echo "🎉 Autotune Karaoke System is now running!"
echo "=========================================="
echo "🌐 Frontend: http://localhost:3000"
echo "🎤 WebSocket Backend: ws://localhost:8765"
echo "🎤 Devices API: http://localhost:8766/api/devices"
echo ""
echo "🎵 To stop the system, run: ./stop_autotune_system.sh"
echo "🎵 Or press Ctrl+C to stop this script"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Autotune Karaoke System..."
    kill $BACKEND_PID 2>/dev/null
    kill $DEVICES_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait
