"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_si_04.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("SI")
ws.append(['run', 'force_n', 'length_mm', 'temp_c'])
ws.append(['RUN-01', 391.444, 63.5, 20.0])
ws.append(['RUN-02', 469.287, 82.55, 22.0])
ws.append(['RUN-03', 547.131, 101.6, 24.0])
ws.append(['RUN-04', 624.975, 120.65, 26.0])
ws.append(['RUN-05', 702.819, 139.7, 28.0])
ws.append(['RUN-06', 780.663, 158.75, 30.0])
ws.append(['RUN-07', 858.507, 177.8, 32.0])
ws.append(['RUN-08', 936.351, 196.85, 34.0])
ws.append(['RUN-09', 1014.195, 215.9, 36.0])
ws.append(['RUN-10', 1092.038, 234.95, 38.0])
ws.append(['RUN-11', 1169.882, 254.0, 40.0])
wb.save("output.xlsx")
