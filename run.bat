@echo off
title Resume Maker Telegram Bot
cd /d "%~dp0"
echo ===================================================
echo        📄 Resume Maker Telegram Bot
echo ===================================================
echo.
echo Installing/Checking dependencies...
pip install -r requirements.txt
echo.
echo Starting bot...
python bot.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Bot encountered an error or stopped.
    pause
)

