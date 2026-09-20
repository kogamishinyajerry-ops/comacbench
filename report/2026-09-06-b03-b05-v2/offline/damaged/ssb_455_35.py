"""oracle — copy init workbook, write embedded golden answer-region values."""
import datetime as _dt
import json
import openpyxl

VALUES = [
    (1, 1, "Action"),
    (1, 2, "User"),
    (1, 3, "Date"),
    (1, 4, "Client"),
    (1, 5, "Packslip"),
    (1, 6, "PO Number"),
    (1, 7, "Quantity"),
    (1, 8, "Packsize"),
    (1, 9, "Extended Product Code"),
    (1, 10, "Bin Label"),
]


def _v(x):
    if isinstance(x, dict) and "__date__" in x:
        return _dt.datetime.strptime(x["__date__"], "%Y-%m-%d %H:%M:%S") \
            if len(x["__date__"]) > 10 else _dt.datetime.strptime(x["__date__"], "%Y-%m-%d")
    return x


wb = openpyxl.load_workbook("ssb_455_35_init.xlsx")
ws = wb["Worksheet1"] if "Worksheet1" in wb.sheetnames else wb.worksheets[0]
for cells in ws['A1:J10411']:
    for cell in cells:
        if not isinstance(cell, openpyxl.cell.cell.MergedCell):
            cell.value = None
for row, col, v in VALUES:
    ws.cell(row=row, column=col).value = _v(v)
wb.save("output.xlsx")

import openpyxl
w=openpyxl.load_workbook("output.xlsx")
s=w['Worksheet1']
s['A2']="__NEGATIVE_CONTROL_WRONG__"
w.save("output.xlsx")
w.close()
