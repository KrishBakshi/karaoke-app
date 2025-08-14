@echo off
echo 🛑 Shutting down Autotune Karaoke System...

REM Stop Node.js processes
echo 🎤 Stopping Node.js servers...
taskkill /f /im "node.exe" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Node.js servers stopped
) else (
    echo ℹ️  No Node.js servers were running
)

REM Stop Python processes
echo 🐍 Stopping Python servers...
taskkill /f /im "python.exe" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python servers stopped
) else (
    echo ℹ️  No Python servers were running
)

REM Stop any remaining processes on our ports
echo 🔌 Checking for remaining processes on ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765\|:8766\|:3000"') do (
    echo 🚫 Stopping process %%a on ports 8765, 8766, or 3000
    taskkill /f /pid %%a 2>nul
)

echo.
echo ✅ All servers stopped successfully!
echo 🎵 You can now run start_autotune_system_windows.bat to restart the system
pause
