"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_si_01.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SI")
ws.append(['run', 'force_n', 'length_mm', 'temp_c'])
ws.append(['RUN-01', 378.099, 63.5, 20.0])
ws.append(['RUN-02', 455.943, 82.55, 22.0])
ws.append(['RUN-03', 533.787, 101.6, 24.0])
ws.append(['RUN-04', 611.63, 120.65, 26.0])
ws.append(['RUN-05', 689.474, 139.7, 28.0])
ws.append(['RUN-06', 767.318, 158.75, 30.0])
ws.append(['RUN-07', 845.162, 177.8, 32.0])
ws.append(['RUN-08', 923.006, 196.85, 34.0])
wb.save("output.xlsx")
