@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0code\week1_demo"
"..\..\env\.venv\Scripts\python.exe" demo_question.py
echo.
pause
