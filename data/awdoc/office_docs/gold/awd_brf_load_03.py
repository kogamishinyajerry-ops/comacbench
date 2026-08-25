"""gold — data-anchored briefing deck (pptx)."""
import csv
from pptx import Presentation
from pptx.util import Inches

with open("load_03.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

lf = [float(r[1]) for r in data]
cyc = [int(float(r[2])) for r in data]

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
p = tf.add_paragraph(); p.text = "N cases = {26}"
p = tf.add_paragraph(); p.text = "load max = {2.39}"
p = tf.add_paragraph(); p.text = "load mean = {1.7}"
p = tf.add_paragraph(); p.text = "total cycles = {120035}"
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Next steps"
slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(2)).text_frame.text = "TBD"
prs.save("report.pptx")
