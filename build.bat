@echo off
echo ==================================================
echo YouTube Media Downloader - Build Script
echo ==================================================

:: Check if tools exist
if not exist "tools\yt-dlp.exe" (
    echo [ERROR] yt-dlp.exe not found in tools\ directory.
    echo Please run setup_tools.bat first!
    pause
    exit /b 1
)

if not exist "tools\ffmpeg.exe" (
    echo [ERROR] ffmpeg.exe not found in tools\ directory.
    echo Please run setup_tools.bat first!
    pause
    exit /b 1
)

echo Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "CrowTube.spec" del "CrowTube.spec"

echo Starting PyInstaller build...
:: Building a standalone single executable using --onefile
pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "CrowTube" ^
    --add-data "ui/styles;ui/styles" ^
    --add-data "tools;tools" ^
    --add-data "assets;assets" ^
    --icon "assets/icon.png" ^
    --hidden-import "PySide6" ^
    app.py

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ==================================================
echo BUILD COMPLETE!
echo The compiled portable app is located in the 'dist\YouTubeDownloader' folder.
echo ==================================================
pause
