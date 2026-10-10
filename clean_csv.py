"""Phone-friendly CSV cleaning utility. Uses Python's standard library only.

Open this saved file in Pydroid 3 and tap Run. Put the input CSV next to it.
Optional on a computer: python clean_csv.py my_file.csv
"""

import csv
import json
import re
import sys
from pathlib import Path

# Edit only this line when using Pydroid 3 with another input file.
INPUT_FILENAME = "sample_customers.csv"


def tidy_cell(value, header):
    """Apply conservative cleanup; avoid changing IDs, phone numbers or notes."""
    value = value.strip()
    field = header.strip().casefold()
    if field in {"name", "first name", "last name", "city"}:
        value = re.sub(r"\s+", " ", value)
    if field in {"email", "email address", "e-mail"}:
        value = value.casefold()
    return value


def clean_file(input_path):
    input_path = Path(input_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError("Input CSV not found: " + str(input_path))
    if input_path.suffix.lower() != ".csv":
        raise ValueError("This version supports .csv files only (not .xlsx).")

    output_dir = input_path.parent / "output"
    output_dir.mkdir(exist_ok=True)
    stem = input_path.stem
    cleaned_path = output_dir / (stem + "_cleaned.csv")
    duplicates_path = output_dir / (stem + "_duplicates.csv")
    rejected_path = output_dir / (stem + "_rejected.csv")
    report_path = output_dir / (stem + "_report.json")

    kept = []
    duplicates = []
    rejected = []
    seen = {}
    blank_rows = 0
    read_rows = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            raise ValueError("CSV is empty. Add a header row and at least one data row.")
        if not headers or any(not header for header in headers):
            raise ValueError("The header row contains an empty column name.")
        if len(set(h.casefold() for h in headers)) != len(headers):
            raise ValueError("Column names are repeated (ignoring case). Rename them first.")

        email_index = next((i for i, h in enumerate(headers)
                            if h.casefold() in {"email", "email address", "e-mail"}), None)
        for source_record, values in enumerate(reader, start=2):
            read_rows += 1
            if not values or all(not v.strip() for v in values):
                blank_rows += 1
                continue
            if len(values) != len(headers):
                rejected.append({
                    "source_record": source_record,
                    "issue": f"Expected {len(headers)} columns, found {len(values)}",
                    "raw_values": json.dumps(values, ensure_ascii=False),
                })
                continue

            values = [tidy_cell(value, header) for value, header in zip(values, headers)]
            if all(not value for value in values):
                blank_rows += 1
                continue
            if email_index is not None and values[email_index]:
                dedupe_key = ("email", values[email_index])
            else:
                dedupe_key = ("whole_row", tuple(values))
            row = dict(zip(headers, values))
            if dedupe_key in seen:
                duplicates.append({"source_record": source_record,
                                   "matches_record": seen[dedupe_key], **row})
            else:
                seen[dedupe_key] = source_record
                kept.append(row)

    def write_csv(path, fieldnames, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    write_csv(cleaned_path, headers, kept)
    write_csv(duplicates_path, ["source_record", "matches_record"] + headers, duplicates)
    write_csv(rejected_path, ["source_record", "issue", "raw_values"], rejected)

    report = {
        "input_file": input_path.name,
        "data_rows_read": read_rows,
        "cleaned_rows": len(kept),
        "duplicate_rows_removed": len(duplicates),
        "blank_rows_removed": blank_rows,
        "malformed_rows_rejected": len(rejected),
        "column_names": headers,
        "duplicate_rule": ("same non-empty email, otherwise identical full row"
                           if email_index is not None else "identical full row"),
        "notes": "Duplicate detection keeps the first occurrence. Inspect the duplicates and rejected files.",
    }
    with report_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)

    print("SUCCESS! CSV cleaning completed.")
    print("Input records:", read_rows)
    print("Cleaned records:", len(kept))
    print("Duplicates:", len(duplicates))
    print("Blank records:", blank_rows)
    print("Malformed records:", len(rejected))
    print("Results saved in:", output_dir)
    return report


if __name__ == "__main__":
    script_folder = Path(__file__).resolve().parent
    file_arg = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILENAME
    chosen_input = Path(file_arg)
    if not chosen_input.is_absolute():
        chosen_input = script_folder / chosen_input
    try:
        clean_file(chosen_input)
    except (FileNotFoundError, ValueError, UnicodeError, OSError, csv.Error) as error:
        print("ERROR:", error)
        print("Check that your CSV is UTF-8 and stored next to clean_csv.py.")