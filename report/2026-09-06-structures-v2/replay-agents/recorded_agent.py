"""Offline adapter: returns a frozen response, makes no provider/network call."""
import json
from pathlib import Path
import sys
request=json.load(sys.stdin)
record=json.loads(Path(sys.argv[1]).read_text())
if request['task_id'] != record['task_id']:
    raise ValueError('recorded task mismatch')
print(json.dumps(record,ensure_ascii=False))
