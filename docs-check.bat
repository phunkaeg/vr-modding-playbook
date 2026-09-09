@echo off
REM ---------------------------------------------------------------
REM  Use the canonical verifier, including receipt/instrument controls.
REM  You do NOT need this to pass in order to use docs-serve.bat.
REM ---------------------------------------------------------------
cd /d "%~dp0"

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" tools\verify.py %*
) else (
  py -3 tools\verify.py %*
)
if errorlevel 1 goto :failed

echo.
echo OK - requested verification checks passed; see any explicit SKIP lines above.
echo.
call :maybepause
exit /b 0

:failed
echo.
echo ** DOC VALIDATION FAILED - fix the errors above **
echo.
call :maybepause
exit /b 1

REM A BOUNDED wait, never `pause`. An Explorer double-click and `cmd /c script.bat`
REM are indistinguishable from inside the script, so there is no reliable way to
REM detect "a human is watching" - and an unconditional pause here hung a
REM background task for 92 minutes. `timeout` holds the window ~20s for a human
REM (any key continues), and returns INSTANTLY when stdin is redirected, which is
REM every script, CI and agent invocation.
:maybepause
echo (window closes in 20s - press any key)
timeout /t 20 >nul 2>&1
exit /b 0
