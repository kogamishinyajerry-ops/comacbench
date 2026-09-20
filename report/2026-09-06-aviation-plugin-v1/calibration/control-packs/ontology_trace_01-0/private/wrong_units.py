import math

def normalize_records(records):
    counts = {}
    for r in records:
        key = r.get('record_id')
        if isinstance(key, str) and key:
            counts[key] = counts.get(key, 0) + 1
    accepted, rejected = [], []
    for row in records:
        rid = row.get('record_id', '')
        if not isinstance(rid, str) or not rid:
            reason = 'missing_id'
            rid = ''
        elif counts[rid] > 1:
            reason = 'duplicate_id'
        elif not isinstance(row.get('part_id'), str) or not row['part_id'] or not isinstance(row.get('source_id'), str) or not row['source_id']:
            reason = 'missing_lineage'
        elif row.get('unit') not in ('mm', 'm'):
            reason = 'unknown_unit'
        elif isinstance(row.get('length'), bool) or not isinstance(row.get('length'), (int, float)) or not math.isfinite(row['length']) or row['length'] <= 0:
            reason = 'invalid_length'
        else:
            accepted.append({'record_id': rid, 'part_id': row['part_id'], 'length_mm': row['length'] * (100 if row['unit'] == 'm' else 1), 'source_id': row['source_id']})
            continue
        rejected.append({'record_id': rid, 'reason': reason})
    return {'accepted': sorted(accepted, key=lambda r: r['record_id']), 'rejected': sorted(rejected, key=lambda r: (r['record_id'], r['reason']))}
