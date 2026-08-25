"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_exceed_01.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("EXCEED")
ws.append(['event', 't_s', 'load_factor'])
ws.append(['E018', '2675.0', 2.08])
ws.append(['E012', '2450.0', 1.91])
ws.append(['E007', '2262.5', 1.8])
ws.append(['E017', '2637.5', 1.8])
wb.save("output.xlsx")
