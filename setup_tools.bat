@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo YouTube Media Downloader - Setup Tools
echo ==================================================
echo.

set "TOOLS_DIR=%~dp0tools"
if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"

echo [1/3] Downloading latest yt-dlp.exe...
curl -L -o "%TOOLS_DIR%\yt-dlp.exe" "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to download yt-dlp.
    goto :error
)
echo [OK] yt-dlp downloaded successfully.
echo.

echo [2/3] Downloading FFmpeg (gyan.dev)...
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "TEMP_ZIP=%TOOLS_DIR%\ffmpeg_temp.zip"

curl -L -o "%TEMP_ZIP%" "%FFMPEG_URL%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to download FFmpeg.
    goto :error
)

echo Extracting FFmpeg...
powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TOOLS_DIR%' -Force"

:: Move ffmpeg.exe and ffprobe.exe to tools dir
for /d %%I in ("%TOOLS_DIR%\ffmpeg-*") do (
    move /y "%%I\bin\ffmpeg.exe" "%TOOLS_DIR%\" >nul
    move /y "%%I\bin\ffprobe.exe" "%TOOLS_DIR%\" >nul
    rmdir /s /q "%%I"
)
del "%TEMP_ZIP%"

echo [OK] FFmpeg extracted successfully.
echo.

echo [3/3] Creating empty icon file (if missing)...
set "ASSETS_DIR=%~dp0assets"
if not exist "%ASSETS_DIR%" mkdir "%ASSETS_DIR%"
if not exist "%ASSETS_DIR%\icon.png" (
    powershell -Command "$bytes = [byte[]]::new(0); [System.IO.File]::WriteAllBytes('%ASSETS_DIR%\icon.png', $bytes)"
    echo Created placeholder icon.png in assets directory.
)

echo.
echo ==================================================
echo SETUP COMPLETE!
echo All required tools have been downloaded to the 'tools' folder.
echo You can now run the app using 'python app.py' or build it with 'build.bat'.
echo ==================================================
pause
exit /b 0

:error
echo.
echo Setup failed. Please check your internet connection and try again.
pause
exit /b 1
