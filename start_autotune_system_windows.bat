@echo off
echo 🎤 Starting Autotune Karaoke System...
echo ======================================

REM Check if we're in the right directory
if not exist "autotune_backend_server.js" (
    echo ❌ Error: Please run this script from the project root directory
    echo    Current directory: %CD%
    echo    Expected files: autotune_backend_server.js, autotune-app/
    pause
    exit /b 1
)

REM Check prerequisites
echo 🔍 Checking prerequisites...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if Python3 is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if conda environment exists
conda env list | findstr "k-gen" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Conda environment 'k-gen' not found. Please create it first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Activate conda environment
echo 🐍 Activating conda environment 'k-gen'...
call conda activate k-gen

REM Check if C++ executable exists, build if needed
if not exist "autotune-app\autotune-karaoke.exe" (
    echo 🔨 C++ executable not found. Building...
    cd autotune-app
    if exist "Makefile" (
        make all
    ) else if exist "CMakeLists.txt" (
        if not exist "build" mkdir build
        cd build
        cmake ..
        cmake --build . --config Release
        cd ..
    ) else (
        echo ❌ No build system found. Please check autotune-app/ directory.
        pause
        exit /b 1
    )
    cd ..
) else (
    echo ✅ C++ executable found
)

REM Check if Node.js dependencies are installed
if not exist "node_modules" (
    echo 📦 Installing Node.js dependencies...
    npm install
) else (
    echo ✅ Node.js dependencies found
)

REM Check port availability
echo 🔌 Checking port availability...

REM Check if ports are in use (Windows equivalent)
netstat -an | findstr ":8765" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Port 8765 is already in use
    echo    Please stop the service or choose a different port
    pause
    exit /b 1
)

netstat -an | findstr ":8766" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Port 8766 is already in use
    echo    Please stop the service or choose a different port
    pause
    exit /b 1
)

netstat -an | findstr ":3000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Port 3000 is already in use
    echo    Please stop the service or choose a different port
    pause
    exit /b 1
)

echo ✅ All ports are available

REM Start the system components
echo 🚀 Starting system components...

REM Start Node.js backend server (WebSocket)
echo 🎤 Starting Node.js backend server...
start /b node autotune_backend_server.js
echo    Backend started

REM Start devices server
echo 🎤 Starting devices server...
cd autotune-app
start /b python devices_server.py
cd ..
echo    Devices server started

REM Wait a moment for servers to start
timeout /t 2 /nobreak >nul

REM Start Python HTTP frontend server
echo 🌐 Starting Python HTTP frontend server...
start /b python -m http.server 3000
echo    Frontend started

REM Wait a moment for all servers to start
timeout /t 3 /nobreak >nul

REM Check if all servers are running
echo 🔍 Checking server status...

netstat -an | findstr ":8765" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ WebSocket Backend is running on port 8765
) else (
    echo ❌ WebSocket Backend is not running on port 8765
)

netstat -an | findstr ":8766" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Devices Server is running on port 8766
) else (
    echo ❌ Devices Server is not running on port 8766
)

netstat -an | findstr ":3000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ HTTP Frontend is running on port 3000
) else (
    echo ❌ HTTP Frontend is not running on port 3000
)

echo.
echo 🎉 Autotune Karaoke System is now running!
echo ==========================================
echo 🌐 Frontend: http://localhost:3000
echo 🎤 WebSocket Backend: ws://localhost:8765
echo 🎤 Devices API: http://localhost:8766/api/devices
echo.
echo 🎵 To stop the system, run: stop_autotune_system_windows.bat
echo 🎵 Or close this window to stop all servers

REM Keep script running
pause
