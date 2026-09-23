Option Explicit
' Lanceur College Aureole : execute le script PowerShell en arriere-plan
' (fenetre masquee), puis ferme immediatement ce process VBS.
Dim fso, dir, sh, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & dir & "\lanceur-college-aureole.ps1"""
sh.Run cmd, 0, False