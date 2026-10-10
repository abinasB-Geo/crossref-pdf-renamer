# Crossref PDF Renamer + BibTeX Generator

A Windows desktop utility for identifying academic research PDFs through [Crossref](https://www.crossref.org/), renaming them using publication metadata, and saving a BibTeX reference file beside each renamed PDF.

## Features

- Select multiple PDF files through a Windows file-selection dialog.
- Set a maximum number of PDFs to process in one batch.
- Search the first five pages of each PDF for a DOI.
- If a DOI is found, look up the publication record directly through Crossref.
- If no DOI is found, enter a DOI or search by title.
- Review possible Crossref matches and select the correct publication record.
- Preview proposed PDF and BibTeX filenames before making changes.
- Rename selected PDFs using the first author's name, publication year, and title (the title is limited to the first 100 characters).
- Retrieve BibTeX from Crossref and save it beside the renamed PDF.
- Avoid overwriting existing PDF and BibTeX files by choosing unique filenames when necessary.
- Save a CSV log of the rename and BibTeX operations.
- Cache Crossref responses locally to reduce repeated requests.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or later recommended
- Internet connection for Crossref lookups and BibTeX retrieval

The program uses these Python packages:

- `requests` — sends requests to Crossref.
- `PyMuPDF` (`pymupdf`) — reads PDF text and searches for DOI strings.
- `tkinterdnd2` — included in the supplied requirements file; the current script's primary file-selection workflow uses Tkinter's file dialog.
- `pyinstaller` — optional, for packaging the script as a Windows executable.

**Tkinter** is normally included with the standard Windows installation of Python. If Tkinter is missing, repair/reinstall Python with the Tcl/Tk support option enabled.

## Folder layout

Keep the Python script, requirements file, and batch file together in the same folder:

```text
CrossrefPDFRenamer/
├── crossref_pdf_renamer.py
├── requirements.txt
├── run_crossref_renamer.bat
└── README.md
```

The batch file should be named `run_crossref_renamer.bat` (or another `.bat` name of your choice). It changes to its own directory, installs the packages listed in `requirements.txt`, and launches the program.

> **Important:** The batch file uses `requirements.txt` (plural). Name the dependency file exactly `requirements.txt`, not `requirement.txt`, unless you also change the batch file to match.

## Installation and launch

### Option 1 — Run using the batch file

1. Install Python from [python.org](https://www.python.org/downloads/windows/). During installation, enable **Add Python to PATH**.
2. Make sure the files are arranged as shown above.
3. Double-click the `.bat` file.
4. The batch file installs or updates the listed packages, then starts the GUI.
5. If installation fails, the batch file displays an error and pauses so you can read it.

The supplied batch file:

```bat
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
```

### Option 2 — Run from Command Prompt

Open Command Prompt in the program folder and run:

```bat
python -m pip install -r requirements.txt
python crossref_pdf_renamer.py
```

If `python` is not recognized, try the Windows Python launcher:

```bat
py -m pip install -r requirements.txt
py crossref_pdf_renamer.py
```

## Configure your Crossref email

The script contains this setting near the top:

```python
EMAIL_ID_DEFAULT = "your.email@example.com"
```

Replace the example address with an email address you use:

```python
EMAIL_ID_DEFAULT = "your.name@example.com"
```

The GUI also displays an **Email** field, where you can edit the address before processing. Supplying a real email helps Crossref identify the client making requests. Do not put passwords or API keys in this field.

## How to use the program

1. Launch the application.
2. Enter your email address in the **Crossref settings** section.
3. Set **Maximum PDFs** to the number of files you want to process in this batch.
4. Click **Select PDF Files** and choose the research papers. The selection is limited by the maximum number configured in the GUI.
5. Click **Start Processing**.
6. For PDFs with a detectable DOI, the program attempts to retrieve the Crossref record automatically.
7. If a DOI cannot be found or used, follow the prompts to enter a DOI or search by title, then select the correct Crossref candidate when prompted.
8. Review the **Rename + BibTeX Preview** table. Check the original PDF name, proposed PDF name, DOI, and BibTeX filename.
9. Select the rows you want to process. The preview initially selects all matched rows.
10. Click **Rename + Generate BibTeX** to rename the selected PDFs and retrieve their BibTeX records.
11. Read the completion message and inspect the CSV log for the recorded outcomes.

**Review the preview carefully before confirming.** Crossref metadata may be incomplete or may match a different edition or version of a paper. Check the DOI, title, author, and year before renaming important files.

## Output files

### Renamed PDFs

PDFs are renamed in their existing folders. The proposed filename follows this pattern:

```text
FirstAuthor - Year - First 100 characters of title.pdf
```

Characters that Windows does not allow in filenames are cleaned by the script. If a destination filename already exists, the program uses a unique name rather than intentionally overwriting the existing file.

### BibTeX files

A BibTeX file is saved beside each processed PDF, using a name based on the first author's name and year, for example:

```text
Smith2021.bib
```

If a BibTeX filename already exists, the program generates a unique alternative. The BibTeX content is retrieved from Crossref's content-negotiation/Transform service, so availability and completeness depend on Crossref and the DOI record.

### CSV log

The program writes `crossrefRenameLog.csv` in the folder containing the first selected PDF. It appends new rows to an existing log rather than replacing it.

The log records fields such as:

- Original and new PDF paths/names
- DOI
- Author, year, and title
- Matching method
- PDF rename status
- BibTeX path and status

If a batch contains PDFs from several folders, the log is still written to the folder of the first selected PDF.

### Crossref cache

The program also uses `crossref_cache.json` to cache Crossref responses and reduce repeat lookups. The script determines the cache location; keep the file with the program's other working files when practical, and do not delete it while the program is running.

## Optional: build a Windows executable

PyInstaller is included in the requirements file. To build a one-folder distribution, open Command Prompt in the program folder and run:

```bat
python -m PyInstaller --onedir --windowed --name CrossrefPDFRenamer crossref_pdf_renamer.py
```

The application will be placed under:

```text
dist\CrossrefPDFRenamer\
```

Test the executable on a small set of copied PDFs before using it on your main research library. Depending on the target computer and Python environment, additional packaging adjustments may be needed. The executable does not remove the need for an internet connection for Crossref requests.

## Safety and good practice

- Back up your PDFs before the first large batch.
- Test the program on copies of a few papers first.
- Confirm each Crossref candidate before renaming.
- Do not edit or move source PDFs while the program is processing them.
- Avoid running two copies of the program against the same files at the same time.
- Keep the CSV log as an audit trail; it records outcomes but should not be treated as a backup.
- Crossref cannot guarantee a match for every paper, especially records with missing, incorrect, or non-Crossref DOIs.

## Troubleshooting

### `python` is not recognized

Reinstall Python and enable **Add Python to PATH**, or use `py` instead of `python` in the batch file and commands.

### `requirements.txt` cannot be found

Make sure the dependency file is named exactly `requirements.txt` and is in the same folder as the batch file. The batch file uses `%~dp0` to switch to its own folder before running commands.

### Package installation fails

Check your internet connection and run the installation command in Command Prompt to read the full error:

```bat
python -m pip install -r requirements.txt
```

### Crossref does not return a result

Check the DOI spelling, try searching by the full paper title, and inspect the candidate metadata. Some publications may not be indexed by Crossref or may have incomplete metadata.

### A PDF was not renamed

Review the completion dialog and `crossrefRenameLog.csv`. Confirm that the file is not open in another program, that the folder is writable, and that the file still exists at the original path.

## Dependencies file

A suitable `requirements.txt` for the supplied batch file is:

```text
requests
pymupdf
tkinterdnd2>=0.4.3
pyinstaller>=6.0
```

`pyinstaller` is only needed if you intend to build an executable. The `.bat` file installs every package listed in this file, including PyInstaller.
