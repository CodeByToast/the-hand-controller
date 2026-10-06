@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The app is not installed yet. Double-click install.bat first.
    pause
    exit /b 1
)

set "HAND_CONTROLLER_LAUNCHER=%~f0"
set "HAND_CONTROLLER_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $link = Join-Path $desktop 'The Hand Controller.lnk'; $iconPath = Join-Path $env:HAND_CONTROLLER_DIR 'app-icon.ico'; $iconLocation = [string]::Concat($iconPath, ',0'); $stagedLink = Join-Path $env:TEMP ('TheHandController-' + [guid]::NewGuid().ToString('N') + '.lnk'); try { $shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut($stagedLink); $shortcut.TargetPath = $env:HAND_CONTROLLER_LAUNCHER; $shortcut.WorkingDirectory = $env:HAND_CONTROLLER_DIR; $shortcut.Description = 'Launch The Hand Controller'; if (Test-Path -LiteralPath $iconPath) { $shortcut.IconLocation = $iconLocation }; $shortcut.Save(); if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link -Force }; [IO.File]::Move($stagedLink, $link); Write-Output 'Desktop shortcut created or updated.' } catch { Write-Output ('Could not create or update the desktop shortcut: ' + $_.Exception.Message) } finally { if (Test-Path -LiteralPath $stagedLink) { Remove-Item -LiteralPath $stagedLink -Force -ErrorAction SilentlyContinue } }"

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause