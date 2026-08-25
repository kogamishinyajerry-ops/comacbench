# Engineering table task — exceed family

You are given an input file `eng_exceed_04.csv` in the current working directory.

## Transformation specification

1. Read `eng_exceed_04.csv` (columns: event, t_s, load_factor).
2. Select all rows with load_factor >= 1.60.
3. Sort the selected rows by load_factor DESCENDING (largest first); for equal
   values keep source order.
4. Output ONE sheet named `EXCEED` with header exactly:
   ["event", "t_s", "load_factor"]
   containing the FIRST 7 rows of that sorted selection (top-7).
5. Copy event/t_s as strings unchanged; load_factor as the original number
   (already 2-decimal source data — do not re-round).
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
