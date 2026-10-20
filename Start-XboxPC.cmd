@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m xboxpc gui
) else (
    python -m xboxpc gui
)
if errorlevel 1 (
    echo Install Python 3.10 or later with Tkinter, then try again.
    pause
)
