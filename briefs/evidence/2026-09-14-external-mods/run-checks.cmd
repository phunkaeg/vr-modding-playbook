@echo off
setlocal
rem Local-only source audit. Requires the pinned checkouts and Visual Studio 2022.
set "DONORS=D:\Dev Debug\Other VR Mods"
set "OUT=%~dp0..\..\..\reference\build\external-harvest-20260914"
if not exist "%OUT%" mkdir "%OUT%"
if errorlevel 1 exit /b 1
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%OUT%"
cl /nologo /EHsc /std:c++20 /I"%DONORS%" /I"%DONORS%\MGS5VR\include" /Fe:policy_checks.exe "%~dp0policy_checks.cpp" "%DONORS%\MGS5VR\src\core.cpp" "%DONORS%\MGS5VR\src\stereo.cpp"
if errorlevel 1 (popd & exit /b 1)
policy_checks.exe
set "CHECK_RESULT=%ERRORLEVEL%"
popd
exit /b %CHECK_RESULT%
