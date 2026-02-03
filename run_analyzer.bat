@echo off
REM OpenType Font Analyzer Launcher
REM Run this to start the GUI application

echo Starting OpenType Font Analyzer...
python font_analyzer_ui.py

if errorlevel 1 (
    echo.
    echo Error running the application. Make sure Python is installed and all dependencies are available.
    echo Required files: ttxread.py, ttxfont.py, ttxtables.py
    echo.
    pause
)