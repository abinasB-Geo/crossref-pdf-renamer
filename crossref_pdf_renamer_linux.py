# -*- coding: utf-8 -*-

"""
===============================================================
 Crossref Research PDF Renamer + BibTeX Generator
===============================================================

Workflow
--------

1. Select PDF files using Windows Explorer.
2. Maximum number of PDFs per batch can be set in GUI.
3. Search first 5 pages of each PDF for DOI.
4. If DOI is found:
       -> Query Crossref directly.
5. If DOI is not found:
       -> Ask user for DOI OR title.
6. If title is entered:
       -> Search Crossref.
       -> Show candidate records.
       -> User selects correct record.
7. Generate proposed filename:

       FirstAuthor - Year - First 100 characters of title.pdf

8. Show complete rename preview.
9. User clicks "Rename + Generate BibTeX".
10. PDF is renamed.
11. BibTeX is retrieved from Crossref Transform API.
12. BibTeX is saved beside the renamed PDF:

       FirstAuthorYear.bib

13. Duplicate BibTeX names are handled safely.
14. A CSV log is saved:

       crossrefRenameLog.csv

===============================================================

Required packages:

    py -m pip install --upgrade requests pymupdf

Tkinter is normally included with standard Windows Python.
===============================================================
"""

import os
import sys
import subprocess
import re
import csv
import json
import time
import threading
import tkinter as tk

from tkinter import (
    ttk,
    filedialog,
    messagebox
)

from urllib.parse import quote

import requests
import pymupdf


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILES_DEFAULT = 25

REQUEST_TIMEOUT = 30

REQUEST_DELAY = 0.2

CACHE_FILENAME = "crossref_cache.json"

RENAME_LOG_FILENAME = "crossrefRenameLog.csv"

Email_ID= "your.email@example.com" # Default Email ID
# ============================================================
# GLOBALS
# ============================================================

selected_files = []

processing_results = []


# ============================================================
# DOI REGEX
# ============================================================

DOI_REGEX = re.compile(
    r"""
    (?:
        https?://(?:dx\.)?doi\.org/
        |
        doi\s*:\s*
    )?
    (
        10\.\d{4,9}/[-._;()/:A-Z0-9]+
    )
    """,
    re.IGNORECASE | re.VERBOSE
)


# ============================================================
# CACHE
# ============================================================

def get_cache_path():

    """
    Store cache in the same directory as this script/executable.
    """

    try:
        base = os.path.dirname(
            os.path.abspath(__file__)
        )
    except Exception:
        base = os.getcwd()

    return os.path.join(
        base,
        CACHE_FILENAME
    )


def load_cache():

    path = get_cache_path()

    if not os.path.exists(path):
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


cache = load_cache()


def save_cache():

    try:

        with open(
            get_cache_path(),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                cache,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            "Could not save cache:",
            e
        )


# ============================================================
# DOI CLEANING
# ============================================================

def clean_doi(doi):

    if not doi:
        return None

    doi = str(doi).strip()

    # Remove DOI URL
    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        doi,
        flags=re.IGNORECASE
    )

    # Remove DOI prefix
    doi = re.sub(
        r"^doi\s*:\s*",
        "",
        doi,
        flags=re.IGNORECASE
    )

    # Remove whitespace
    doi = re.sub(
        r"\s+",
        "",
        doi
    )

    # Remove punctuation accidentally captured
    doi = doi.rstrip(
        ".,;:)]}>\"'"
    )

    if re.match(
        r"^10\.\d{4,9}/\S+$",
        doi,
        re.IGNORECASE
    ):
        return doi

    return None


# ============================================================
# PDF DOI EXTRACTION
# ============================================================

def extract_doi_from_text(text):

    if not text:
        return None

    matches = DOI_REGEX.findall(
        text
    )

    for match in matches:

        doi = clean_doi(
            match
        )

        if doi:
            return doi

    return None


def extract_doi_from_pdf(pdf_path):

    """
    Search first 5 pages of PDF.

    PyMuPDF modern API:
        import pymupdf
        pymupdf.open()
    """

    try:

        doc = pymupdf.open(
            pdf_path
        )

        pages_to_check = min(
            5,
            len(doc)
        )

        text = ""

        for page_number in range(
            pages_to_check
        ):

            try:

                text += "\n" + doc[
                    page_number
                ].get_text()

            except Exception:
                pass

        doc.close()

        return extract_doi_from_text(
            text
        )

    except Exception as e:

        print(
            "PDF extraction error:",
            pdf_path,
            e
        )

        return None


# ============================================================
# CROSSREF HTTP REQUEST
# ============================================================

def crossref_request(
    url,
    params,
    email,
    accept=None
):

    headers = {
        "User-Agent":
            "CrossrefPDFRenamer/1.0 "
            f"(mailto:{email})"
    }

    if accept:

        headers[
            "Accept"
        ] = accept

    for attempt in range(4):

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            # Rate limit
            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                try:
                    wait_time = float(
                        retry_after
                    )
                except Exception:
                    wait_time = (
                        3 * (attempt + 1)
                    )

                time.sleep(
                    wait_time
                )

                continue

            # Temporary server error
            if response.status_code in (
                500,
                502,
                503,
                504
            ):

                time.sleep(
                    2 * (attempt + 1)
                )

                continue

            response.raise_for_status()

            time.sleep(
                REQUEST_DELAY
            )

            return response

        except requests.RequestException as e:

            if attempt == 3:
                raise

            time.sleep(
                2 * (attempt + 1)
            )

    return None


# ============================================================
# CROSSREF DOI METADATA
# ============================================================

def crossref_doi_lookup(
    doi,
    email
):

    doi = clean_doi(
        doi
    )

    if not doi:
        return None

    cache_key = (
        "DOI_METADATA:"
        + doi.lower()
    )

    if cache_key in cache:

        return cache[
            cache_key
        ]

    encoded_doi = quote(
        doi,
        safe=""
    )

    url = (
        "https://api.crossref.org/v1/works/"
        + encoded_doi
    )

    try:

        response = crossref_request(
            url,
            {
                "mailto": email
            },
            email
        )

        data = response.json()

        item = data.get(
            "message",
            {}
        )

        if item:

            cache[
                cache_key
            ] = item

            save_cache()

        return item

    except Exception as e:

        print(
            "Crossref DOI lookup failed:",
            doi,
            e
        )

        return None


# ============================================================
# CROSSREF TITLE SEARCH
# ============================================================

def crossref_title_search(
    query,
    email,
    rows=5
):

    query = query.strip()

    if not query:
        return []

    cache_key = (
        "TITLE_SEARCH:"
        + query.lower()
        + f":{rows}"
    )

    if cache_key in cache:

        return cache[
            cache_key
        ]

    try:

        response = crossref_request(
            "https://api.crossref.org/v1/works",
            {
                "query.bibliographic":
                    query,
                "rows":
                    rows,
                "mailto":
                    email
            },
            email
        )

        data = response.json()

        items = (
            data
            .get(
                "message",
                {}
            )
            .get(
                "items",
                []
            )
        )

        cache[
            cache_key
        ] = items

        save_cache()

        return items

    except Exception as e:

        print(
            "Crossref search failed:",
            e
        )

        return []


# ============================================================
# CROSSREF BIBTEX TRANSFORM
# ============================================================

def get_bibtex_from_doi(
    doi,
    email
):

    """
    Retrieve BibTeX for DOI using Crossref Transform API.

    The important header is:

        Accept: application/x-bibtex
    """

    doi = clean_doi(
        doi
    )

    if not doi:
        return None

    cache_key = (
        "BIBTEX:"
        + doi.lower()
    )

    if cache_key in cache:

        return cache[
            cache_key
        ]

    encoded_doi = quote(
        doi,
        safe=""
    )

    url = (
        "https://api.crossref.org/v1/works/"
        + encoded_doi
        + "/transform"
    )

    try:

        response = crossref_request(
            url,
            {
                "mailto": email
            },
            email,
            accept="application/x-bibtex"
        )

        bibtex = (
            response.text
            .strip()
        )

        if bibtex:

            cache[
                cache_key
            ] = bibtex

            save_cache()

            return bibtex

    except Exception as e:

        print(
            "BibTeX request failed:",
            doi,
            e
        )

    return None


# ============================================================
# CROSSREF METADATA
# ============================================================

def get_first_author(item):

    authors = item.get(
        "author",
        []
    )

    if not authors:

        return "UnknownAuthor"

    first = authors[0]

    family = first.get(
        "family"
    )

    if family:

        return family.strip()

    literal = first.get(
        "literal"
    )

    if literal:

        return literal.strip()

    return "UnknownAuthor"


def get_year(item):

    fields = [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created"
    ]

    for field in fields:

        date_info = item.get(
            field
        )

        if not date_info:
            continue

        parts = date_info.get(
            "date-parts",
            []
        )

        if parts and parts[0]:

            year = parts[0][0]

            if year:

                return str(
                    year
                )

    return "UnknownYear"


def get_title(item):

    titles = item.get(
        "title",
        []
    )

    if not titles:

        return "Untitled"

    return titles[0].strip()


# ============================================================
# FILENAME CLEANING
# ============================================================

def clean_filename_component(
    text
):

    if not text:

        return "Unknown"

    # Windows forbidden characters
    text = re.sub(
        r'[<>:"/\\|?*]',
        "",
        text
    )

    # Control characters
    text = re.sub(
        r"[\x00-\x1f]",
        "",
        text
    )

    # Newlines / tabs
    text = re.sub(
        r"[\r\n\t]+",
        " ",
        text
    )

    # Multiple spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = text.strip()

    # Windows does not like trailing period/space
    text = text.rstrip(
        ". "
    )

    return text


# ============================================================
# MAKE PDF FILENAME
# ============================================================

def make_new_filename(
    item
):

    author = clean_filename_component(
        get_first_author(item)
    )

    year = clean_filename_component(
        get_year(item)
    )

    title = clean_filename_component(
        get_title(item)
    )

    # --------------------------------------------------------
    # Maximum title length = 100 characters
    # --------------------------------------------------------

    if len(title) > 100:

        title = title[:100]

        # Don't cut a word in half
        if " " in title:

            title = title.rsplit(
                " ",
                1
            )[0]

    title = title.rstrip(
        " ."
    )

    return (
        f"{author} - "
        f"{year} - "
        f"{title}.pdf"
    )


# ============================================================
# UNIQUE PDF FILENAME
# ============================================================

def get_unique_path(
    directory,
    filename,
    reserved=None
):

    if reserved is None:

        reserved = set()

    reserved_lower = {
        x.lower()
        for x in reserved
    }

    base, ext = os.path.splitext(
        filename
    )

    candidate = filename

    counter = 1

    while (
        os.path.exists(
            os.path.join(
                directory,
                candidate
            )
        )
        or
        candidate.lower()
        in reserved_lower
    ):

        candidate = (
            f"{base} "
            f"({counter})"
            f"{ext}"
        )

        counter += 1

    reserved.add(
        candidate
    )

    return candidate


# ============================================================
# UNIQUE BIBTEX FILENAME
# ============================================================

def get_unique_bib_path(
    directory,
    author,
    year,
    reserved=None
):

    if reserved is None:

        reserved = set()

    reserved_lower = {
        x.lower()
        for x in reserved
    }

    base = (
        clean_filename_component(
            author
        )
        +
        clean_filename_component(
            year
        )
    )

    filename = (
        base
        + ".bib"
    )

    candidate = filename

    counter = 1

    while (
        os.path.exists(
            os.path.join(
                directory,
                candidate
            )
        )
        or
        candidate.lower()
        in reserved_lower
    ):

        candidate = (
            f"{base} "
            f"({counter})"
            ".bib"
        )

        counter += 1

    reserved.add(
        candidate
    )

    return os.path.join(
        directory,
        candidate
    )


# ============================================================
# SEARCH INPUT DIALOG
# ============================================================

class SearchInputDialog(
    tk.Toplevel
):
    # ============================================================
    # OPEN PDF WHILE TITLE SEARCH
    # ============================================================    
    def open_pdf(self):
        """Open the current PDF using the Windows default PDF viewer."""
        try:
            if os.path.isfile(self.pdf_path):
                if sys.platform.startswith("win"):
                    os.startfile(self.pdf_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", self.pdf_path])
                else:
                    subprocess.Popen(["xdg-open", self.pdf_path])
            else:
                messagebox.showerror(
                    "File not found",
                    f"PDF not found:\n{self.pdf_path}",
                    parent=self
                )
        except Exception as exc:
            messagebox.showerror(
                "Error",
                f"Could not open PDF:\n{exc}",
                parent=self
            )

    def __init__(
        self,
        parent,
        pdf_path
    ):
        


        super().__init__(
            parent
        )

        self.result = None
        
        self.pdf_path = pdf_path
        
        self.title(
            "DOI / Title Search"
        )

        self.geometry(
            "650x260"
        )

        self.resizable(
            False,
            False
        )

        self.transient(
            parent
        )

        self.grab_set()

        ttk.Label(
            self,
            text=(
                "DOI was not found in this PDF."
            ),
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        ).pack(
            pady=(15, 5)
        )

        ttk.Label(
            self,
            text=(
                "You can enter a DOI or the "
                "paper title."
            )
        ).pack(
            pady=5
        )

        ttk.Label(
            self,
            text=(
                "File: "
                + os.path.basename(
                    pdf_path
                )
            ),
            wraplength=600
        ).pack(
            pady=(0, 12)
        )

        self.entry = ttk.Entry(
            self,
            width=80
        )

        self.entry.pack(
            padx=20,
            pady=5
        )

        self.entry.focus_set()

        button_frame = ttk.Frame(
            self
        )

        button_frame.pack(
            pady=20
        )

        ttk.Button(
            button_frame,
            text="Search Crossref",
            command=self.submit
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Skip",
            command=self.cancel
        ).pack(
            side="left",
            padx=5
        )
        ttk.Button(
            button_frame,
            text="Open PDF",
            command=self.open_pdf
        ).pack(side="left", padx=5)

        self.bind(
            "<Return>",
            lambda e:
                self.submit()
        )

        self.bind(
            "<Escape>",
            lambda e:
                self.cancel()
        )

    def submit(self):

        value = (
            self.entry
            .get()
            .strip()
        )

        if not value:

            messagebox.showwarning(
                "Input required",
                "Enter a DOI or title.",
                parent=self
            )

            return

        self.result = value

        self.destroy()

    def cancel(self):

        self.result = None

        self.destroy()


# ============================================================
# CANDIDATE SELECTION DIALOG
# ============================================================

class CandidateDialog(
    tk.Toplevel
):

    def __init__(
        self,
        parent,
        pdf_path,
        candidates
    ):

        super().__init__(
            parent
        )

        self.result = None

        self.candidates = candidates

        self.title(
            "Select Crossref Record"
        )

        self.geometry(
            "1200x560"
        )

        self.transient(
            parent
        )

        self.grab_set()

        ttk.Label(
            self,
            text=(
                "Select the correct Crossref "
                "record:"
            ),
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        ).pack(
            pady=(10, 3)
        )

        ttk.Label(
            self,
            text=os.path.basename(
                pdf_path
            ),
            wraplength=1100
        ).pack(
            pady=(0, 10)
        )

        frame = ttk.Frame(
            self
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        columns = (
            "score",
            "year",
            "author",
            "title",
            "doi"
        )

        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "score": "Score",
            "year": "Year",
            "author": "Author",
            "title": "Title",
            "doi": "DOI"
        }

        widths = {
            "score": 80,
            "year": 70,
            "author": 170,
            "title": 560,
            "doi": 280
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[
                    column
                ]
            )

            self.tree.column(
                column,
                width=widths[
                    column
                ],
                anchor="w"
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=
                scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        for i, item in enumerate(
            candidates
        ):

            score = item.get(
                "score",
                ""
            )

            authors = item.get(
                "author",
                []
            )

            author = ""

            if authors:

                author = authors[0].get(
                    "family",
                    ""
                )

            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    (
                        f"{score:.2f}"
                        if isinstance(
                            score,
                            (
                                int,
                                float
                            )
                        )
                        else score
                    ),
                    get_year(item),
                    author,
                    get_title(item),
                    item.get(
                        "DOI",
                        ""
                    )
                )
            )

        if candidates:

            self.tree.selection_set(
                "0"
            )

        self.tree.bind(
            "<Double-1>",
            lambda e:
                self.confirm()
        )

        button_frame = ttk.Frame(
            self
        )

        button_frame.pack(
            pady=10
        )

        ttk.Button(
            button_frame,
            text="Use Selected",
            command=self.confirm
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(
            side="left",
            padx=5
        )

    def confirm(self):

        selected = (
            self.tree.selection()
        )

        if not selected:

            messagebox.showwarning(
                "No selection",
                "Select a Crossref record.",
                parent=self
            )

            return

        index = int(
            selected[0]
        )

        self.result = (
            self.candidates[
                index
            ]
        )

        self.destroy()

    def cancel(self):

        self.result = None

        self.destroy()


# ============================================================
# MAIN APPLICATION
# ============================================================

class Application(
    tk.Tk
):

    def __init__(self):

        super().__init__()

        self.title(
            "Crossref PDF Renamer + BibTeX"
        )

        self.geometry(
            "1100x720"
        )

        self.minsize(
            900,
            600
        )

        self.email = ""

        self.create_widgets()

    # --------------------------------------------------------
    # GUI
    # --------------------------------------------------------

    def create_widgets(self):

        ttk.Label(
            self,
            text=(
                "Crossref Research PDF "
                "Renamer + BibTeX"
            ),
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        ).pack(
            pady=(15, 3)
        )

        ttk.Label(
            self,
            text=(
                "DOI extraction → Crossref → "
                "Rename PDF → Generate BibTeX"
            )
        ).pack(
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # Settings
        # ----------------------------------------------------

        settings = ttk.LabelFrame(
            self,
            text="Crossref settings"
        )

        settings.pack(
            fill="x",
            padx=15,
            pady=5
        )

        ttk.Label(
            settings,
            text="Email:"
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=10
        )

        self.email_entry = ttk.Entry(
            settings,
            width=45
        )

        self.email_entry.grid(
            row=0,
            column=1,
            padx=5
        )
        # ----------------------------------------------------
        # Default email for Crossref polite access
        # ----------------------------------------------------
        self.email_entry.insert(
            0,
            Email_ID
        )

        ttk.Label(
            settings,
            text="Maximum PDFs:"
        ).grid(
            row=0,
            column=2,
            padx=(30, 5)
        )

        self.max_spin = ttk.Spinbox(
            settings,
            from_=1,
            to=100,
            width=6
        )

        self.max_spin.grid(
            row=0,
            column=3
        )

        self.max_spin.set(
            MAX_FILES_DEFAULT
        )

        # ----------------------------------------------------
        # File list
        # ----------------------------------------------------

        file_frame = ttk.LabelFrame(
            self,
            text="Selected PDFs"
        )

        file_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=8
        )

        list_frame = ttk.Frame(
            file_frame
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        self.file_list = tk.Listbox(
            list_frame,
            font=(
                "Consolas",
                10
            )
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.file_list.yview
        )

        self.file_list.configure(
            yscrollcommand=
                scrollbar.set
        )

        self.file_list.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        button_frame = ttk.Frame(
            file_frame
        )

        button_frame.pack(
            pady=5
        )

        ttk.Button(
            button_frame,
            text="Select PDF Files",
            command=self.select_files
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_files
        ).pack(
            side="left",
            padx=5
        )

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.process_button = ttk.Button(
            self,
            text=(
                "Start Processing"
            ),
            command=self.start_processing
        )

        self.process_button.pack(
            pady=8
        )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        self.progress = ttk.Progressbar(
            self,
            mode="determinate"
        )

        self.progress.pack(
            fill="x",
            padx=20
        )

        self.status_var = tk.StringVar(
            value="Ready."
        )

        ttk.Label(
            self,
            textvariable=self.status_var
        ).pack(
            anchor="w",
            padx=20,
            pady=5
        )

    # --------------------------------------------------------
    # Select files
    # --------------------------------------------------------

    def select_files(self):

        try:

            maximum = int(
                self.max_spin.get()
            )

        except Exception:

            maximum = (
                MAX_FILES_DEFAULT
            )

        files = (
            filedialog.askopenfilenames(
                title=(
                    "Select research PDFs"
                ),
                filetypes=[
                    (
                        "PDF files",
                        "*.pdf"
                    )
                ]
            )
        )

        if not files:
            return

        if len(files) > maximum:

            messagebox.showwarning(
                "Too many PDFs",
                (
                    f"You selected "
                    f"{len(files)} PDFs.\n\n"
                    f"Maximum allowed: "
                    f"{maximum}"
                ),
                parent=self
            )

            return

        global selected_files

        selected_files = list(
            files
        )

        self.file_list.delete(
            0,
            tk.END
        )

        for path in selected_files:

            self.file_list.insert(
                tk.END,
                path
            )

        self.status_var.set(
            f"{len(selected_files)} PDF(s) selected."
        )

    # --------------------------------------------------------
    # Clear
    # --------------------------------------------------------

    def clear_files(self):

        global selected_files

        selected_files = []

        self.file_list.delete(
            0,
            tk.END
        )

        self.status_var.set(
            "Ready."
        )

    # --------------------------------------------------------
    # Start processing
    # --------------------------------------------------------

    def start_processing(self):

        if not selected_files:

            messagebox.showwarning(
                "No PDFs",
                "Select PDF files first.",
                parent=self
            )

            return

        email = (
            self.email_entry
            .get()
            .strip()
        )

        if not email:

            messagebox.showwarning(
                "Email required",
                (
                    "Please enter your email "
                    "address for Crossref "
                    "polite access."
                ),
                parent=self
            )

            return

        self.email = email

        self.process_button.config(
            state="disabled"
        )

        self.progress[
            "value"
        ] = 0

        thread = threading.Thread(
            target=self.process_files,
            daemon=True
        )

        thread.start()

    # --------------------------------------------------------
    # Process PDFs
    # --------------------------------------------------------

    def process_files(self):

        global processing_results

        processing_results = []

        total = len(
            selected_files
        )

        for number, pdf_path in enumerate(
            selected_files,
            start=1
        ):

            self.after(
                0,
                self.status_var.set,
                (
                    f"{number}/{total}: "
                    "Extracting DOI..."
                )
            )

            # ------------------------------------------------
            # Extract DOI
            # ------------------------------------------------

            doi = extract_doi_from_pdf(
                pdf_path
            )

            item = None

            method = ""

            # ------------------------------------------------
            # DOI found
            # ------------------------------------------------

            if doi:

                self.after(
                    0,
                    self.status_var.set,
                    (
                        f"{number}/{total}: "
                        f"DOI found: {doi}"
                    )
                )

                item = (
                    crossref_doi_lookup(
                        doi,
                        self.email
                    )
                )

                if item:

                    method = "PDF DOI"

                else:

                    item = (
                        self.manual_search(
                            pdf_path,
                            (
                                "DOI was found in "
                                "the PDF, but "
                                "Crossref did not "
                                "return metadata."
                            )
                        )
                        )

                    if item:
                        method = (
                            "Manual search"
                        )

            # ------------------------------------------------
            # DOI not found
            # ------------------------------------------------

            else:

                self.after(
                    0,
                    self.status_var.set,
                    (
                        f"{number}/{total}: "
                        "No DOI found."
                    )
                )

                item = (
                    self.manual_search(
                        pdf_path,
                        None
                    )
                )

                if item:

                    method = (
                        "Manual DOI/title"
                    )

            # ------------------------------------------------
            # Store result
            # ------------------------------------------------

            if item:

                final_doi = clean_doi(
                    item.get(
                        "DOI",
                        doi or ""
                    )
                )

                processing_results.append(
                    {
                        "source":
                            pdf_path,

                        "item":
                            item,

                        "doi":
                            final_doi or "",

                        "method":
                            method,

                        "status":
                            "Matched"
                    }
                )

            else:

                processing_results.append(
                    {
                        "source":
                            pdf_path,

                        "item":
                            None,

                        "doi":
                            doi or "",

                        "method":
                            "Skipped",

                        "status":
                            "Skipped"
                    }
                )

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            percent = (
                number /
                total *
                100
            )

            self.after(
                0,
                self.progress.configure,
                {"value": percent}
            )

        self.after(
            0,
            self.processing_finished
        )

    # --------------------------------------------------------
    # Manual DOI/title search
    # --------------------------------------------------------

    def manual_search(
        self,
        pdf_path,
        message
    ):

        result_holder = {
            "value": None
        }

        event = threading.Event()

        def show_input():

            if message:

                answer = (
                    messagebox.askyesno(
                        "Crossref lookup",
                        message
                        + "\n\n"
                        + "Search Crossref "
                        + "manually?",
                        parent=self
                    )
                )

                if not answer:

                    event.set()

                    return

            dialog = SearchInputDialog(
                self,
                pdf_path
            )

            self.wait_window(
                dialog
            )

            result_holder[
                "value"
            ] = dialog.result

            event.set()

        self.after(
            0,
            show_input
        )

        event.wait()

        query = (
            result_holder[
                "value"
            ]
        )

        if not query:

            return None

        # ----------------------------------------------------
        # User entered DOI
        # ----------------------------------------------------

        doi = clean_doi(
            query
        )

        if doi:

            self.after(
                0,
                self.status_var.set,
                (
                    "Searching DOI: "
                    + doi
                )
            )

            return (
                crossref_doi_lookup(
                    doi,
                    self.email
                )
            )

        # ----------------------------------------------------
        # User entered title
        # ----------------------------------------------------

        self.after(
            0,
            self.status_var.set,
            "Searching Crossref by title..."
        )

        candidates = (
            crossref_title_search(
                query,
                self.email,
                rows=5
            )
        )

        if not candidates:

            self.after(
                0,
                lambda:
                    messagebox.showinfo(
                        "No results",
                        (
                            "Crossref returned "
                            "no results."
                        ),
                        parent=self
                    )
            )

            return None

        # ----------------------------------------------------
        # Candidate selection
        # ----------------------------------------------------

        result_holder = {
            "item": None
        }

        event = threading.Event()

        def show_candidates():

            dialog = CandidateDialog(
                self,
                pdf_path,
                candidates
            )

            self.wait_window(
                dialog
            )

            result_holder[
                "item"
            ] = dialog.result

            event.set()

        self.after(
            0,
            show_candidates
        )

        event.wait()

        return result_holder[
            "item"
        ]

    # --------------------------------------------------------
    # Processing finished
    # --------------------------------------------------------

    def processing_finished(self):

        self.progress[
            "value"
        ] = 100

        self.status_var.set(
            "Metadata processing complete."
        )

        self.process_button.config(
            state="normal"
        )

        self.show_preview()

    # --------------------------------------------------------
    # Rename preview
    # --------------------------------------------------------

    def show_preview(self):

        matched = [
            result
            for result in processing_results
            if result["item"] is not None
        ]

        skipped = [
            result
            for result in processing_results
            if result["item"] is None
        ]

        if not matched:

            messagebox.showinfo(
                "No matches",
                "No PDFs were successfully matched.",
                parent=self
            )

            return

        preview = tk.Toplevel(
            self
        )

        preview.title(
            "Rename + BibTeX Preview"
        )

        preview.geometry(
            "1350x680"
        )

        preview.transient(
            self
        )

        ttk.Label(
            preview,
            text=(
                "Rename + BibTeX Preview"
            ),
            font=(
                "Segoe UI",
                15,
                "bold"
            )
        ).pack(
            pady=(10, 3)
        )

        ttk.Label(
            preview,
            text=(
                f"Matched: {len(matched)}    "
                f"Skipped: {len(skipped)}"
            )
        ).pack(
            pady=(0, 10)
        )

        frame = ttk.Frame(
            preview
        )
        # Live rename and BibTeX counter
        self.rename_counter_var = tk.StringVar(
            value="Ready: no files processed yet"
        )

        ttk.Label(
            preview,
            textvariable=self.rename_counter_var,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(0, 8))

        frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        columns = (
            "old",
            "new",
            "doi",
            "bib"
        )

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="extended"
        )

        tree.heading(
            "old",
            text="Current PDF"
        )

        tree.heading(
            "new",
            text="New PDF filename"
        )

        tree.heading(
            "doi",
            text="DOI"
        )

        tree.heading(
            "bib",
            text="BibTeX filename"
        )

        tree.column(
            "old",
            width=300
        )

        tree.column(
            "new",
            width=570
        )

        tree.column(
            "doi",
            width=250
        )

        tree.column(
            "bib",
            width=170
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(
            yscrollcommand=
                scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # Generate preview records
        # ----------------------------------------------------

        preview_records = []

        reserved_pdf_names = set()

        reserved_bib_names = set()

        for result in matched:

            source = result[
                "source"
            ]

            item = result[
                "item"
            ]

            doi = result[
                "doi"
            ]

            directory = os.path.dirname(
                source
            )

            # ----------------------------------------------
            # PDF filename
            # ----------------------------------------------

            proposed_pdf = (
                make_new_filename(
                    item
                )
            )

            new_pdf_filename = (
                get_unique_path(
                    directory,
                    proposed_pdf,
                    reserved_pdf_names
                )
            )

            # ----------------------------------------------
            # BibTeX filename
            # ----------------------------------------------

            author = (
                get_first_author(
                    item
                )
            )

            year = (
                get_year(
                    item
                )
            )

            bib_path = (
                get_unique_bib_path(
                    directory,
                    author,
                    year,
                    reserved_bib_names
                )
            )

            bib_filename = os.path.basename(
                bib_path
            )

            preview_records.append(
                {
                    "source":
                        source,

                    "directory":
                        directory,

                    "new_pdf":
                        new_pdf_filename,

                    "doi":
                        doi,

                    "item":
                        item,

                    "bib_path":
                        bib_path,

                    "bib_filename":
                        bib_filename,

                    "method":
                        result["method"]
                }
            )

            tree.insert(
                "",
                "end",
                values=(
                    os.path.basename(
                        source
                    ),

                    new_pdf_filename,

                    doi,

                    bib_filename
                )
            )

        # Select all by default
        tree.selection_set(
            tree.get_children()
        )

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        button_frame = ttk.Frame(
            preview
        )

        button_frame.pack(
            pady=10
        )

        ttk.Button(
            button_frame,
            text="Select All",
            command=lambda:
                tree.selection_set(
                    tree.get_children()
                )
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="Deselect All",
            command=lambda:
                tree.selection_remove(
                    tree.selection()
                )
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text=(
                "Rename + Generate BibTeX"
            ),
            command=lambda:
                self.rename_and_bibtex(
                    preview,
                    tree,
                    preview_records
                )
        ).pack(
            side="left",
            padx=20
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=preview.destroy
        ).pack(
            side="left",
            padx=5
        )

    # --------------------------------------------------------
    # Rename + BibTeX
    # --------------------------------------------------------

    def rename_and_bibtex(
        self,
        preview,
        tree,
        preview_records
    ):

        selected = (
            tree.selection()
        )

        if not selected:

            messagebox.showwarning(
                "Nothing selected",
                "Select at least one PDF.",
                parent=preview
            )

            return

        answer = (
            messagebox.askyesno(
                "Confirm operation",
                (
                    f"You are about to process "
                    f"{len(selected)} PDF(s).\n\n"
                    "For each selected PDF:\n\n"
                    "1. Rename the PDF\n"
                    "2. Retrieve BibTeX\n"
                    "3. Save the .bib beside it\n\n"
                    "Continue?"
                ),
                parent=preview
            )
        )

        if not answer:

            return

        # Map selected tree IDs to records
        children = (
            tree.get_children()
        )

        selected_indexes = set()

        for i, child in enumerate(
            children
        ):

            if child in selected:

                selected_indexes.add(
                    i
                )

        renamed = 0
        bibtex_created = 0
        errors = 0
        processed = 0

        log_rows = []

        total_selected = len(selected)

        self.rename_counter_var.set(
            f"Starting: 0/{total_selected} processed | "
            f"Renamed: 0 | BibTeX created: 0"
        )
        preview.update_idletasks()

        # ----------------------------------------------------
        # Process selected records
        # ----------------------------------------------------

        for i, record in enumerate(
            preview_records
        ):

            if i not in selected_indexes:

                continue

            source = record[
                "source"
            ]

            directory = record[
                "directory"
            ]

            new_pdf_filename = record[
                "new_pdf"
            ]

            destination = os.path.join(
                directory,
                new_pdf_filename
            )

            doi = record[
                "doi"
            ]

            item = record[
                "item"
            ]

            bib_path = record[
                "bib_path"
            ]

            bib_filename = record[
                "bib_filename"
            ]

            pdf_status = ""

            bib_status = ""

            # =================================================
            # RENAME PDF
            # =================================================

            try:

                # If source and destination are same
                if os.path.abspath(
                    source
                ) == os.path.abspath(
                    destination
                ):

                    pdf_status = (
                        "Already correct name"
                    )

                else:

                    # Never overwrite an existing PDF
                    if os.path.exists(
                        destination
                    ):

                        new_pdf_filename = (
                            get_unique_path(
                                directory,
                                new_pdf_filename
                            )
                        )

                        destination = os.path.join(
                            directory,
                            new_pdf_filename
                        )

                    os.rename(
                        source,
                        destination
                    )

                    renamed += 1

                    pdf_status = (
                        "Renamed"
                    )

            except Exception as e:

                pdf_status = (
                    f"ERROR: {e}"
                )

                errors += 1
                
            # Update live counter immediately after PDF rename attempt
            self.rename_counter_var.set(
                f"Processing {processed + 1}/{total_selected} | "
                f"Renamed: {renamed} | "
                f"BibTeX created: {bibtex_created}"
            )

            preview.update_idletasks()

            # =================================================
            # GET BIBTEX
            # =================================================

            # Use DOI from the same selected Crossref record
            bibtex = None

            if doi:

                self.status_var.set(
                    "Generating BibTeX: "
                    + doi
                )

                bibtex = (
                    get_bibtex_from_doi(
                        doi,
                        self.email
                    )
                )

            if bibtex:

                try:

                    # Avoid overwriting an existing .bib
                    if os.path.exists(
                        bib_path
                    ):

                        bib_path = (
                            get_unique_bib_path(
                                directory,
                                get_first_author(
                                    item
                                ),
                                get_year(
                                    item
                                )
                            )
                        )

                        bib_filename = (
                            os.path.basename(
                                bib_path
                            )
                        )

                    with open(
                        bib_path,
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(
                            bibtex
                        )

                    bibtex_created += 1

                    bib_status = (
                        "BibTeX created"
                    )

                except Exception as e:

                    bib_status = (
                        f"BibTeX ERROR: {e}"
                    )

                    errors += 1

            else:

                bib_status = (
                    "BibTeX retrieval failed"
                )

                errors += 1

            # =================================================
            # LOG
            # =================================================

            log_rows.append(
                {
                    "Original file":
                        source,

                    "New file":
                        destination,

                    "DOI":
                        doi,

                    "Author":
                        get_first_author(
                            item
                        ),

                    "Year":
                        get_year(
                            item
                        ),

                    "Title":
                        get_title(
                            item
                        ),

                    "Method":
                        record[
                            "method"
                        ],

                    "PDF status":
                        pdf_status,

                    "BibTeX file":
                        bib_path,

                    "BibTeX status":
                        bib_status
                }
            )
            # Update completed-file counter
            processed += 1

            self.rename_counter_var.set(
                f"Completed: {processed}/{total_selected} | "
                f"Renamed: {renamed} | "
                f"BibTeX created: {bibtex_created} | "
                f"Errors: {errors}"
            )

            preview.update_idletasks()

        # ----------------------------------------------------
        # Save CSV log
        # ----------------------------------------------------

        log_path = (
            self.save_rename_log(
                log_rows
            )
        )

        preview.destroy()

        self.status_var.set(
            (
                f"Completed: "
                f"{renamed} PDF(s), "
                f"{bibtex_created} BibTeX file(s)"
            )
        )

        messagebox.showinfo(
            "Operation complete",
            (
                f"PDFs renamed: "
                f"{renamed}\n\n"
                f"BibTeX files created: "
                f"{bibtex_created}\n\n"
                f"Errors: "
                f"{errors}\n\n"
                f"Log saved as:\n"
                f"{log_path}"
            ),
            parent=self
        )

    # --------------------------------------------------------
    # Save CSV log
    # --------------------------------------------------------

    def save_rename_log(
        self,
        rows
    ):

        # ----------------------------------------------------
        # Put log in the folder of the first selected PDF
        # ----------------------------------------------------

        if selected_files:

            log_directory = (
                os.path.dirname(
                    selected_files[0]
                )
            )

        else:

            log_directory = os.getcwd()

        log_path = os.path.join(
            log_directory,
            RENAME_LOG_FILENAME
        )

        fieldnames = [
            "Original file",
            "New file",
            "DOI",
            "Author",
            "Year",
            "Title",
            "Method",
            "PDF status",
            "BibTeX file",
            "BibTeX status"
        ]

        try:

            # Append if log already exists
            exists = os.path.exists(
                log_path
            )

            with open(
                log_path,
                "a",
                newline="",
                encoding="utf-8-sig"
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames
                )

                if not exists:

                    writer.writeheader()

                writer.writerows(
                    rows
                )

            return log_path

        except Exception as e:

            messagebox.showerror(
                "Log error",
                (
                    "Could not save rename log:\n"
                    + str(e)
                ),
                parent=self
            )

            return log_path


# ============================================================
# START APPLICATION
# ============================================================
if __name__ == "__main__":

    app = Application()

    app.mainloop()