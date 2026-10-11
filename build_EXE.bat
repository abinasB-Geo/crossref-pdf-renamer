@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto error

    .venv\Scripts\python.exe -m pip install --upgrade pip
    if errorlevel 1 goto error

    .venv\Scripts\python.exe -m pip install pymupdf requests pyinstaller
    if errorlevel 1 goto error
)

.venv\Scripts\python.exe -m PyInstaller ^
  --name crossref_pdf_renamer ^
  --collect-all pymupdf ^
  --exclude-module matplotlib ^
  --exclude-module scipy ^
  --exclude-module pandas ^
  --exclude-module numpy ^
  crossref_pdf_renamer.py

if errorlevel 1 goto error

echo.
echo BUILD SUCCESSFUL
echo Executable: dist\crossref_pdf_renamer\crossref_pdf_renamer.exe
pause
exit /b 0
