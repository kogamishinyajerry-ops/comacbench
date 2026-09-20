"""Self-contained, offline, read-only report. Scores are never calculated in the UI."""
import html
import json
from pathlib import Path


def write_report(path, data):
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=Path(__file__).with_name('report.html').read_text(encoding='utf-8')
    Path(path).write_text(template.replace('/*__DATA__*/',payload),encoding='utf-8')
