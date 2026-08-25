# Engineering table task — flag family

You are given an input file `eng_flag_02.csv` in the current working directory.

## Transformation specification

1. Read `eng_flag_02.csv` (columns: time, alt_ft, ias_kt, load_g). Some load_g
   cells are EMPTY (missing measurements).
2. Output TWO sheets.

Sheet `DATA`, header exactly:
["time", "alt_ft", "ias_kt", "load_g", "status_alt", "status_ias", "status_load"]
- Copy the four source columns unchanged (empty stays empty — do NOT write
  anything, not even 0 or a blank string, into an empty cell).
- For each channel add a status column with exactly one of "OK" / "OVER" /
  "MISSING": "MISSING" if the source cell is empty; otherwise "OVER" if the
  value is outside the inclusive limit range, "OK" if inside.

Limits (inclusive [lo, hi]):
- alt_ft: [9000.0, 18000.0]
- ias_kt: [135.0, 210.0]
- load_g: [1.05, 2.2]

Sheet `STATS`, header exactly: ["channel", "min", "max", "mean"]
- One row per channel name sorted ascending (alt_ft, ias_kt, load_g);
  min/max/mean computed over NON-EMPTY values only, rounded to 3 decimals.
- The status columns are NOT part of stats.
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
