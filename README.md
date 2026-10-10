# CSV Cleaner — Python automation portfolio example

## Excel Cleaner V3 (.xlsx support)

The [Excel Cleaner V3](excel_cleaner_v3/README.md) complements the CSV cleaner. It processes Excel .xlsx workbooks, separates duplicates, flags missing values for review, and exports cleaned Excel and CSV files plus a report. The folder includes a fictional sample generator, example outputs and tests.


A **phone-friendly Python tool** that turns a messy CSV into a cleaned CSV plus an audit trail. No external packages, APIs, laptop display, or paid services are required.

## What this demo does

- Trims leading and trailing whitespace in every cell.
- Collapses repeated spaces in `Name`, `First Name`, `Last Name`, and `City` columns.
- Converts values in an `Email`/`Email Address`/`E-mail` column to lowercase.
- Removes fully blank records.
- Detects duplicate non-empty email values; if email is missing, compares whole records instead.
- Exports **cleaned**, **duplicate**, and **rejected/malformed** records separately, plus a JSON summary.
- Supports UTF-8 CSV files, including ones with a byte-order mark (BOM).

### Important limits

Only `.csv` is supported, not `.xlsx` or `.xls`. Duplicates with the same email are considered duplicates even if other fields differ; the earliest occurrence is retained, and all later matching records can be reviewed in the duplicates file. No email validity checks or automatic merging of different records are performed. The tool does not upload client data to any service.

## Running on Android with Pydroid 3

1. Download and **extract** the ZIP onto your phone.
2. In **Pydroid 3**, open the extracted `clean_csv.py` file (not a temporary untitled tab).
3. Confirm `sample_customers.csv` is in the **same folder** as `clean_csv.py`.
4. Tap **Run**. There is nothing to install with pip.
5. Open the `output` subfolder for the results.

To clean another CSV, copy it into this folder and change the value of `INPUT_FILENAME` near the top of `clean_csv.py` to that file's exact name. Re-run. On a computer you can also run `python clean_csv.py your_file.csv`.

If Android prevents the app from accessing the Downloads folder, move both files to a directory Pydroid 3 is allowed to access, then open the script from that location. Check Pydroid 3 file-access permissions in Android settings.

## Output files for `sample_customers.csv`

- `output/sample_customers_cleaned.csv` — cleaned data, suitable for opening in Excel or Sheets
- `output/sample_customers_duplicates.csv` — excluded duplicate records and the record each matched
- `output/sample_customers_rejected.csv` — rows with the wrong number of columns
- `output/sample_customers_report.json` — summary counts

The `output` folder included in this package shows **sample results already generated and tested**, so you can inspect the results before running anything.

## How to offer this as a service

Suggested listing: **"I will clean and de-duplicate your CSV customer or inventory data with Python"**.

Ask a prospective client:
1. Is the file CSV or Excel? This version can only handle **CSV**.
2. Which column(s) define a duplicate (email, order ID, or exact row)? This sample uses email; other rules need custom work.
3. Do you want to keep the first record or merge updates? This version keeps the first.
4. Which exact formatting changes should be made?
5. What final deliverables and deadline do you want?

Always confirm requirements and scope before quoting. Test a copy of the dataset and verify outputs with the client; don't silently alter important fields. Avoid taking on sensitive personal/customer data without appropriate permissions and safe handling.

## Portfolio summary

> Built a Python CSV cleanup utility that standardizes basic fields, removes duplicate records, and generates an audit report. Tested with synthetic customer records and designed to run on Android using Pydroid 3.

This is an example project, **not evidence of previous paid client work**. Review, test, and understand the code before offering it to clients.