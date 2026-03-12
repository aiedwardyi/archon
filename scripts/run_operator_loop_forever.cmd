@echo off
setlocal

cd /d "%~dp0\.."

set "OUT_LOG=operator-loop.out.log"
set "ERR_LOG=operator-loop.err.log"
set "STOP_FILE=operator-loop.stop"

echo [%date% %time%] operator wrapper starting>>"%ERR_LOG%"

:loop
if exist "%STOP_FILE%" (
  echo [%date% %time%] stop file detected, exiting wrapper>>"%ERR_LOG%"
  del "%STOP_FILE%" >nul 2>nul
  exit /b 0
)

echo [%date% %time%] launching operator loop>>"%ERR_LOG%"
.\.venv\Scripts\python.exe eval\operator_loop.py --expected-branch eval/loops --max-cycles 0 --commit-wins 1>>"%OUT_LOG%" 2>>"%ERR_LOG%"
set "EXIT_CODE=%ERRORLEVEL%"
echo [%date% %time%] operator loop exited with code %EXIT_CODE%>>"%ERR_LOG%"

if exist "%STOP_FILE%" (
  echo [%date% %time%] stop file detected after exit, exiting wrapper>>"%ERR_LOG%"
  del "%STOP_FILE%" >nul 2>nul
  exit /b 0
)

timeout /t 10 /nobreak >nul
goto loop
