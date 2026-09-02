@echo off
REM ---------------------------------------------------------------
REM  Load the Gemini key into THIS SHELL ONLY, then run something
REM  with it present.
REM
REM  Why a launcher and not just a setter: an environment variable
REM  set here is inherited by CHILD processes only. A Claude Code
REM  session that is ALREADY RUNNING will never see it. Start the
REM  thing that needs the key FROM here.
REM
REM    graphify-key.bat                 open a shell with the key set
REM    graphify-key.bat claude          start Claude Code with the key set
REM    graphify-key.bat <any command>   run that command with the key set
REM
REM  The key is never printed, never written to the registry, and
REM  never persists past this window.
REM ---------------------------------------------------------------
setlocal EnableExtensions EnableDelayedExpansion

set "KEYFILE=%LocalAppData%\graphify\gemini.key"
if not exist "%KEYFILE%" goto :nokey

REM First non-empty line only. No echo, so the key never reaches the console.
set "GEMINI_API_KEY="
for /f "usebackq delims=" %%K in ("%KEYFILE%") do (
    if not defined GEMINI_API_KEY set "GEMINI_API_KEY=%%K"
)
if not defined GEMINI_API_KEY goto :emptykey

REM Length-only sanity check. Delayed expansion is required here: inside a
REM parenthesised block %LEN% would expand once at parse time and the loop
REM would never terminate (or fail to parse at all).
set "PROBE=!GEMINI_API_KEY!"
set /a LEN=0
:measure
if not defined PROBE goto :measured
set "PROBE=!PROBE:~1!"
set /a LEN+=1
if !LEN! GEQ 200 goto :measured
goto :measure
:measured

if !LEN! LSS 20 goto :suspect

echo Gemini key loaded for this window only (!LEN! characters).
echo Any process started from here inherits it.
echo.

if "%~1"=="" (
    echo No command given - opening a shell with the key set.
    echo Start Claude Code or run graphify from here. Type exit to discard it.
    echo.
    cmd /k
    goto :eof
)

REM Run the command and PROPAGATE ITS EXIT CODE. Without the explicit
REM `exit /b`, this launcher returns 0 even when the command it wrapped
REM failed - which silently reports a failed extraction as a success.
call %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo.& echo Command exited with code %RC%.
exit /b %RC%

:nokey
echo.
echo ===============================================================
echo  No key file at:
echo    %KEYFILE%
echo.
echo  Create it with the bare key on one line, nothing else:
echo    mkdir "%LocalAppData%\graphify"
echo    notepad "%KEYFILE%"
echo.
echo  Keep it outside any repo. Do not commit it, and do not paste
echo  it into a chat.
echo ===============================================================
echo.
exit /b 1

:emptykey
echo  The key file exists but its first line is empty: %KEYFILE%
exit /b 1

:suspect
echo  First line is only !LEN! characters - shorter than any real
echo  Gemini key. Check the file holds the key, not a placeholder.
exit /b 1
