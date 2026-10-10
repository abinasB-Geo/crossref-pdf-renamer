# Crossref PDF Renamer
### A Practical Research-Paper Organization Tool for PhD Scholars and Researchers

**Stop losing research papers in your own computer. Spend less time searching and more time researching.**

## 1. Introduction: A Common Problem in Every Researcher's Life

During a PhD, researchers gradually accumulate hundreds or even thousands of research articles from journal websites, academic publishers, research databases, and institutional repositories. These papers are essential for literature reviews, research planning, methodology development, comparison of results, and thesis writing.

However, there is a frustrating problem that almost every research scholar encounters: **different publishers save their article PDFs using different, often meaningless filenames.**

For example, a downloaded research paper might be saved as:

- `S0169555X23001234.pdf`
- `1-s2.0-S0040195123004567-main.pdf`
- `article_987654.pdf`
- `download.pdf`
- `fulltext.pdf`

These filenames provide little or no useful information about the paper's author, publication year, or title. When your research library contains hundreds of such files, finding a particular article several months later can become a time-consuming and frustrating task.

Imagine remembering an important result from a paper you read last year but being unable to identify the corresponding PDF. You may have to open files one by one, search through multiple folders, or download the same article again simply because you cannot locate the original.

Over the course of a PhD, this small inconvenience can turn into a significant obstacle to an efficient research workflow.

**Crossref PDF Renamer was developed to address this problem by helping researchers give their academic PDFs meaningful, consistent, and recognizable filenames.**

## 2. What Is Crossref PDF Renamer?

Crossref PDF Renamer is a Windows desktop utility that identifies academic research papers using bibliographic metadata, retrieves publication information from the [Crossref database](https://www.crossref.org/), and renames PDF files according to a consistent naming convention.

The standard filename format is:

`First Author - Year - Article Title.pdf`

For example, an article with the first author Smith, published in 2021, might be saved as:

`Smith - 2021 - Numerical modelling of tectonic deformation.pdf`

The actual filename depends on the publication metadata returned by Crossref, and the title is limited to its first 100 characters. Characters that Windows does not permit in filenames are cleaned by the program.

Rather than manually renaming every article, researchers can select multiple PDFs, identify the corresponding publication records, review the proposed names, and process the selected files through a graphical interface.

The program can also retrieve a BibTeX reference for a matched publication and save it beside the corresponding PDF, helping researchers maintain both their article collection and bibliographic records.

## 3. How Does It Work?

Crossref PDF Renamer combines PDF text extraction, DOI identification, bibliographic lookup, manual verification, file renaming, and BibTeX retrieval in a single workflow.

### Step 1: Select research PDFs

Choose multiple PDF files from your computer using the Windows file-selection dialog. You can configure the maximum number of PDFs to process in a batch.

The selected files do not need to follow a common naming convention.

### Step 2: Extract the DOI

The program uses PyMuPDF to extract text from the first five pages of each PDF and search for a Digital Object Identifier (DOI).

A DOI is a persistent identifier assigned to many scholarly publications. When a DOI is found, the program attempts to retrieve the corresponding publication record directly from Crossref.

### Step 3: Identify articles without a detectable DOI

If the program cannot find or use a DOI, you can enter a DOI manually or search for the article using its title.

Crossref may return multiple possible matches. You can review the candidate publication records and select the one that corresponds to your PDF.

### Step 4: Preview proposed filenames

Before renaming files, the program displays a preview of the proposed changes. This allows you to inspect the available bibliographic information, including the title, author, year, DOI, and proposed PDF and BibTeX filenames.

You can select the matched records you want to process.

### Step 5: Rename PDFs

The selected PDFs are renamed using the standardized format:

`First Author - Year - First 100 characters of title.pdf`

The files remain in their existing folders. If a destination filename already exists, the program generates a unique alternative rather than intentionally overwriting the existing file.

### Step 6: Generate BibTeX references

The program attempts to retrieve BibTeX data from Crossref's content-negotiation/Transform service and save it beside the renamed PDF.

For example:

```text
Smith - 2021 - Numerical modelling of tectonic deformation.pdf
Smith2021.bib
```

The BibTeX filename is based on the first author's name and publication year. If a filename already exists, a unique alternative is generated.

### Step 7: Maintain a record of operations

The program records rename and BibTeX outcomes in `crossrefRenameLog.csv`. It also uses `crossref_cache.json` to cache Crossref responses and reduce repeated lookups.

This provides a useful record of completed operations and helps avoid unnecessary repeat requests to Crossref.

## 4. Key Features

- **Batch PDF processing:** Select multiple academic articles and process them in manageable batches.
- **DOI extraction:** Search the first five pages of a PDF for a DOI.
- **Crossref integration:** Retrieve publication metadata from Crossref using a DOI or title search.
- **Manual identification:** Enter a DOI, search by title, and choose the correct record when automatic identification is unsuccessful.
- **Filename standardization:** Rename articles using the first author's name, publication year, and title.
- **Filename preview:** Review proposed filenames before committing changes.
- **BibTeX retrieval:** Save a BibTeX reference beside a matched PDF when retrieval succeeds.
- **Duplicate-name protection:** Generate unique destination names to avoid intentionally overwriting existing files.
- **CSV logging:** Record rename operations, bibliographic information, and BibTeX outcomes.
- **Local caching:** Cache Crossref responses to reduce repeated lookups.
- **Graphical interface:** Perform the workflow through a Windows desktop GUI rather than manually editing filenames in File Explorer.

## 5. Why Is This Useful for PhD Scholars?

### Find articles by recognizable names

A filename containing the author, year, and title is much easier to recognize than a publisher-generated code. You can use Windows File Explorer's search and sorting features to locate papers more conveniently.

### Reduce unnecessary re-downloads

When you remember a paper's author or title but not its folder location, a meaningful filename makes it easier to find an existing copy. This can reduce duplicate downloads and unnecessary use of time and storage.

### Improve literature-review efficiency

Researchers often return to previously read papers while preparing literature reviews, writing journal manuscripts, comparing methodologies, or responding to reviewers. Consistently named PDFs make this process more manageable.

### Keep research files organized across publishers

Articles downloaded from different journals can follow the same naming convention, regardless of how the publishers originally named their PDFs.

### Support reference-management workflows

Saving BibTeX references alongside PDFs can make it easier to retrieve bibliographic details and transfer references into compatible reference-management workflows. The BibTeX output should still be checked for completeness and correctness.

### Build a more manageable digital research library

A well-organized collection of PDFs becomes increasingly valuable as a research project grows. Consistent filenames help make an existing collection easier to maintain over the long term.

## 6. Who Should Use It?

Crossref PDF Renamer can be useful for:

- PhD scholars and doctoral candidates
- Master's students undertaking research projects
- Postdoctoral researchers
- University faculty and academic staff
- Research scientists and laboratory personnel
- Anyone maintaining a large collection of scholarly PDFs

The tool is discipline-independent. It can support research in geology, geotechnical engineering, civil engineering, tectonics, environmental science, computer science, medicine, physics, chemistry, and other fields, provided the publications can be matched to suitable Crossref records.

## 7. System Requirements

The program is intended for Windows 10 and Windows 11.

Recommended environment:

- Python 3.10 or later
- Internet connection for Crossref metadata searches and BibTeX retrieval
- PyMuPDF for extracting PDF text
- Requests for making HTTP requests to Crossref
- Tkinter for the graphical user interface

The supplied dependency file may also include `tkinterdnd2` and PyInstaller. Tkinter is normally included with a standard Windows Python installation, while PyInstaller is only necessary if you intend to package the application as an executable.

## 8. Installation and Launch

Keep the following files together in one folder:

```text
CrossrefPDFRenamer/
├── crossref_pdf_renamer.py
├── requirements.txt
├── run_crossref_pdf_renamer_gui.bat
└── README.md
```

Install Python from [python.org](https://www.python.org/downloads/windows/) and enable the option to add Python to PATH during installation.

Make sure the dependency file is named `requirements.txt`, with the final **s**. The supplied batch file uses this exact filename.

A suitable dependency list is:

```text
requests
pymupdf
tkinterdnd2>=0.4.3
pyinstaller>=6.0
```

To launch the program, double-click `run_crossref_renamer.bat`, or open Command Prompt in the program folder and run:

```bat
python -m pip install -r requirements.txt
python crossref_pdf_renamer.py
```

If the `python` command is unavailable, try using `py` instead.

### Configure your Crossref email

The script contains an email setting:

```python
EMAIL_ID_DEFAULT = "your.email@example.com"
```

Replace the example address with your own email address, or enter your address in the application's Email field if available. This helps identify the client making Crossref requests. It is not a password or API key.

## 9. Understanding the Output Files

### Renamed PDF

The original PDF is renamed in its existing folder. The naming convention is:

`FirstAuthor - Year - First 100 characters of title.pdf`

The exact output depends on the metadata available for the matched publication.

### BibTeX file

The program attempts to save a BibTeX reference beside the renamed PDF. A typical filename is:

`Smith2021.bib`

BibTeX availability and completeness depend on the publication record and Crossref's service.

### CSV log

The program writes `crossrefRenameLog.csv` in the folder containing the first selected PDF. New entries are appended to an existing log rather than replacing it.

The log can record information such as:

- Original and new PDF names or paths
- DOI and publication metadata
- Matching method
- PDF rename status
- BibTeX filename and retrieval status

If the selected PDFs come from multiple folders, the log is still written to the folder of the first selected PDF.

### Crossref cache

The program uses `crossref_cache.json` to cache Crossref responses. This can reduce repeat lookups and make subsequent processing more efficient.

## 10. Optional: Build a Windows Executable

If you prefer to run Crossref PDF Renamer as a Windows desktop application without manually launching the Python script, the repository includes a `build_EXE.bat` file to automate the executable-building process.

### How to build the executable

1. Download or clone the GitHub repository to your Windows computer.
2. Ensure Python 3.10 is installed and available through the Python launcher.
3. Open the project folder containing `crossref_pdf_renamer.py` and `build_EXE.bat`.
4. Double-click `build_EXE.bat`.
5. Wait for the script to create a virtual environment, install the required packages, check the Python script for syntax errors, and build the application using PyInstaller.
6. After a successful build, locate the generated application inside the `dist` folder.

The batch file automatically performs the following operations:

- Creates a dedicated Python 3.10 virtual environment named `.venv`.
- Upgrades pip and installs `requests`, `pymupdf`, and `pyinstaller`.
- Checks the main Python script for syntax errors using `py_compile`.
- Builds a one-folder (`--onedir`) Windows application without a console window (`--windowed`).
- Collects the required PyMuPDF components and excludes unnecessary modules such as Matplotlib, SciPy, pandas, and NumPy to help reduce the packaged application's size.
- Cleans previous PyInstaller build artifacts before generating the new build.

### Important notes

- **Python 3.10 is required** by the supplied build script. Make sure it is installed before running the batch file.
- Keep `crossref_pdf_renamer.py` and `build_EXE.bat` in the same project folder.
- The output is a **one-folder application**, not a single standalone `.exe`. Distribute or move the complete generated application folder, including its supporting files.
- Crossref metadata searches and BibTeX retrieval require an internet connection.
- Test the built application using copies of a few PDFs before processing your main research library.

If the build fails, run `build_EXE.bat` from Command Prompt so that you can inspect the error messages.
Test the executable on a small set of copied PDFs before using it on your primary research library. Packaging may require additional adjustments depending on the computer and Python environment.

The program still requires an internet connection for Crossref lookups and BibTeX retrieval.

## 11. Important Limitations and Good Practices

Crossref PDF Renamer is an assistance tool for organizing research papers, not a guarantee of perfect metadata recognition.

- Some PDFs may not contain an extractable DOI in their first five pages.
- Some publications may not have a Crossref record or may have incomplete metadata.
- A title search can return multiple possible matches, including similar articles or different versions.
- BibTeX retrieval may fail even when publication metadata is available.
- The CSV log records operations but is not a backup of your PDFs.
- A unique filename prevents an intentional filename collision; it does not determine whether two different files contain the same article.

**Before processing a large collection, make a backup and test the program on a small number of copied PDFs.** Review the DOI, title, author, and publication year in the preview before confirming a batch operation.

## 12. The Bigger Picture: Less File Searching, More Research

A PhD already demands substantial time for reading, analysis, experiments, modelling, data interpretation, and academic writing. Researchers should not have to waste valuable hours trying to identify an article because its filename consists of meaningless characters.

Crossref PDF Renamer offers a practical way to make a growing collection of academic PDFs easier to recognize, locate, and manage. By combining DOI identification, Crossref metadata lookup, standardized filenames, BibTeX retrieval, and CSV logging, it brings several repetitive file-management tasks into one desktop workflow.

**Organize your research library once, maintain it consistently, and make it easier to find the papers you need when you need them.**

*Crossref PDF Renamer — because finding the research paper you already downloaded should not become another research problem.*

