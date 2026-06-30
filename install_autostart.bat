@echo off
title Deck Autostart
cd /d "%~dp0"

echo.
echo Installing Deck autostart...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_autostart.ps1"
if errorlevel 1 goto fail

set LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Deck Stream.lnk
if exist "%LINK%" goto ok

:fail
echo.
echo ERROR: shortcut was not created.
echo.
pause
exit /b 1

:ok
echo.
echo OK: Deck will start with Windows.
echo Shortcut: %LINK%
echo.
pause