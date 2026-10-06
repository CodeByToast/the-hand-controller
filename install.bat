@echo off
setlocal
cd /d "%~dp0"

if not exist "models\hand_landmarker.task" (
    echo The hand-tracking model is missing from the models folder.
    echo Restore models\hand_landmarker.task, then run this installer again.
    pause
    exit /b 1
)

where py >nul 2>&1
if not errorlevel 1 goto USE_PY_LAUNCHER
where python >nul 2>&1
if errorlevel 1 goto NO_PYTHON
goto USE_PYTHON

:USE_PY_LAUNCHER
py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 9))" >nul 2>&1
if errorlevel 1 goto NO_SUPPORTED_PYTHON
py -3 -m venv .venv
if errorlevel 1 goto VENV_FAILED
goto INSTALL_PACKAGES

:USE_PYTHON
python -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info < (3, 9))" >nul 2>&1
if errorlevel 1 goto NO_SUPPORTED_PYTHON
python -m venv .venv
if errorlevel 1 goto VENV_FAILED

:INSTALL_PACKAGES
echo Installing required packages. This may take a few minutes...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto PIP_FAILED
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto PIP_FAILED
echo.
echo Setup complete. Double-click run.bat to start The Hand Controller.
pause
exit /b 0

:NO_PYTHON
echo Python 3 was not found. Install Python 3.9 or newer from python.org, then run this installer again.
goto FAILED

:NO_SUPPORTED_PYTHON
echo Python 3.9 or newer could not be selected. Install a current 64-bit Python 3 from python.org, then retry.
goto FAILED

:VENV_FAILED
echo Python was found, but its virtual environment could not be created.
echo Repair or reinstall Python and make sure the pip and venv features are enabled.
goto FAILED

:PIP_FAILED
echo Package installation failed. Check your internet connection and try install.bat again.
echo One or more camera or hand-tracking packages may not support the selected Python version yet.
echo Try installing Python 3.13 or 3.12 from python.org, then run install.bat again.
goto FAILED

:FAILED
pause
exit /b 1