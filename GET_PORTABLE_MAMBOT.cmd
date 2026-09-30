@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "MAMBOT_DOWNLOAD_URL=https://github.com/Jakcasas/mambot/releases/download/v1.1.0/Mambot.1.1.zip"
set "MAMBOT_EXPECTED_SHA256=DAF6C0AFB524F49071D9D24D2917F39BC789853C6ACBA09F20F5E6BA9E00A294"
set "MAMBOT_INSTALL_BASE=%~dp0var\mambot-portable"
set "MAMBOT_ARCHIVE_FILE=%~dp0var\Mambot.1.1.zip"
if not exist "%~dp0var" mkdir "%~dp0var"
if errorlevel 1 goto failed
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; try { $archive=$env:MAMBOT_ARCHIVE_FILE; $base=$env:MAMBOT_INSTALL_BASE; $project=Join-Path $base 'Mambot 1.1'; if(-not (Test-Path -LiteralPath (Join-Path $project 'runtime\python\python.exe') -PathType Leaf)){ $valid=(Test-Path -LiteralPath $archive -PathType Leaf) -and ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($archive))).Replace('-','') -eq $env:MAMBOT_EXPECTED_SHA256); if(-not $valid){ Invoke-WebRequest -UseBasicParsing -Uri $env:MAMBOT_DOWNLOAD_URL -OutFile $archive -TimeoutSec 120; if([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($archive))).Replace('-','') -ne $env:MAMBOT_EXPECTED_SHA256){ throw 'SHA-256 khong khop. Hay tai file Mambot.1.1.zip tu GitHub Releases.' } }; if(Test-Path -LiteralPath $base){ Move-Item -LiteralPath $base -Destination ($base+'-incomplete-'+[Guid]::NewGuid().ToString('N')) }; Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory($archive,$base) }; if(-not (Test-Path -LiteralPath (Join-Path $project 'START_MAMBOT.cmd') -PathType Leaf)){ throw 'Goi ZIP thieu START_MAMBOT.cmd.' }; Write-Host ('DA GIAI NEN: '+$project); exit 0 } catch { Write-Host ('LOI TAI/ GIAI NEN: '+$_.Exception.Message); exit 1 }"
if errorlevel 1 goto failed
call "%MAMBOT_INSTALL_BASE%\Mambot 1.1\START_MAMBOT.cmd" %~1
exit /b %ERRORLEVEL%
:failed
echo Tai thu cong goi Windows day du tai:
echo %MAMBOT_DOWNLOAD_URL%
echo Bam chuot phai ZIP, chon Extract All, sau do chay START_MAMBOT.cmd trong thu muc da giai nen.
if /i not "%~1"=="--check" pause
exit /b 1
