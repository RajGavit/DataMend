# DataMend — Smart Spreadsheet Cleaner & Merger

**Clean your data. Connect your data. Make it useful.**

DataMend is a Python web application prototype for inspecting, cleaning, appending, and joining CSV and Excel spreadsheets. It uses Streamlit for the interface and Pandas for data processing.

## MVP features

- Upload CSV, XLSX, or XLSM files.
- Review dimensions, missing cells, duplicate rows, and per-column quality metrics.
- Choose cleaning rules: trim text, optionally standardize capitalization, remove duplicates, remove fully empty rows, and select a missing-value policy.
- Preview original and cleaned data before export.
- Append datasets by stacking rows and aligning columns by name.
- Join related datasets on selected key columns, with selectable join type and optional key relationship validation.
- Download output as CSV or Excel without overwriting original uploads.

## Technology

Python · Pandas · Streamlit · OpenPyXL

## Run locally (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## Project structure

```text
DataMend/
├── app.py
├── cleaner.py
├── merger.py
├── utils.py
├── requirements.txt
├── .gitignore
├── README.md
├── sample_data/
│   ├── students_part1.csv
│   ├── students_part2.csv
│   └── student_details.csv
└── tests/
    ├── test_cleaner.py
    └── test_merger.py
```

## Data-handling notes

- Cleaning functions return a new DataFrame; uploaded input is not mutated.
- Users should preview cleaning decisions and results.
- Appending uses the union of column names by default, so columns absent from a source file result in missing values.
- Join keys must be chosen carefully. Many-to-many joins can increase row counts; use validation when the intended key relationship is known.
- Title Case is a broad normalization and may not suit IDs, acronyms, or code columns.
- This prototype processes files in the active app session and does not store them in a database.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## References

- Pandas: https://pandas.pydata.org/docs/
- Streamlit: https://docs.streamlit.io/
- OpenPyXL: https://openpyxl.readthedocs.io/
