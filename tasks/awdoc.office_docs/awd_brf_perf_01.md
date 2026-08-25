# Engineering test briefing (pptx) — data-anchored

You are given the data file `perf_01.csv` in the current working directory.

## Required deck structure

- EXACTLY 4 slides:
  1. Title slide (deck title, any wording).
  2. "Data" slide with ONE table: header row + one row per data record,
     columns exactly ['config', 'cl_max', 'cd_cruise', 'ld_ratio'].
  3. "Summary" slide with bullet lines containing these EXACT numbers:
     - CLmax max = 0.545
   - CDcruise mean = 0.0313
   - L/D mean = 16.3
   - best config (max L/D) = A1 (state this config name)
  4. "Next steps" slide (any wording).

## Output contract (objective, cell-level grading)

- Produce a file named exactly `report.pptx` in the current directory
  (python-pptx is the expected tool; standard library + python-pptx, openpyxl-free only).
- All numeric claims in the document MUST come from the input data — compute
  min/max/mean/count from the CSV values with Python and write the ROUNDED
  display values exactly as specified below (do not hand-round differently).
- Structure requirements (headings/tables/slide count) are graded exactly.
- No external facts; do not invent numbers.

