"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_pivot_03.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SUMMARY")
ws.append(['config', 'drag', 'lift', 'moment'])
ws.append(['CFG-A', 25.625, 121.625, -6.875])
ws.append(['CFG-B', 32.75, 128.75, 0.25])
ws.append(['CFG-C', 38.625, 134.625, 6.125])
ws.append(['CFG-D', 45.75, 141.75, 13.25])
ws.append(['CFG-E', 51.625, 147.625, 19.125])
wb.save("output.xlsx")
