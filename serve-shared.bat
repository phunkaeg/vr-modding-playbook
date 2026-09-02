@echo off
REM ---------------------------------------------------------------
REM  Build the SHAREABLE playbook and serve it locally for review.
REM
REM  This is the variant with the internal status report removed:
REM  no coverage dashboard, no fleet table, no bottleneck matrix or
REM  per-project "next proof", and no local paths.
REM
REM  Nothing leaves this machine. Use host-shared.bat for that.
REM ---------------------------------------------------------------
setlocal
cd /d "%~dp0"

set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=py -3"

echo Building the shareable variant...
echo.
"%PY%" tools\build_public.py
if errorlevel 1 goto :unsafe

echo.
echo ---------------------------------------------------------------
echo  Serving the SHAREABLE copy at  http://127.0.0.1:8001
echo  This is exactly what host-shared.bat would publish.
echo  Ctrl+C to stop.
echo ---------------------------------------------------------------
echo.
"%PY%" -m http.server 8001 --bind 127.0.0.1 -d site-public
goto :eof

:unsafe
echo.
echo ===============================================================
echo  BUILD OR SANITISE CHECK FAILED - nothing is being served.
echo  Read the errors above. Do not publish site-public\.
echo ===============================================================
echo.
pause
exit /b 1
