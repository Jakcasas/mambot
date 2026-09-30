@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Mambot 1.1
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto folder_error
if not exist "run.py" if exist "Mambot 1.1\run.py" cd "Mambot 1.1"
if not exist "runtime\python\python.exe" if exist "run.py" if exist "backend\app.py" goto source_archive
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
:source_archive
if /i "%~1"=="--check" goto incomplete
echo Ban dang dung SOURCE CODE ZIP tu nut Code cua GitHub. Goi nay khong chua Python va thu vien.
echo Dang tai goi Windows tu GitHub Release va kiem tra SHA-256 truoc khi giai nen.
if not exist "GET_PORTABLE_MAMBOT.cmd" goto incomplete
call "GET_PORTABLE_MAMBOT.cmd" %~1
set "MAMBOT_RESULT=%ERRORLEVEL%"
popd
exit /b %MAMBOT_RESULT%
:incomplete
echo.
echo THU MUC DANG CHAY: "%CD%"
echo Mambot 1.1 can cac file THIEU FILE liet ke o tren.
echo Neu thu muc co ten mambot-main, ban da tai Source code ZIP tu nut Code cua GitHub.
echo Goi Windows day du: https://github.com/Jakcasas/mambot/releases/download/v1.1.0/Mambot.1.1.zip
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
