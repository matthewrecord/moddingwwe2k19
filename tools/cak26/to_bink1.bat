@echo off
rem Converts every .mp4 under a folder to Bink 1, saved with a .bk2 extension next to the source.
rem Usage: double-click (does "Videos (2K19 Derived)"), or drag any folder onto this file.
setlocal
cd /d "%~dp0"
set TAG=%RANDOM%%RANDOM%
set LOG=%~dp0tobink1_%TAG%.log
set TMPD=%TEMP%\bk1_%TAG%
set TMPB=%TEMP%\bk1_%TAG%.bik
set LST=%TEMP%\bk1_%TAG%.lst
set RAD=C:\Program Files (x86)\RADVideo\binkc.exe
set ROOT=%~1
if "%ROOT%"=="" set ROOT=%~dp0..\..\Videos (2K19 Derived)
echo start %date% %time% > "%LOG%"
for /r "%ROOT%" %%V in (*.mp4) do (
  if not exist "%%~dpnV.bk2" (
    call :one "%%V" "%%~dpnV.bk2"
    if not exist "%%~dpnV.bk2" goto :stop
  )
)
echo finished %date% %time% >> "%LOG%"
echo ALL DONE - see %LOG%
pause
exit /b

:one
echo %~1
if exist "%TMPD%" rd /s /q "%TMPD%"
mkdir "%TMPD%"
del "%TMPB%" 2>nul
ffmpeg.exe -v error -y -i "%~1" -an -start_number 0 -pix_fmt bgr24 "%TMPD%\f%%04d.bmp" >> "%LOG%" 2>&1
dir /b /s /on "%TMPD%\*.bmp" > "%LST%"
start "" "%RAD%" "%LST%" "%TMPB%" /F29.97 /O /#
rem wait for binkc: when it exits on its own, or when the output stops growing, close it
set last=-1
:wait
timeout /t 2 /nobreak >nul
tasklist /fi "imagename eq binkc.exe" | find /i "binkc.exe" >nul || goto :gotit
if not exist "%TMPB%" goto :wait
for %%S in ("%TMPB%") do set cur=%%~zS
if not "%cur%"=="%last%" (set last=%cur%& goto :wait)
taskkill /f /im binkc.exe >nul 2>&1
:gotit
timeout /t 1 /nobreak >nul
if exist "%TMPB%" move /y "%TMPB%" "%~2" >nul
rd /s /q "%TMPD%" 2>nul
if exist "%~2" (echo OK %~1 >> "%LOG%") else (echo FAILED %~1 >> "%LOG%" & echo FAILED on %~1 - stopping.)
exit /b

:stop
echo Stopped after a failure - see %LOG%
pause
