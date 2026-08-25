"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_pivot_04.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SUMMARY")
ws.append(['config', 'drag', 'lift', 'moment'])
ws.append(['CFG-A', 26.5, 122.5, -6.0])
ws.append(['CFG-B', 31.75, 127.75, -0.75])
ws.append(['CFG-C', 39.5, 135.5, 7.0])
wb.save("output.xlsx")
