$deckDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startup = [Environment]::GetFolderPath('Startup')
$linkPath = Join-Path $startup 'Deck Stream.lnk'
$vbsPath = Join-Path $deckDir 'start_hidden.vbs'

$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($linkPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = "`"$vbsPath`""
$shortcut.WorkingDirectory = $deckDir
$shortcut.Description = 'Deck - Browser Stream Deck'
$shortcut.Save()

Write-Host "Autostart OK: $linkPath"