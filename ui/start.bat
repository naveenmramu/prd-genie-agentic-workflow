@echo off
if not exist .venv ( python -m venv .venv )
call .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --port 8000
