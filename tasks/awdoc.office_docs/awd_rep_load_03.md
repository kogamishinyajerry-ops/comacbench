# Engineering test report (docx) — data-anchored

You are given the data file `load_03.csv` in the current working directory.

## Required document structure

1. Title (any wording) as a Heading.
2. An "Overview" section (Heading 1) with one short paragraph stating the number
   of data rows N (the count of data records in the CSV, excluding the header).
3. A "Results table" section (Heading 1) containing ONE table with a header row
   plus one row per data record, columns exactly ['case', 'load_factor', 'cycles'] (same order, same
   values as the source, numbers formatted with the same rounding as source).
4. A "Summary" section (Heading 1) stating, in any wording, these EXACT numbers:
   - N cases = 26
   - load max = 2.39
   - load mean = 1.7
   - total cycles = 120035
5. One concluding paragraph under a "Conclusion" heading (Heading 1).

## Output contract (objective, cell-level grading)

- Produce a file named exactly `report.docx` in the current directory
  (python-docx is the expected tool; standard library + python-docx only).
- All numeric claims in the document MUST come from the input data — compute
  min/max/mean/count from the CSV values with Python and write the ROUNDED
  display values exactly as specified below (do not hand-round differently).
- Structure requirements (headings/tables/slide count) are graded exactly.
- No external facts; do not invent numbers.

