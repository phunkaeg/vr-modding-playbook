@echo off
REM ---------------------------------------------------------------
REM  Publish the SHAREABLE playbook on a temporary public URL.
REM
REM  Builds the sanitised variant, refuses to continue if the
REM  sanitise check fails, serves it locally, then opens a Cloudflare
REM  quick tunnel and prints a https://<random>.trycloudflare.com URL.
REM
REM  THE URL IS UNAUTHENTICATED. Anyone with the link can read it.
REM  It dies when you close this window.
REM ---------------------------------------------------------------
setlocal
cd /d "%~dp0"

set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=py -3"
set "SRVTITLE=VR Playbook shared server"

where cloudflared >nul 2>&1
if errorlevel 1 goto :nocloudflared

echo Building the shareable variant...
echo.
"%PY%" tools\build_public.py
if errorlevel 1 goto :unsafe

echo.
echo Starting the local server...
start "%SRVTITLE%" /min cmd /c ""%PY%" -m http.server 8001 --bind 127.0.0.1 -d site-public"

REM Give the server a moment to bind before the tunnel reaches for it.
ping -n 3 127.0.0.1 >nul

echo.
echo ---------------------------------------------------------------
echo  Opening a Cloudflare quick tunnel.
echo  Your public URL appears below as  https://....trycloudflare.com
echo.
echo  REMEMBER: that link needs no password. Share it deliberately.
echo  Ctrl+C here ends the tunnel and stops the server.
echo ---------------------------------------------------------------
echo.
cloudflared tunnel --url http://127.0.0.1:8001

echo.
echo Tunnel closed. Stopping the local server...
taskkill /FI "WINDOWTITLE eq %SRVTITLE%*" /T /F >nul 2>&1
echo Done - the public URL is dead.
echo.
pause
goto :eof

:nocloudflared
echo.
echo ===============================================================
echo  cloudflared is not installed.
echo.
echo  Install it once with:
echo.
echo      winget install Cloudflare.cloudflared
echo.
echo  Then run this file again. Nothing has been published.
echo ===============================================================
echo.
pause
exit /b 1

:unsafe
echo.
echo ===============================================================
echo  BUILD OR SANITISE CHECK FAILED - NOTHING HAS BEEN PUBLISHED.
echo.
echo  The shareable copy could not be proven clean, so no server
echo  and no tunnel were started. Read the errors above.
echo ===============================================================
echo.
pause
exit /b 1
