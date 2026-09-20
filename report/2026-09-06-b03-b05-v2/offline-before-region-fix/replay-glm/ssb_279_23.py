"""
Replaces the VBA macro described in the task:
For every cell in column B (rows 3..26 of Sheet1, iterated continuously,
"without gaps"):
  - blank cells stay blank (nothing, not even 0, is written)
  - if the cell text contains parentheses, everything outside the
    (first ...) pair of parentheses is deleted (the parentheses
    themselves and their contents are kept)
  - if there are no parentheses, the cell is left exactly as it is

Column A of the answer region A3:B26 is left untouched (its existing
content is preserved), the whole workbook (all sheets) is preserved and
saved as output.xlsx.
"""

from openpyxl import load_workbook

INPUT_FILE = "ssb_279_23_init.xlsx"
OUTPUT_FILE = "output.xlsx"
SHEET_NAME = "Sheet1"
FIRST_ROW = 3
LAST_ROW = 26
TARGET_COL = 2  # column B


def keep_parenthesized(text: str):
    """
    Delete everything outside the parentheses.

    Returns the substring starting at the first '(' and ending at the
    last ')'.  Returns None when there is no complete '( ... )' pair,
    signalling that the cell should be left unchanged.
    """
    start = text.find("(")
    end = text.rfind(")")
    if start == -1 or end == -1 or end < start:
        return None  # no parentheses -> leave the cell as is
    result = text[start:end + 1]
    stripped = result.strip()
    return stripped if stripped else None


def main():
    wb = load_workbook(INPUT_FILE)   # keeps every existing sheet
    ws = wb[SHEET_NAME]

    # iterate over all cells in column B without gaps (rows 3..26)
    for row in range(FIRST_ROW, LAST_ROW + 1):
        cell = ws.cell(row=row, column=TARGET_COL)
        value = cell.value

        if value is None:
            # blank cell stays blank - never write 0 or anything else
            continue
        if not isinstance(value, str):
            # numbers / other types are left untouched
            continue
        if value == "":
            continue

        new_value = keep_parenthesized(value)
        if new_value is not None:
            cell.value = new_value   # display result in column B
        # else: no parentheses -> leave the cell exactly as it is

    wb.save(OUTPUT_FILE)


if __name__ == "__main__":
    main()