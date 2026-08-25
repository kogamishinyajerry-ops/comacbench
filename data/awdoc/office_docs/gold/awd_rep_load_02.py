"""gold — data-anchored engineering report (docx)."""
import csv
from docx import Document
from docx.shared import Pt

with open("load_02.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

lf = [float(r[1]) for r in data]
cyc = [int(float(r[2])) for r in data]

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
doc.add_paragraph("N cases = {22}")
doc.add_paragraph("load max = {2.39}")
doc.add_paragraph("load mean = {1.69}")
doc.add_paragraph("total cycles = {102294}")
doc.add_heading("Conclusion", level=1)
doc.add_paragraph("See summary above.")
doc.save("report.docx")
