@echo off
echo 🔧 Запуск форматирования кода...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python scripts\check_format.py
pause