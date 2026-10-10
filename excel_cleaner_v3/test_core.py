"""Basic checks of the Excel cleaner's processing logic."""
from excel_cleaner import process_rows

HEADERS = ["Name", "Email", "City", "Notes"]
ROWS = [
    (2, ["  Asha   Nair  ", "ASHA@EXAMPLE.COM", " Kochi ", "Online enquiry"]),
    (3, ["Rahul", "rahul@example.com", "Thiruvalla", "Confirmed"]),
    (4, ["Asha Nair", "asha@example.com", "Kochi", "Second enquiry"]),
    (5, ["Jiya", "jiya@example.com", "Kottayam", "New lead"]),
    (6, ["Nora", None, "Thiruvalla", "Walk-in"]),
    (7, ["Ravi", "ravi@example.com", "Alappuzha", "Interested"]),
    (8, [None, None, None, None]),
    (9, [None, "unknown@example.com", "Kollam", "Name not provided"]),
]
cleaned, duplicates, reviews, counts = process_rows(HEADERS, ROWS)
assert counts == {"input_data_rows": 8, "cleaned_rows": 6,
                  "duplicates_removed": 1, "blank_rows_removed": 1,
                  "review_items": 2}, counts
assert cleaned[0] == ["Asha Nair", "asha@example.com", "Kochi", "Online enquiry"]
assert duplicates[0]["excel_row"] == 4
assert any("Missing email" in r["reason"] for r in reviews)
assert any("Missing name" in r["reason"] for r in reviews)
print("PASS: cleaning, duplicates, and missing-value review rules")
