"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_si_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SI")
ws.append(['run', 'force_n', 'length_mm', 'temp_c'])
ws.append(['RUN-01', 382.547, 63.5, 20.0])
ws.append(['RUN-02', 460.391, 82.55, 22.0])
ws.append(['RUN-03', 538.235, 101.6, 24.0])
ws.append(['RUN-04', 616.079, 120.65, 26.0])
ws.append(['RUN-05', 693.923, 139.7, 28.0])
ws.append(['RUN-06', 771.766, 158.75, 30.0])
ws.append(['RUN-07', 849.61, 177.8, 32.0])
ws.append(['RUN-08', 927.454, 196.85, 34.0])
ws.append(['RUN-09', 1005.298, 215.9, 36.0])
wb.save("output.xlsx")
