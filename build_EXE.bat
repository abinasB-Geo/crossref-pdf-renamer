cd /d "%~dp0"

python -3.10 -m venv .venv
.venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install requests pymupdf pyinstaller
python -m py_compile crossref_pdf_renamer.py

pyinstaller --clean --noconfirm --onedir --windowed ^
  --name crossref_pdf_renamer ^
  --collect-all pymupdf ^
  --exclude-module matplotlib ^
  --exclude-module scipy ^
  --exclude-module pandas ^
  --exclude-module numpy ^
  crossref_pdf_renamer.py