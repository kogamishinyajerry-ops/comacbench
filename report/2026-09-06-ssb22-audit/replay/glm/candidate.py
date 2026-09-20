import openpyxl
from datetime import datetime, date

SRC = 'ssb_22_47_init.xlsx'
DST = 'output.xlsx'

# Load twice: once to read cached/calculated values, once to preserve everything on save
wb_vals = openpyxl.load_workbook(SRC, data_only=True)
wb = openpyxl.load_workbook(SRC, data_only=False)

ws_v = wb_vals['sheet1'] if 'sheet1' in wb_vals.sheetnames else wb_vals.active
ws = wb['sheet1'] if 'sheet1' in wb.sheetnames else wb.active


def rd(r, c):
    """Read a cell value (prefer cached/calculated value over formula text)."""
    v = ws_v.cell(row=r, column=c).value
    if v is not None:
        return v
    return ws.cell(row=r, column=c).value


def is_blank(v):
    return v is None or (isinstance(v, str) and v.strip() == '')


def canon(v):
    """Canonical Excel-like key: case-insensitive text, normalized numbers."""
    if v is None:
        return ''
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        f = float(v)
        return str(int(f)) if f.is_integer() else repr(f)
    if isinstance(v, (datetime, date)):
        return str(v).casefold()
    return str(v).strip().casefold()


max_row = ws.max_row or 1

# ---- headers (row 1 of A:C) ----
hdr_keys = set()
for c in (1, 2, 3):
    k = canon(rd(1, c))
    if k != '':
        hdr_keys.add(k)
b1_key = canon(rd(1, 2))

# ---- read data rows from A2:C<max>: skip empties, headers, duplicate (B,C) pairs ----
rows = []
seen = set()
for r in range(2, max_row + 1):
    a = rd(r, 1)
    b = rd(r, 2)
    c = rd(r, 3)
    if is_blank(b):
        continue                        # skip empty cells / blank rows
    bk = canon(b)
    if bk in hdr_keys or bk == b1_key:  # skip header rows (even repeated ones)
        continue
    dk = (bk, canon(c))
    if dk in seen:                      # duplicates: identical B and C
        continue
    seen.add(dk)
    rows.append((a, b, c))

# ---- read helper list from column J (skip empties, headers, duplicates) ----
jnames = []
jseen = set()
for r in range(1, max_row + 1):
    v = rd(r, 10)
    if is_blank(v):
        continue
    k = canon(v)
    if k in hdr_keys:
        continue
    if k in jseen:
        continue
    jseen.add(k)
    jnames.append(k)

# ---- ordering ----
if jnames:
    # names listed in J come first, in J order; rows of the same name keep
    # their original source order (no sorting inside the group);
    # names not listed in J follow afterwards in original data order
    used = [False] * len(rows)
    result = []
    for jk in jnames:
        for i, row in enumerate(rows):
            if not used[i] and canon(row[1]) == jk:
                used[i] = True
                result.append(row)
    for i, row in enumerate(rows):
        if not used[i]:
            result.append(row)
else:
    # helper column J empty -> sort names alphabetically A-Z (stable)
    def az_key(v):
        if isinstance(v, bool):
            return (1, str(v).casefold())
        if isinstance(v, (int, float)):
            return (0, float(v))
        return (1, str(v).strip().casefold())
    result = sorted(rows, key=lambda t: az_key(t[1]))

# ---- write final answer into sheet1 F2:H10 (G = names, H = values) ----
for r in range(2, 11):
    for c in (6, 7, 8):
        ws.cell(row=r, column=c).value = None

for idx, (a, b, c) in enumerate(result[:9]):
    r = 2 + idx
    ws.cell(row=r, column=6).value = a   # column A passthrough (part of F:H output range)
    ws.cell(row=r, column=7).value = b   # sorted name (column B)
    ws.cell(row=r, column=8).value = c   # corresponding value (column H)

# ---- save workbook (all existing sheets preserved) ----
wb.save(DST)