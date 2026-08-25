"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_exceed_03.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("EXCEED")
ws.append(['event', 't_s', 'load_factor'])
ws.append(['E006', '2225.0', 2.26])
ws.append(['E000', '2000.0', 2.08])
ws.append(['E024', '2900.0', 1.91])
ws.append(['E009', '2337.5', 1.8])
ws.append(['E019', '2712.5', 1.8])
ws.append(['E018', '2675.0', 1.73])
wb.save("output.xlsx")
