"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_exceed_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("EXCEED")
ws.append(['event', 't_s', 'load_factor'])
ws.append(['E018', '2675.0', 2.35])
ws.append(['E012', '2450.0', 2.17])
ws.append(['E006', '2225.0', 1.99])
ws.append(['E000', '2000.0', 1.82])
ws.append(['E008', '2300.0', 1.8])
wb.save("output.xlsx")
