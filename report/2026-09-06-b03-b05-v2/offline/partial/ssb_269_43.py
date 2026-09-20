"""oracle — copy init workbook, write embedded golden answer-region values."""
import datetime as _dt
import json
import openpyxl

VALUES = [
    (1, 1, "XXMTKGMA"),
    (1, 2, 2010022),
    (1, 8, "2022/01/26"),
    (1, 9, 14862.42),
    (2, 1, "XXMRKAMA"),
    (2, 2, 2010023),
    (2, 8, "2022/02/14"),
    (2, 9, 20832.33),
    (3, 1, "XXMTKGMB"),
    (3, 2, 2010024),
    (3, 8, "2022/02/15"),
    (3, 9, 13923.56),
    (4, 1, "XXERK1MK"),
    (4, 2, 2010025),
    (4, 8, "2022/04/14"),
    (4, 9, 23528.95),
    (5, 1, "XXERK1MG"),
    (5, 2, 2010025),
    (5, 8, "2022/04/14"),
    (5, 9, 22557.38),
]


def _v(x):
    if isinstance(x, dict) and "__date__" in x:
        return _dt.datetime.strptime(x["__date__"], "%Y-%m-%d %H:%M:%S") \
            if len(x["__date__"]) > 10 else _dt.datetime.strptime(x["__date__"], "%Y-%m-%d")
    return x


wb = openpyxl.load_workbook("ssb_269_43_init.xlsx")
ws = wb["Sheet1"] if "Sheet1" in wb.sheetnames else wb.worksheets[0]
for cells in ws['A1:I7']:
    for cell in cells:
        if not isinstance(cell, openpyxl.cell.cell.MergedCell):
            cell.value = None
for row, col, v in VALUES:
    ws.cell(row=row, column=col).value = _v(v)
wb.save("output.xlsx")

import openpyxl
w=openpyxl.load_workbook("output.xlsx")
s=w['Sheet1']
initial=openpyxl.load_workbook('ssb_269_43_init.xlsx')
for coordinate in ['A4', 'B4', 'H4', 'I4', 'A5']:
    s[coordinate]=initial['Sheet1'][coordinate].value
initial.close()
w.save("output.xlsx")
w.close()
