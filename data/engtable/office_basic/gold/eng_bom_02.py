"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("eng_bom_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet("BOM")
ws.append(['part_no', 'desc', 'qty_total', 'unit'])
ws.append(['P-1001', 'bracket', 6, 'pcs'])
ws.append(['P-1002', 'fastener', 21, 'pcs'])
ws.append(['P-1003', 'gusset', 8, 'pcs'])
ws.append(['P-1004', 'spacer', 6, 'pcs'])
ws.append(['P-1005', 'rib', 21, 'pcs'])
wb.save("output.xlsx")
