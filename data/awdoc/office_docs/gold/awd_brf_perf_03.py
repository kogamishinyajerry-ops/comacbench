"""gold — data-anchored briefing deck (pptx)."""
import csv
from pptx import Presentation
from pptx.util import Inches

with open("perf_03.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

cl = [float(r[1]) for r in data]
cd = [float(r[2]) for r in data]
ld = [float(r[3]) for r in data]

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "Test Briefing"
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Data"
tbl_shape = slide.shapes.add_table(len(data) + 1, len(header), Inches(0.5), Inches(1.2), Inches(6), Inches(0.4 + 0.25 * len(data)))
tbl = tbl_shape.table
for i, h in enumerate(header):
    tbl.cell(0, i).text = str(h)
for r_i, r in enumerate(data, 1):
    for c_i, v in enumerate(r):
        tbl.cell(r_i, c_i).text = str(v)
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Summary"
tf = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(3)).text_frame
tf.text = "Summary"
p = tf.add_paragraph(); p.text = "CLmax max = {0.606}"
p = tf.add_paragraph(); p.text = "CDcruise mean = {0.0333}"
p = tf.add_paragraph(); p.text = "L/D mean = {17.3}"
p = tf.add_paragraph(); p.text = "best config (max L/D) = {'B1'}"
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Next steps"
slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(2)).text_frame.text = "TBD"
prs.save("report.pptx")
