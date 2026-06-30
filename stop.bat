@echo off
title Deck - Stop
echo Stopping Deck on port 8765...
powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Write-Host 'Deck stopped.' } else { Write-Host 'Deck is not running.' }"
pause