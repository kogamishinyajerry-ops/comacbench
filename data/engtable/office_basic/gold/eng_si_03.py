"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_si_03.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SI")
ws.append(['run', 'force_n', 'length_mm', 'temp_c'])
ws.append(['RUN-01', 386.995, 63.5, 20.0])
ws.append(['RUN-02', 464.839, 82.55, 22.0])
ws.append(['RUN-03', 542.683, 101.6, 24.0])
ws.append(['RUN-04', 620.527, 120.65, 26.0])
ws.append(['RUN-05', 698.371, 139.7, 28.0])
ws.append(['RUN-06', 776.215, 158.75, 30.0])
ws.append(['RUN-07', 854.059, 177.8, 32.0])
ws.append(['RUN-08', 931.902, 196.85, 34.0])
ws.append(['RUN-09', 1009.746, 215.9, 36.0])
ws.append(['RUN-10', 1087.59, 234.95, 38.0])
wb.save("output.xlsx")
