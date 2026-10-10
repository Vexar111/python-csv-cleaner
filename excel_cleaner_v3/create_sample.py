"""Generate the fictional Excel demo workbook for Excel Cleaner V3."""
from pathlib import Path
from openpyxl import Workbook

rows = [
    ["Name", "Email", "City", "Notes"],
    ["  Asha   Nair  ", "ASHA@EXAMPLE.COM", " Kochi ", "Online enquiry"],
    ["Rahul", "rahul@example.com", "Thiruvalla", "Confirmed"],
    ["Asha Nair", "asha@example.com", "Kochi", "Second enquiry"],
    ["Jiya", "jiya@example.com", "Kottayam", "New lead"],
    ["Nora", None, "Thiruvalla", "Walk-in"],
    ["Ravi", "ravi@example.com", "Alappuzha", "Interested"],
    [None, None, None, None],
    [None, "unknown@example.com", "Kollam", "Name not provided"],
]

workbook = Workbook()
sheet = workbook.active
sheet.title = "Customers"
for row in rows:
    sheet.append(row)

destination = Path(__file__).resolve().parent / "sample_customers.xlsx"
workbook.save(destination)
print("Created fictional sample:", destination)
