@echo off
cd /d "%~dp0"

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Installation failed.
    pause
    exit /b 1
)

python crossref_pdf_renamer.py
pause