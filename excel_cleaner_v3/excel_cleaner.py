"""Excel customer-data cleaner for Android Pydroid 3 (requires openpyxl).

Put sample_customers.xlsx beside this script, then run in Pydroid 3.
It leaves the input file unchanged and writes results under excel_output/.
"""

import csv
import json
import re
import sys
from datetime import date, datetime, time
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# To clean your own workbook, change ONLY this filename.
INPUT_FILENAME = "sample_customers.xlsx"
SHEET_NAME = "Customers"  # Set to None to use the first sheet.


def as_text(value):
    """Avoid changes to the source workbook; treat cells as values, not code."""
    if value is None:
        return ""
    if isinstance(value, (date, datetime, time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def tidy(value, header):
    value = as_text(value).strip()
    field = header.casefold().strip()
    if field in {"name", "first name", "last name", "city"}:
        value = re.sub(r"\s+", " ", value)
    if field in {"email", "email address", "e-mail"}:
        value = value.casefold()
    return value


def process_rows(headers, numbered_rows):
    """Return cleaned rows, duplicates, review entries and counters."""
    headers = [as_text(h) for h in headers]
    if not headers or any(not h for h in headers):
        raise ValueError("The first row must contain non-empty column names.")
    if len({h.casefold() for h in headers}) != len(headers):
        raise ValueError("Duplicate column headings detected. Rename them first.")

    email_idx = next((i for i, h in enumerate(headers)
                      if h.casefold() in {"email", "email address", "e-mail"}), None)
    name_idx = next((i for i, h in enumerate(headers)
                     if h.casefold() in {"name", "full name"}), None)
    kept, duplicates, reviews, seen = [], [], [], {}
    blank_rows = 0
    total_rows = 0

    for excel_row, values in numbered_rows:
        total_rows += 1
        if len(values) != len(headers):
            reviews.append({"excel_row": excel_row, "reason": "Column count mismatch", "values": list(values)})
            continue
        row = [tidy(value, header) for value, header in zip(values, headers)]
        if not any(row):
            blank_rows += 1
            continue

        if email_idx is not None and row[email_idx]:
            key = ("email", row[email_idx])
        else:
            key = ("row", tuple(row))
        if key in seen:
            duplicates.append({"excel_row": excel_row, "matches_row": seen[key], "values": row})
            continue
        seen[key] = excel_row
        kept.append(row)
        reasons = []
        if name_idx is not None and not row[name_idx]:
            reasons.append("Missing name")
        if email_idx is not None and not row[email_idx]:
            reasons.append("Missing email (verify whether required)")
        if reasons:
            reviews.append({"excel_row": excel_row, "reason": "; ".join(reasons), "values": row})

    counts = {"input_data_rows": total_rows, "cleaned_rows": len(kept),
              "duplicates_removed": len(duplicates), "blank_rows_removed": blank_rows,
              "review_items": len(reviews)}
    return kept, duplicates, reviews, counts


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def write_cleaned_xlsx(path, headers, rows):
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Cleaned Data"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="163A5F")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(vertical="center")
    for col in sheet.columns:
        letter = col[0].column_letter
        width = min(38, max(13, max(len(str(cell.value or "")) for cell in col) + 2))
        sheet.column_dimensions[letter].width = width
    wb.save(path)


def clean_workbook(path):
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() != ".xlsx":
        raise ValueError("This version accepts .xlsx only (not .xls or .csv).")
    if not path.is_file():
        raise FileNotFoundError("Excel workbook not found: " + str(path))
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        if SHEET_NAME is not None and SHEET_NAME not in wb.sheetnames:
            raise ValueError("Sheet '" + SHEET_NAME + "' not found. Sheets: " + ", ".join(wb.sheetnames))
        sheet = wb[SHEET_NAME] if SHEET_NAME else wb.worksheets[0]
        row_iter = sheet.iter_rows(values_only=True)
        try:
            headers = [as_text(h) for h in next(row_iter)]
        except StopIteration:
            raise ValueError("This worksheet is empty.")
        kept, duplicates, reviews, counts = process_rows(headers, enumerate(row_iter, start=2))
        sheet_used = sheet.title
    finally:
        wb.close()

    out = path.parent / "excel_output"
    out.mkdir(exist_ok=True)
    stem = path.stem
    write_cleaned_xlsx(out / (stem + "_cleaned.xlsx"), headers, kept)
    write_csv(out / (stem + "_cleaned.csv"), headers, kept)
    write_csv(out / (stem + "_duplicates.csv"), ["excel_row", "matches_row"] + headers,
              [[d["excel_row"], d["matches_row"]] + d["values"] for d in duplicates])
    write_csv(out / (stem + "_needs_review.csv"), ["excel_row", "reason"] + headers,
              [[d["excel_row"], d["reason"]] + d["values"] for d in reviews])
    report = {"input_file": path.name, "sheet": sheet_used, **counts,
              "duplicate_rule": "Same nonempty email, otherwise identical row",
              "review_note": "Missing names/emails are flagged but retained; confirm fields with client",
              "important_limitations": ["Only .xlsx files", "First row must contain headers",
                "Uses stored results for formula cells; uncalculated formulas may appear blank",
                "Do not automatically trust all extracted data; review results before delivery"]}
    (out / (stem + "_report.json")).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("SUCCESS! Excel cleaning completed.")
    for key, count in counts.items():
        print(key.replace("_", " ").capitalize() + ":", count)
    print("Results saved in:", out)


if __name__ == "__main__":
    try:
        selected = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / INPUT_FILENAME
        clean_workbook(selected)
    except Exception as error:
        print("ERROR:", error)
        print("Check that sample_customers.xlsx is next to excel_cleaner.py and open this saved script in Pydroid 3.")
