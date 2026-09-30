@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Mambot 1.1
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto folder_error
if not exist "run.py" if exist "Mambot 1.1\run.py" cd "Mambot 1.1"
set "MAMBOT_MISSING="
for %%F in ("run.py" "backend\app.py" "static\index.html" "data\knowledge.json" "registry\lock.json" "runtime\python\python.exe" "runtime\python\python312.dll" "runtime\python\python312._pth" "runtime\python\Lib\encodings\__init__.py" "runtime\packages\fastapi\__init__.py" "runtime\packages\uvicorn\__init__.py") do (
  if not exist "%%~F" (
    echo THIEU FILE: "%%~F"
    set "MAMBOT_MISSING=1"
  )
)
if defined MAMBOT_MISSING goto incomplete
set "MAMBOT_ACTION=--open-browser"
if /i "%~1"=="--check" set "MAMBOT_ACTION=--check"
if /i "%~1"=="--no-browser" set "MAMBOT_ACTION=--no-browser"
"runtime\python\python.exe" -B run.py %MAMBOT_ACTION%
if errorlevel 1 goto failed
popd
exit /b 0
:incomplete
echo.
echo THU MUC DANG CHAY: "%CD%"
echo Mambot 1.1 can cac file THIEU FILE liet ke o tren.
echo Bam chuot phai Mambot 1.1.zip, chon Extract All / Giai nen tat ca.
echo Khong chay START_MAMBOT.cmd truc tiep ben trong cua so ZIP.
echo Can giu nguyen runtime, backend, static, data va registry.
:failed
echo.
echo Khong the khoi dong. Xem LOI o tren va file BAT_DAU.txt.
popd
if /i not "%~1"=="--check" pause
exit /b 1
:folder_error
echo Khong mo duoc thu muc chua START_MAMBOT.cmd. Hay giai nen vao thu muc tren may.
if /i not "%~1"=="--check" pause
exit /b 1
