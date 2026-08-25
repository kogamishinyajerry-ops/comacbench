# Engineering table task — si family

You are given an input file `eng_si_03.csv` in the current working directory.

## Transformation specification

1. Read `eng_si_03.csv` (columns: run, force_lbf, length_in, temp_f).
2. Output ONE sheet named `SI` with header exactly:
   ["run", "force_n", "length_mm", "temp_c"]
3. Convert per row using EXACTLY these factors:
   force_n = force_lbf * 4.4482216152605
   length_mm = length_in * 25.4
   temp_c = (temp_f - 32.0) * 5.0 / 9.0
4. Round every converted value to 3 decimals; keep the run id string unchanged.
5. Preserve source row order.
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
- Round every computed numeric cell to 3 decimal places (Python round()).
- No formatting requirements (colors/bold are ignored by the grader).
