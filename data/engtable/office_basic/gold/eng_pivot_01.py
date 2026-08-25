"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_pivot_01.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SUMMARY")
ws.append(['config', 'drag', 'lift', 'moment'])
ws.append(['CFG-A', 24.625, 120.625, -7.875])
ws.append(['CFG-B', 31.75, 127.75, -0.75])
ws.append(['CFG-C', 37.625, 133.625, 5.125])
wb.save("output.xlsx")
