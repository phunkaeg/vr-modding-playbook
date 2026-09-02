@echo off
REM ---------------------------------------------------------------
REM  Live docs server. Rebuilds automatically as you edit.
REM  Leave it running while you read. Ctrl+C to stop.
REM ---------------------------------------------------------------
cd /d "%~dp0"
echo Serving docs at  http://127.0.0.1:8000
echo Edits reload by themselves. Press Ctrl+C to stop.
echo.
mkdocs serve
if errorlevel 1 (
  echo.
  echo ** FAILED ** - is mkdocs installed?   pip install -r requirements.txt
  echo.
  pause
)
