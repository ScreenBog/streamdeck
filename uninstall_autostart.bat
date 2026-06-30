@echo off
title Deck Remove Autostart
set LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Deck Stream.lnk
if exist "%LINK%" (
    del "%LINK%"
    echo Autostart removed.
) else (
    echo Autostart was not installed.
)
pause