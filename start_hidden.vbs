Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = dir
WshShell.Run "cmd /c """ & dir & "\run_service.bat""", 0, False