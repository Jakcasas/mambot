@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
call START_MAMBOT.cmd --check
set "MAMBOT_RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %MAMBOT_RESULT%
