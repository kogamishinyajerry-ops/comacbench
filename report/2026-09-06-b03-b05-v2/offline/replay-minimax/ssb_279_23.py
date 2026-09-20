import openpyxl
import re

# Load the input workbook
wb = openpyxl.load_workbook('ssb_279_23_init.xlsx')
ws = wb['Sheet1']

# Iterate over column B cells in the answer region (rows 3 to 26)
for row in range(3, 27):
    cell = ws.cell(row=row, column=2)  # Column B
    value = cell.value

    # Leave blank cells blank
    if value is None or (isinstance(value, str) and value == ''):
        continue

    text = str(value)

    # Extract content within the first pair of parentheses
    match = re.search(r'\(([^)]*)\)', text)
    if match:
        cell.value = match.group(1)
    # else: leave as is if no parentheses

# Save the workbook
wb.save('output.xlsx')