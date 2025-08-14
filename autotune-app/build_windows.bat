@echo off
echo 🔨 Building Autotune Karaoke for Windows...

REM Check if we're in the right directory
if not exist "CMakeLists.txt" (
    echo ❌ Error: CMakeLists.txt not found. Please run this from the autotune-app directory.
    pause
    exit /b 1
)

REM Check if CMake is installed
cmake --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ CMake is not installed. Please install CMake first.
    echo    Download from: https://cmake.org/download/
    pause
    exit /b 1
)

REM Check if Visual Studio Build Tools are available
where cl >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Visual Studio Build Tools not found in PATH.
    echo    Please run this from a Developer Command Prompt or install Visual Studio Build Tools.
    echo    You can also try running: "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    echo.
    echo    Press any key to continue anyway...
    pause >nul
)

REM Create build directory
if not exist "build" mkdir build
cd build

REM Configure with CMake
echo 🔧 Configuring with CMake...
cmake .. -G "Visual Studio 17 2022" -A x64
if %errorlevel% neq 0 (
    echo ❌ CMake configuration failed.
    echo    This might be due to missing dependencies.
    echo    Please install the required libraries using vcpkg:
    echo    vcpkg install portaudio libsndfile aubio sdl2
    pause
    exit /b 1
)

REM Build the project
echo 🚀 Building project...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo ❌ Build failed.
    pause
    exit /b 1
)

REM Check if executable was created
if exist "bin\Release\autotune-karaoke.exe" (
    echo ✅ Build successful!
    echo 🎵 Executable created: bin\Release\autotune-karaoke.exe
    
    REM Copy executable to parent directory for convenience
    copy "bin\Release\autotune-karaoke.exe" "..\autotune-karaoke.exe" >nul
    echo 📁 Copied to: autotune-karaoke.exe
) else (
    echo ❌ Executable not found after build.
    echo    Expected location: bin\Release\autotune-karaoke.exe
)

cd ..
echo.
echo 🎉 Build process completed!
pause
