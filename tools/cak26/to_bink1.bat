@echo off
rem Converts every .mp4 under a folder to Bink 1, saved with a .bk2 extension next to the source.
rem Usage: double-click (does "Videos (2K19 Derived)"), or drag any folder onto this file.
setlocal enabledelayedexpansion
cd /d "%~dp0"
set RAD=C:\Program Files (x86)\RADVideo\binkc.exe
set ROOT=%~1
if "%ROOT%"=="" set ROOT=%~dp0..\..\Videos (2K19 Derived)
echo start %date% %time% > tobink1.log
for /r "%ROOT%" %%V in (*.mp4) do (
  if not exist "%%~dpnV.bk2" (
    echo %%V
    ffmpeg.exe -v error -y -i "%%V" -an -c:v rawvideo -pix_fmt bgr24 "%TEMP%\bk1tmp.avi" >> tobink1.log 2>&1
    "%RAD%" "%TEMP%\bk1tmp.avi" "%TEMP%\bk1tmp.bik" /O >> tobink1.log 2>&1
    if exist "%TEMP%\bk1tmp.bik" move /y "%TEMP%\bk1tmp.bik" "%%~dpnV.bk2" >nul
    if exist "%%~dpnV.bk2" (echo OK %%V >> tobink1.log) else (echo FAILED %%V >> tobink1.log)
    del "%TEMP%\bk1tmp.avi" 2>nul
  )
)
echo finished %date% %time% >> tobink1.log
echo ALL DONE - see tobink1.log
pause
