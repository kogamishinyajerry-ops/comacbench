"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_bom_01.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("BOM")
ws.append(['part_no', 'desc', 'qty_total', 'unit'])
ws.append(['P-1001', 'bracket', 1, 'pcs'])
ws.append(['P-1002', 'fastener', 10, 'pcs'])
ws.append(['P-1003', 'gusset', 18, 'pcs'])
ws.append(['P-1004', 'spacer', 1, 'pcs'])
wb.save("output.xlsx")
