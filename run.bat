@echo off
REM One-command start for Windows.
cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    py -3 -m venv .venv || python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo SylvaCast running at http://127.0.0.1:5000  (Ctrl+C to stop)
python main.py
pause
