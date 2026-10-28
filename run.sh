#!/usr/bin/env bash
# One-command start for macOS / Linux.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

echo "SylvaCast running at http://127.0.0.1:5000  (Ctrl+C to stop)"
python main.py
