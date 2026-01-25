@echo off
title openAgloadMonitor
REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat"
set PROJECT_DRIVE=Cd \
set PROJECT_FOLDER=openagloadmonitor
set ENVIRONMENT=openagloadmonitor
set SCRIPT_1=video_server.py
set SCRIPT_2=run.py

REM Navigate to project directory and activate environment
call %CONDA_PATH%
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
call conda activate %ENVIRONMENT%

REM Launch scripts in separate terminals (remove REM to enable)
echo Starting %SCRIPT_1%...
start "Script 1" cmd /k python %SCRIPT_1%

REM Wait 2 seconds between scripts
timeout /t 2 /nobreak >nul

echo Starting %SCRIPT_2%...
start "Script 2" cmd /k python %SCRIPT_2%

REM Show current location and keep main window open
echo Anaconda environment activated in %cd%
echo Current conda environment: %ENVIRONMENT%
cmd /k
