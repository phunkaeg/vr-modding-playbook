@echo off
REM Builds and runs the reference-maths tests with MSVC. No dependencies beyond a
REM VS 2022 Build Tools install. Propagates the real exit code -- see the playbook's
REM rule about never masking a validator's status.
setlocal
set VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat
if not exist "%VCVARS%" set VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
if not exist "%VCVARS%" set VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat
if not exist "%VCVARS%" set VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat
if not exist "%VCVARS%" (
  echo Could not find vcvars64.bat -- install VS 2022 Build Tools, or use CMake:
  echo   cmake -S . -B build ^&^& cmake --build build ^&^& ctest --test-dir build
  exit /b 2
)

call "%VCVARS%" >nul
if errorlevel 1 exit /b 2

pushd "%~dp0"
if not exist build mkdir build

REM WILDCARD ON PURPOSE. An explicit file list is how tests\test_depth_slice.cpp came to be
REM written, committed, and never compiled -- the suite reported "all passed" with a whole
REM file missing from the build.
cl /nologo /std:c++17 /EHsc /W4 /permissive- /Iinclude ^
   tests\*.cpp ^
   /Fo:build\ /Fe:build\vrref_tests.exe
if errorlevel 1 ( popd & exit /b 1 )

build\vrref_tests.exe
set RC=%ERRORLEVEL%
popd
exit /b %RC%
