@echo off
REM ─────────────────────────────────────────────────────────────
REM  MallNav - Start Server with Anthropic API Key
REM  Edit the line below with your actual API key, then double-click this file
REM ─────────────────────────────────────────────────────────────

set ANTHROPIC_API_KEY=your-api-key-here
REM Optionally override other settings:
REM set SECRET_KEY=your-secret-key
REM set DEBUG=True

cd /d "%~dp0"
echo Starting MallNav server...
echo API Key loaded from environment.
python manage.py runserver 0.0.0.0:8000
pause
