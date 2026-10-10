# Excel Cleaner V3 — Android / Pydroid 3

A phone-friendly Python tool for cleaning Excel **.xlsx** data. This is a portfolio demo with fictional customer records; it complements the CSV cleaner in the root of this repository.

## Features
- Trims whitespace and normalizes name, city, and email fields.
- Removes blank rows.
- Detects duplicate records using matching nonempty emails; otherwise compares full rows.
- Keeps the first occurrence and exports later duplicates for inspection.
- Flags missing names or emails without silently discarding those records.
- Exports a cleaned Excel workbook, a cleaned CSV, duplicate records, review items, and a JSON report.
- Never overwrites the input workbook.

## Run on an Android phone
1. Install Pydroid 3.
2. In Pydroid 3, install `openpyxl` with Pip.
3. Keep `excel_cleaner.py` and `sample_customers.xlsx` together in the same folder.
4. Open `excel_cleaner.py` and press Run.
5. Inspect the new `excel_output` folder.
6. For your own workbook, change `INPUT_FILENAME` near the top and set `SHEET_NAME` to the correct worksheet name (or `None` for the first sheet).

Optional PC execution: `python excel_cleaner.py path/to/file.xlsx`.

## Sample results
| Measure | Count |
|---|---:|
| Input data rows | 8 |
| Cleaned records | 6 |
| Duplicate records excluded | 1 |
| Blank rows removed | 1 |
| Records flagged for manual review | 2 |

The sample is fictional. The output worksheet is named **Cleaned Data**.

## Limitations
- Works on `.xlsx` files only, not legacy `.xls` workbooks, PDFs, or images.
- Uses the first row as headers.
- The default duplicate rule is email-based; agree on the rules with a client before applying them.
- Formula cells use saved/cached results. Uncalculated formulas may be blank.
- Numeric cells and dates may be converted into text; IDs, formatting, formulas, macros, and other source sheets are not preserved.
- This is a demonstration, not evidence of previously completed client projects.
- Never upload client/private customer data to public repositories. Verify outputs before delivery.

## Portfolio
- [Main repository — CSV cleaner](../README.md)
- [Python script](excel_cleaner.py)
- [Core tests](test_core.py)
