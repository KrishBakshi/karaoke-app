@echo off
echo 🎵 Starting Karaoke System with Device Discovery...

REM Function to cleanup background processes
:cleanup
echo 🛑 Shutting down servers...
taskkill /f /im "node.exe" 2>nul
exit /b 0

REM Set up signal handlers (Windows doesn't have trap, but we can handle Ctrl+C)
REM This is a simplified version - in production you might want to use PowerShell

REM Start device discovery server in background
echo 🎤 Starting device discovery server...
start /b node device_server.js > device_server.log 2>&1

REM Wait a moment for device server to start
timeout /t 2 /nobreak >nul

REM Test device server
echo 🔍 Testing device discovery API...
curl -s http://localhost:3001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Device discovery server is running
) else (
    echo ❌ Device discovery server failed to start
    goto cleanup
)

REM Start main karaoke backend server
echo 🎵 Starting main karaoke backend server...
start /b node autotune_backend_server.js

REM Wait for both servers
echo 🚀 Both servers are running!
echo    Device Discovery: http://localhost:3001
echo    Main Backend: http://localhost:8765
echo    Frontend: Open index.html in your browser
echo.
echo Press Ctrl+C to stop all servers

REM Keep script running
pause >nul
goto cleanup
