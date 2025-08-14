# 🪟 Windows Setup Guide for Karaoke System

This guide will help you set up the Professional Autotune Karaoke System on Windows.

## 📋 Prerequisites

### **1. Install Node.js**
- Download from [nodejs.org](https://nodejs.org/)
- Choose LTS version (16.x or higher)
- Verify installation: `node --version`

### **2. Install Python**
- Download from [python.org](https://python.org/)
- Choose Python 3.6 or higher
- **Important**: Check "Add Python to PATH" during installation
- Verify installation: `python --version`

### **3. Install Conda**
- Download from [anaconda.com](https://anaconda.com/)
- Choose Miniconda or Anaconda
- Verify installation: `conda --version`

### **4. Install Visual Studio Build Tools**
- Download from [Microsoft](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- Choose "Build Tools for Visual Studio 2022"
- Install C++ build tools workload
- Verify: Open Developer Command Prompt and run `cl`

### **5. Install CMake**
- Download from [cmake.org](https://cmake.org/download/)
- Choose Windows x64 installer
- **Important**: Check "Add CMake to PATH"
- Verify installation: `cmake --version`

### **6. Install vcpkg (Package Manager)**
```cmd
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

## 🔧 Install Required Libraries

### **Install Audio Libraries via vcpkg**
```cmd
cd vcpkg
.\vcpkg install portaudio:x64-windows
.\vcpkg install libsndfile:x64-windows
.\vcpkg install aubio:x64-windows
.\vcpkg install sdl2:x64-windows
```

### **Set Environment Variable**
```cmd
set VCPKG_ROOT=C:\path\to\your\vcpkg
```

## 🐍 Setup Conda Environment

### **Create and Activate Environment**
```cmd
conda create -n k-gen python=3.9
conda activate k-gen
```

### **Install Python Dependencies**
```cmd
pip install numpy pathlib
```

## 🚀 Quick Start (Windows)

### **Option 1: Use Windows Batch Files (Recommended)**
```cmd
# Start the complete system
start_autotune_system_windows.bat

# Stop the system
stop_autotune_system_windows.bat
```

### **Option 2: Manual Startup**
```cmd
# 1. Start Node.js backend
start /b node autotune_backend_server.js

# 2. Start Python devices server
cd autotune-app
start /b python devices_server.py
cd ..

# 3. Start Python HTTP server
start /b python -m http.server 3000
```

## 🔨 Building C++ Backend (Windows)

### **Automatic Build**
```cmd
cd autotune-app
build_windows.bat
```

### **Manual Build**
```cmd
cd autotune-app
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
cmake --build . --config Release
```

## 🌐 Access the System

- **Frontend**: http://localhost:3000
- **WebSocket Backend**: ws://localhost:8765
- **Devices API**: http://localhost:8766/api/devices

## 🐛 Troubleshooting

### **Common Windows Issues**

#### **"Port already in use"**
```cmd
# Check what's using the ports
netstat -ano | findstr ":3000\|:8765\|:8766"

# Stop processes by PID
taskkill /f /pid <PID>
```

#### **"CMake not found"**
- Ensure CMake is added to PATH
- Restart Command Prompt after installation
- Try running from Developer Command Prompt

#### **"Visual Studio Build Tools not found"**
```cmd
# Run from Developer Command Prompt
"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
```

#### **"Libraries not found"**
```cmd
# Ensure vcpkg is properly installed
# Set CMAKE_TOOLCHAIN_FILE environment variable
set CMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
```

#### **"Python not found"**
- Ensure Python is added to PATH
- Restart Command Prompt after installation
- Try using `py` instead of `python`

### **Audio Issues on Windows**

#### **Microphone Access**
- Check Windows Privacy Settings → Microphone
- Ensure your browser has microphone permissions
- Test microphone in Windows Sound settings

#### **Audio Device Selection**
- Open Windows Sound settings
- Test different input/output devices
- Ensure sample rate is set to 48kHz

#### **PortAudio Issues**
```cmd
# Reinstall PortAudio
.\vcpkg remove portaudio:x64-windows
.\vcpkg install portaudio:x64-windows
```

## 📁 File Structure (Windows)

```
karaoke-frontend-local-run/
├── 🎵 Frontend & Backend
│   ├── app.js                          # React frontend application
│   ├── index.html                      # Main HTML file
│   ├── autotune_backend_server.js      # Node.js WebSocket server
│   ├── package.json                    # Node.js dependencies
│   └── integration_bridge.py           # Python integration bridge
├── 🚀 Windows Scripts
│   ├── start_system_windows.bat        # Basic system startup
│   ├── start_autotune_system_windows.bat # Complete system startup
│   └── stop_autotune_system_windows.bat  # System shutdown
├── 🎤 Autotune Backend (autotune-app/)
│   ├── karaoke.cpp                     # Main C++ application
│   ├── CMakeLists_windows.txt          # Windows CMake configuration
│   ├── build_windows.bat               # Windows build script
│   ├── autotune-karaoke.exe            # Windows executable
│   └── songs/                          # Song library
└── 📚 Documentation
    ├── README.md                       # Main documentation
    └── WINDOWS_SETUP.md                # This file
```

## 🔄 Windows-Specific Commands

### **Process Management**
```cmd
# List Node.js processes
tasklist | findstr "node.exe"

# List Python processes
tasklist | findstr "python.exe"

# Stop all Node.js processes
taskkill /f /im "node.exe"

# Stop all Python processes
taskkill /f /im "python.exe"
```

### **Port Checking**
```cmd
# Check if ports are in use
netstat -an | findstr ":3000"
netstat -an | findstr ":8765"
netstat -an | findstr ":8766"
```

### **Environment Variables**
```cmd
# Set vcpkg path
set VCPKG_ROOT=C:\path\to\vcpkg

# Set CMake toolchain
set CMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
```

## 🎯 Performance Tips for Windows

### **Audio Latency**
- Use WASAPI audio backend for lowest latency
- Set buffer size to 256 samples
- Ensure sample rate is 48kHz

### **System Optimization**
- Disable Windows audio enhancements
- Set power plan to "High Performance"
- Close unnecessary background applications

## 🆘 Getting Help

### **Check System Status**
```cmd
# Verify all components are running
netstat -an | findstr ":3000\|:8765\|:8766"

# Check process status
tasklist | findstr "node.exe\|python.exe"
```

### **Debug Mode**
```cmd
# Enable verbose output
set AUTOTUNE_DEBUG=1
start_autotune_system_windows.bat
```

### **Log Files**
- `device_server.log` - Device discovery server logs
- Check Windows Event Viewer for system errors

## 🎉 Success!

Once everything is working, you should see:
- ✅ All servers running on their respective ports
- 🎵 Frontend accessible at http://localhost:3000
- 🎤 Real-time autotune working with your microphone
- 🎵 Songs loading from the library

**Happy Karaoke! 🎤✨**
