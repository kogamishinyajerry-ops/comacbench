# Engineering test briefing (pptx) — data-anchored

You are given the data file `load_01.csv` in the current working directory.

## Required deck structure

- EXACTLY 4 slides:
  1. Title slide (deck title, any wording).
  2. "Data" slide with ONE table: header row + one row per data record,
     columns exactly ['case', 'load_factor', 'cycles'].
  3. "Summary" slide with bullet lines containing these EXACT numbers:
     - N cases = 18
   - load max = 2.35
   - load mean = 1.7
   - total cycles = 87563
  4. "Next steps" slide (any wording).

## Output contract (objective, cell-level grading)

- Produce a file named exactly `report.pptx` in the current directory
  (python-pptx is the expected tool; standard library + python-pptx, openpyxl-free only).
- All numeric claims in the document MUST come from the input data — compute
  min/max/mean/count from the CSV values with Python and write the ROUNDED
  display values exactly as specified below (do not hand-round differently).
- Structure requirements (headings/tables/slide count) are graded exactly.
- No external facts; do not invent numbers.

