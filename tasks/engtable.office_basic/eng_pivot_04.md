# Engineering table task — pivot family

You are given an input file `eng_pivot_04.csv` in the current working directory.

## Transformation specification

1. Read `eng_pivot_04.csv` (columns: config, channel, rep, value) — long format:
   each (config, channel) pair has 2-4 repeat measurements.
2. Output ONE sheet named `SUMMARY` with header exactly:
   ["config"] + sorted channel names from the data (e.g. ["config", "drag",
   "lift", "moment"] — alphabetical order).
3. One row per config (sorted ascending). Each cell = the MAX of all
   values for that (config, channel), rounded to 3 decimals.
4. Keep the original measured values as-is when aggregating (no pre-rounding).
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
