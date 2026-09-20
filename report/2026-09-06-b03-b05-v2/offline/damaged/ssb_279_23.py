"""oracle — copy init workbook, write embedded golden answer-region values."""
import datetime as _dt
import json
import openpyxl

VALUES = [
    (3, 1, 1),
    (3, 2, "tig"),
    (4, 1, 2),
    (4, 2, "tig"),
    (5, 1, 3),
    (5, 2, "tib"),
    (6, 1, 4),
    (6, 2, "tig"),
    (7, 1, 5),
    (7, 2, "tig"),
    (8, 1, 6),
    (8, 2, "tib"),
    (9, 1, 7),
    (9, 2, "tig"),
    (10, 1, 8),
    (10, 2, "tig"),
    (11, 1, 9),
    (11, 2, "tib"),
    (12, 1, 10),
    (12, 2, "tig"),
    (17, 1, 1),
    (17, 2, "tig"),
    (18, 1, 2),
    (18, 2, "tig"),
    (19, 1, 3),
    (19, 2, "tib"),
    (20, 1, 4),
    (20, 2, "tig"),
    (21, 1, 5),
    (21, 2, "tig"),
    (22, 1, 6),
    (22, 2, "tib"),
    (23, 1, 7),
    (23, 2, "tig"),
    (24, 1, 8),
    (24, 2, "tig"),
    (25, 1, 9),
    (25, 2, "tib"),
    (26, 1, 10),
    (26, 2, "tig"),
]


def _v(x):
    if isinstance(x, dict) and "__date__" in x:
        return _dt.datetime.strptime(x["__date__"], "%Y-%m-%d %H:%M:%S") \
            if len(x["__date__"]) > 10 else _dt.datetime.strptime(x["__date__"], "%Y-%m-%d")
    return x


wb = openpyxl.load_workbook("ssb_279_23_init.xlsx")
ws = wb["Sheet1"] if "Sheet1" in wb.sheetnames else wb.worksheets[0]
for cells in ws['A3:B26']:
    for cell in cells:
        if not isinstance(cell, openpyxl.cell.cell.MergedCell):
            cell.value = None
for row, col, v in VALUES:
    ws.cell(row=row, column=col).value = _v(v)
wb.save("output.xlsx")

import openpyxl
w=openpyxl.load_workbook("output.xlsx")
s=w['Sheet1']
s['B3']="__NEGATIVE_CONTROL_WRONG__"
w.save("output.xlsx")
w.close()
