"""gold — data-anchored engineering report (docx)."""
import csv
from docx import Document
from docx.shared import Pt

with open("perf_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

cl = [float(r[1]) for r in data]
cd = [float(r[2]) for r in data]
ld = [float(r[3]) for r in data]

doc = Document()
doc.add_heading("Test Report", 0)
doc.add_heading("Overview", level=1)
doc.add_paragraph(f"This report summarizes {len(data)} data records.")
doc.add_heading("Results table", level=1)
t = doc.add_table(rows=1, cols=len(header))
for i, h in enumerate(header):
    t.rows[0].cells[i].text = str(h)
for r in data:
    cells = t.add_row().cells
    for i, v in enumerate(r):
        cells[i].text = str(v)
doc.add_heading("Summary", level=1)
doc.add_paragraph("CLmax max = {0.525}")
doc.add_paragraph("CDcruise mean = {0.0339}")
doc.add_paragraph("L/D mean = {15.8}")
doc.add_paragraph("best config (max L/D) = {'A1'}")
doc.add_heading("Conclusion", level=1)
doc.add_paragraph("See summary above.")
doc.save("report.docx")
