@echo off
rem Converts every .mp4 under a folder to Bink 1, saved with a .bk2 extension next to the source.
rem Usage: double-click (does "Videos (2K19 Derived)"), or drag any folder onto this file.
setlocal enabledelayedexpansion
cd /d "%~dp0"
set TAG=%RANDOM%%RANDOM%
set LOG=%~dp0tobink1_%TAG%.log
set TMPA=%TEMP%\bk1_%TAG%.avi
set TMPB=%TEMP%\bk1_%TAG%.bik
set RAD=C:\Program Files (x86)\RADVideo\binkc.exe
set ROOT=%~1
if "%ROOT%"=="" set ROOT=%~dp0..\..\Videos (2K19 Derived)
echo start %date% %time% > "%LOG%"
for /r "%ROOT%" %%V in (*.mp4) do (
  if not exist "%%~dpnV.bk2" (
    echo %%V
    ffmpeg.exe -v error -y -i "%%V" -an -c:v rawvideo -pix_fmt bgr24 "%TMPA%" >> "%LOG%" 2>&1
    "%RAD%" "%TMPA%" "%TMPB%" /O >> "%LOG%" 2>&1
    if exist "%TMPB%" move /y "%TMPB%" "%%~dpnV.bk2" >nul
    if exist "%%~dpnV.bk2" (echo OK %%V >> "%LOG%") else (echo FAILED %%V >> "%LOG%")
    del "%TMPA%" 2>nul
  )
)
echo finished %date% %time% >> "%LOG%"
echo ALL DONE - see %LOG%
pause
