def build_graph(entities, assertions):
    types = {e['id']: e['type'] for e in entities}
    signatures = {'made_of': ('Part', 'Material'), 'verified_by': ('Part', 'Analysis'), 'satisfies': ('Part', 'Requirement')}
    edges, issues = {}, []
    for a in assertions:
        source = a.get('source_id', '')
        if not isinstance(source, str) or not source:
            reason, source = 'missing_source', ''
        elif a.get('relation') not in signatures:
            reason = 'unknown_relation'
        elif a.get('subject') not in types or a.get('object') not in types:
            reason = 'missing_entity'
        elif (types[a['subject']], types[a['object']]) != signatures[a['relation']]:
            reason = 'type_mismatch'
        else:
            key = (a['subject'], a['relation'], a['object'])
            edges.setdefault(key, set()).add(source)
            continue
        issues.append({'source_id': source, 'reason': reason})
    return {'edges': [{'subject': k[0], 'relation': k[1], 'object': k[2], 'evidence': sorted(v)} for k, v in sorted(edges.items())], 'issues': sorted(issues, key=lambda x: (x['source_id'], x['reason']))}
