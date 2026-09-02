@echo off
REM ---------------------------------------------------------------
REM  Validate source-coverage and fleet-bottleneck ledgers/generated
REM  fragments, then link-check the docs. --strict makes a broken
REM  internal link an error.
REM  You do NOT need this to pass in order to use docs-serve.bat.
REM ---------------------------------------------------------------
cd /d "%~dp0"

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" tools\coverage.py --check
  if errorlevel 1 goto :failed
  "%LocalAppData%\Programs\Python\Python312\python.exe" tools\bottlenecks.py --check
  if errorlevel 1 goto :failed
  "%LocalAppData%\Programs\Python\Python312\python.exe" tools\playbook_integrity.py --check
) else (
  py -3 tools\coverage.py --check
  if errorlevel 1 goto :failed
  py -3 tools\bottlenecks.py --check
  if errorlevel 1 goto :failed
  py -3 tools\playbook_integrity.py --check
)
if errorlevel 1 goto :failed

mkdocs build --strict
if errorlevel 1 goto :failed

echo.
echo OK - source and bottleneck ledgers, generated docs, and strict site build all pass.
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
