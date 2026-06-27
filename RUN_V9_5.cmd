@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Izbushka YML Generator V9.5
echo Starting generator...
echo.
py -X utf8 -u "%~dp0run_v9_5.py"
echo.
echo ==========================================
echo The process has stopped or finished.
echo ==========================================
pause
