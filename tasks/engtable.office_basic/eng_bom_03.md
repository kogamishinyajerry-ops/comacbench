# Engineering table task — bom family

You are given an input file `eng_bom_03.csv` in the current working directory.

## Transformation specification

1. Read `eng_bom_03.csv` (columns: part_no, desc, qty, unit, batch, note).
2. The source has duplicate part numbers spread across rows.
3. Output ONE sheet named `BOM` with header exactly:
   ["part_no", "desc", "qty_total", "unit"]
4. One row per unique part_no: desc and unit from the source, qty_total = SUM of
   all qty values for that part_no.
5. Sort rows by part_no ascending (string sort).
6. Do not carry over batch/note columns.
## Workbooks and cells

Respond with ONE complete ```python code block that performs the transformation and writes the workbook.
## Output contract (grading is cell-level and objective)

- Produce a file named exactly `output.xlsx` in the current directory (openpyxl
  Workbook is the expected tool; you may use only the Python standard library
  plus openpyxl).
- Write STATIC values only — NO formulas in any cell (the grader reads values,
  a formula cell reads as None and scores as a miss).
- Sheet names and header rows (row 1) must match the specification EXACTLY
  (names, spelling, order). Extra sheets, extra columns, or extra populated
  cells outside the specified tables are penalized.
- Round every computed numeric cell to 0 decimal places (Python round()).
- No formatting requirements (colors/bold are ignored by the grader).
