"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_pivot_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SUMMARY")
ws.append(['config', 'drag', 'lift', 'moment'])
ws.append(['CFG-A', 27.0, 123.0, -5.5])
ws.append(['CFG-B', 32.25, 128.25, -0.25])
ws.append(['CFG-C', 40.0, 136.0, 7.5])
ws.append(['CFG-D', 45.25, 141.25, 12.75])
wb.save("output.xlsx")
