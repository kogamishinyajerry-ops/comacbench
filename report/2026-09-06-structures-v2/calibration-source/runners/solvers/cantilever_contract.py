"""Bounded, fail-closed input audit for an axis-aligned C3D20 cantilever.

Not a general CalculiX parser. Every supported keyword/option is explicit, and
unsupported semantics stop the audit before a solver can consume the deck.
"""
from __future__ import annotations

from collections import defaultdict
import math
import re

PROFILE = 'ccx.cantilever.v1'
CHECKS = ('connectivity', 'mesh', 'material', 'boundary', 'load', 'output')
MAX_ENTITIES = 100000
ISSUE_CODES = {
    'unconnected_loaded_nodes', 'unused_nodes', 'undefined_connectivity',
    'uncheckable_mesh', 'duplicate_coordinates', 'invalid_c3d20_geometry',
    'mesh_below_minimum', 'geometry_mismatch', 'incomplete_structured_mesh',
    'undefined_section', 'material_assignment', 'material_mismatch',
    'face_set_mismatch', 'clamp_mismatch', 'unsupported_load_dof',
    'tip_load_mismatch', 'print_contract_mismatch', 'unsupported_element_type',
    'unsupported_deck_feature', 'invalid_deck', 'deck_size_limit',
    'nonfinite_load_sum',
}


def contract_errors(contract):
    errors = []
    def bad(field, message):
        errors.append({'field': field, 'message': message})
    def finite(value):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)
    if not isinstance(contract, dict):
        return [{'field': 'deck_contract', 'message': '结构契约必须为对象，不能用空值关闭检查。'}]
    expected = {'profile', 'geometry_mm', 'min_elements', 'material', 'total_fy_n'}
    if set(contract) != expected:
        bad('deck_contract', '字段缺失或未知；需完整声明 profile/geometry_mm/min_elements/material/total_fy_n。')
    if contract.get('profile') != PROFILE:
        bad('profile', f'当前支持 {PROFILE}。')
    dims = contract.get('geometry_mm')
    if not isinstance(dims, list) or len(dims) != 3 or any(not finite(x) or x < .001 or x > 1e6 for x in dims):
        bad('geometry_mm', '按 [长度, 高度, 宽度] 填写 0.001 到 1e6 mm 的有限值。')
    counts = contract.get('min_elements')
    if not isinstance(counts, list) or len(counts) != 3 or any(type(x) is not int or x < 1 or x > 1000 for x in counts) or math.prod(counts) > 20000:
        bad('min_elements', '按三个方向填写正整数，最小单元总数不能超过 20000。')
    mat = contract.get('material')
    if not isinstance(mat, dict) or set(mat) != {'youngs_modulus_mpa', 'poisson_ratio', 'density_tonne_mm3'}:
        bad('material', '材料需完整声明弹性模量 MPa、泊松比和密度 tonne/mm³。')
    else:
        for k, v in mat.items():
            if not finite(v) or (not -1 < v < .5 if k == 'poisson_ratio' else v <= 0):
                bad('material.' + k, '材料参数不在有限、物理可用的范围内。')
    if not finite(contract.get('total_fy_n')) or contract['total_fy_n'] >= 0:
        bad('total_fy_n', '此悬臂梁 profile 要求有限负向 Y 合载荷 N。')
    return errors


class DeckError(ValueError):
    def __init__(self, code, line, message):
        self.code, self.line = code, line
        super().__init__(message)


def _number(value):
    n = float(value.replace('D', 'E'))
    if not math.isfinite(n):
        raise ValueError('数值必须有限')
    return n


def _id(value):
    if not re.fullmatch(r'[0-9]+', value) or not 0 < int(value) <= 2147483647:
        raise ValueError('编号必须为正整数')
    return int(value)


def _cards(text):
    allowed = {
        'HEADING': set(), 'NODE': {'NSET'}, 'ELEMENT': {'TYPE', 'ELSET'},
        'NSET': {'NSET', 'GENERATE'}, 'ELSET': {'ELSET', 'GENERATE'},
        'MATERIAL': {'NAME'}, 'ELASTIC': {'TYPE'}, 'DENSITY': set(),
        'SOLID SECTION': {'ELSET', 'MATERIAL'}, 'BOUNDARY': set(),
        'STEP': {'NAME'}, 'STATIC': set(), 'CLOAD': set(),
        'NODE PRINT': {'NSET'}, 'END STEP': set(),
    }
    cards = []
    if len(text.encode('utf-8')) > 8 * 1024 * 1024:
        raise DeckError('deck_size_limit', 0, '此 profile 的输入文件上限为 8 MiB。')
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip().upper()
        if not s or s.startswith('**'):
            continue
        if s.startswith('*'):
            tokens = [x.strip() for x in s[1:].split(',')]
            name, options = tokens[0], {}
            if name not in allowed:
                raise DeckError('unsupported_deck_feature', ln, f'暂不支持关键字 *{name}。')
            for token in tokens[1:]:
                key, sep, value = token.partition('=')
                key, value = key.strip(), value.strip()
                if not token: continue
                if key in options or key not in allowed[name] or (key == 'GENERATE' and sep) or (key != 'GENERATE' and not value):
                    raise DeckError('unsupported_deck_feature', ln, f'暂不支持或重复的 *{name} 选项：{token}。')
                options[key] = value
            cards.append({'name': name, 'options': options, 'line': ln, 'rows': []})
        elif not cards:
            raise DeckError('invalid_deck', ln, '数据行之前缺少关键字。')
        else:
            vals = [x.strip() for x in s.split(',')]
            while vals and not vals[-1]: vals.pop()
            if len(vals) > 16 and cards[-1]['name'] != 'HEADING':
                raise DeckError('invalid_deck', ln, '数据行超过 16 项。')
            cards[-1]['rows'].append((ln, vals))
    return cards


def _parse(text):
    nodes, elements, nsets, esets, materials = {}, {}, {}, {}, {}
    sections, boundaries, loads, prints = [], [], [], []
    active_material, step, ended, statics = None, False, False, 0

    def expand(token, sets, entities):
        if token in sets:
            return sets[token]
        node = _id(token)
        if node not in entities:
            raise ValueError(f'引用未定义编号 {node}')
        return {node}

    for card in _cards(text):
        name, op, rows, line = card['name'], card['options'], card['rows'], card['line']
        try:
            if ended:
                raise ValueError('END STEP 后不允许额外内容；此 profile 只支持一个静力步')
            if name == 'HEADING': continue
            if name == 'STEP':
                if step: raise ValueError('只支持一个 STEP')
                step = True
            elif name == 'END STEP':
                if not step or statics != 1: raise ValueError('STEP/STATIC/END STEP 不完整')
                ended = True
            elif name == 'STATIC':
                if not step or statics: raise ValueError('需要且只允许一个 STATIC')
                statics += 1
                if len(rows) > 1 or rows and (len(rows[0][1]) > 4 or any(_number(x) <= 0 for x in rows[0][1])):
                    raise ValueError('STATIC 只支持默认参数或一行正数增量参数')
            elif name in {'CLOAD', 'NODE PRINT'}:
                if not step or not statics: raise ValueError(f'{name} 必须位于 STATIC 之后的 STEP 中')
                if name == 'CLOAD':
                    for line, row in rows:
                        if len(row) != 3: raise ValueError('CLOAD 需要节点/集合、自由度、力')
                        loads.append((set(expand(row[0], nsets, nodes)), _id(row[1]), _number(row[2]), line))
                else:
                    if op.get('NSET') not in nsets: raise ValueError('NODE PRINT 集合未定义')
                    prints.append((op['NSET'], [x for _, row in rows for x in row]))
            elif name == 'BOUNDARY':
                for line, row in rows:
                    if not 2 <= len(row) <= 4: raise ValueError('BOUNDARY 需要节点/集合、首末自由度和可选值')
                    start = _id(row[1]); end = _id(row[2]) if len(row) > 2 and row[2] else start
                    if not start <= end <= 6: raise ValueError('边界自由度范围须在 1 到 6 之间')
                    value = _number(row[3]) if len(row) == 4 else 0.
                    boundaries.append((set(expand(row[0], nsets, nodes)), start, end, value, line))
            else:
                if step: raise ValueError(f'{name} 只允许出现在 STEP 之前')
                if name == 'NODE':
                    added = set()
                    for line, row in rows:
                        if len(row) != 4: raise ValueError('NODE 需要编号与三个坐标')
                        n = _id(row[0])
                        if n in nodes: raise ValueError(f'重复节点编号 {n}')
                        nodes[n] = tuple(_number(x) for x in row[1:]); added.add(n)
                    if op.get('NSET'): nsets.setdefault(op['NSET'], set()).update(added)
                elif name == 'ELEMENT':
                    if op.get('TYPE') != 'C3D20':
                        raise DeckError('unsupported_element_type', line, '本题只接受 C3D20 单元。')
                    pending, added = [], set()
                    for line, row in rows:
                        pending.extend(_id(x) for x in row)
                        if len(pending) > 21: raise ValueError('C3D20 连通数据必须按单元换行，每个单元 20 个节点')
                        if len(pending) == 21:
                            eid, *conn = pending
                            if eid in elements: raise ValueError(f'重复单元编号 {eid}')
                            elements[eid] = (conn, line); added.add(eid); pending = []
                    if pending: raise ValueError('C3D20 单元连通数据不完整')
                    if op.get('ELSET'): esets.setdefault(op['ELSET'], set()).update(added)
                elif name in {'NSET', 'ELSET'}:
                    sets, entities = (nsets, nodes) if name == 'NSET' else (esets, elements)
                    label = op[name]; added = set()
                    for line, row in rows:
                        if 'GENERATE' in op:
                            if len(row) not in (2, 3): raise ValueError('GENERATE 需要起止编号与可选步长')
                            first, last = _id(row[0]), _id(row[1]); inc = _id(row[2]) if len(row) == 3 else 1
                            if first > last or (last-first)//inc > MAX_ENTITIES: raise ValueError('GENERATE 范围无效或过大')
                            ids = set(range(first, last+1, inc))
                            if not ids <= entities.keys(): raise ValueError('集合包含未定义编号')
                            added.update(ids)
                        else:
                            for token in row: added.update(expand(token, sets, entities))
                    sets.setdefault(label, set()).update(added)
                elif name == 'MATERIAL':
                    active_material = op['NAME']
                    if active_material in materials: raise ValueError('重复材料名称')
                    materials[active_material] = {}
                elif name in {'ELASTIC', 'DENSITY'}:
                    if not active_material: raise ValueError('缺少 MATERIAL')
                    if op.get('TYPE', 'ISOTROPIC') != 'ISOTROPIC':
                        raise DeckError('unsupported_deck_feature', line, '只支持各向同性线弹性材料。')
                    size = 2 if name == 'ELASTIC' else 1
                    if len(rows) != 1 or len(rows[0][1]) != size or name in materials[active_material]:
                        raise ValueError('材料值缺失、重复或包含温度相关数据')
                    materials[active_material][name] = [_number(x) for x in rows[0][1]]
                elif name == 'SOLID SECTION':
                    if rows: raise ValueError('三维实体截面不接受额外参数行')
                    sections.append((op['ELSET'], op['MATERIAL'], line))
            if name in {'STEP', 'END STEP', 'MATERIAL'} and rows:
                raise ValueError(f'{name} 不接受数据行')
            if len(nodes) > MAX_ENTITIES or len(elements) > 20000:
                raise ValueError('超出本 profile 的节点/单元规模上限')
        except (KeyError, ValueError) as e:
            if isinstance(e, DeckError): raise
            raise DeckError('invalid_deck', line, str(e)) from e
    if not ended:
        raise DeckError('invalid_deck', 0, '缺少完整的 STEP/STATIC/END STEP')
    return dict(nodes=nodes, elements=elements, nsets=nsets, esets=esets,
                materials=materials, sections=sections, boundaries=boundaries, loads=loads, prints=prints)


def audit_cantilever_deck(text, contract):
    report = {'profile': PROFILE, 'passed': False, 'checks': [], 'issues': [], 'summary': {}}
    def issue(check, code, message, details=None, line=None):
        report['issues'].append({'check': check, 'code': code, 'line': line,
                                'message': message, 'details': details or {},
                                'suggested_fix': '按公开题面与受支持输入契约修复后，用新身份重新评测。'})
    errors = contract_errors(contract)
    if errors:
        for error in errors: issue('contract', 'invalid_deck_contract', error['message'], error)
        return report
    try:
        deck = _parse(text)
    except DeckError as e:
        issue('syntax', e.code, str(e), line=e.line)
        return report
    nodes, elements = deck['nodes'], deck['elements']
    used = {n for conn, _ in elements.values() for n in conn}
    loaded = {n for ns, _, value, _ in deck['loads'] if value for n in ns}
    unconnected = sorted(loaded - used)
    if unconnected:
        issue('connectivity', 'unconnected_loaded_nodes', f'{len(unconnected)} 个受载节点未连接任何单元。',
              {'count': len(unconnected), 'node_ids': unconnected, 'source_lines': sorted({ln for ns, _, v, ln in deck['loads'] if v and ns & set(unconnected)})})
    if not nodes or not elements or not used <= nodes.keys():
        issue('connectivity', 'undefined_connectivity', '网格为空或单元引用了未定义节点。', {'node_ids': sorted(used - nodes.keys())})
    unused = sorted(nodes.keys() - used)
    if unused:
        issue('connectivity', 'unused_nodes', f'{len(unused)} 个节点未参与网格。', {'count': len(unused), 'node_ids': unused})
    report['summary'].update(nodes=len(nodes), elements=len(elements), loaded_nodes=len(loaded), unconnected_loaded_nodes=len(unconnected))
    _engineering_checks(deck, contract, issue, report['summary'])
    failed = {i['check'] for i in report['issues']}
    report['checks'] = [{'id': check, 'status': 'fail' if check in failed else 'pass'} for check in CHECKS]
    report['passed'] = not report['issues']
    return report


def _engineering_checks(deck, contract, issue, summary):
    nodes, elements = deck['nodes'], deck['elements']
    used = {n for conn, _ in elements.values() for n in conn}
    length, height, width = contract['geometry_mm']
    eps = max(1e-6, max(length, height, width) * 1e-8)
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-20)
    point_close = lambda a, b: all(abs(x-y) <= eps for x, y in zip(a, b))
    corner_axes = [set() for _ in range(3)]
    cells, bad_elements = [], []
    if not used or not used <= nodes.keys():
        issue('mesh', 'uncheckable_mesh', '节点连通数据不完整，无法核验网格。')
    else:
        coordinates = {}
        duplicates = []
        for n in sorted(used):
            key = tuple(round(v / eps) for v in nodes[n])
            if key in coordinates: duplicates.append([coordinates[key], n])
            coordinates[key] = n
        if duplicates:
            issue('mesh', 'duplicate_coordinates', '相邻单元必须共用节点编号；存在重合但不相连的节点。', {'pairs': duplicates[:20], 'count': len(duplicates)})
        for eid, (conn, line) in elements.items():
            pts = [nodes[n] for n in conn]
            lo = tuple(min(p[a] for p in pts[:8]) for a in range(3))
            hi = tuple(max(p[a] for p in pts[:8]) for a in range(3))
            vectors = [tuple(pts[j][a]-pts[0][a] for a in range(3)) for j in (1, 3, 4)]
            a, b, c = vectors
            determinant = (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0]))
            orthogonal = all(sum(abs(x) > eps for x in v) == 1 for v in vectors)
            corners = [(0,0,0), (1,0,0), (1,1,0), (0,1,0), (0,0,1), (1,0,1), (1,1,1), (0,1,1)]
            valid = len(set(conn)) == 20 and orthogonal and determinant > 0 and all(hi[i]-lo[i] > 2*eps for i in range(3))
            for i, signs in enumerate(corners):
                expected = tuple(pts[0][d] + sum(signs[j]*vectors[j][d] for j in range(3)) for d in range(3))
                valid = valid and point_close(pts[i], expected)
            edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
            for i, (a, b) in enumerate(edges, 8):
                valid = valid and point_close(pts[i], tuple((pts[a][d]+pts[b][d])/2 for d in range(3)))
            if not valid: bad_elements.append(eid)
            cells.append((lo, hi))
            for d in range(3):
                corner_axes[d].update((round(lo[d]/eps), round(hi[d]/eps)))
        if bad_elements:
            issue('mesh', 'invalid_c3d20_geometry', '单元须为正向、轴对齐 C3D20；角点顺序和 12 个边中点必须一致。', {'element_ids': bad_elements[:20], 'count': len(bad_elements)})
        axes = [sorted(a) for a in corner_axes]
        counts = [len(a)-1 for a in axes]
        summary['mesh_elements_xyz'] = counts
        if any(n < m for n, m in zip(counts, contract['min_elements'])):
            issue('mesh', 'mesh_below_minimum', '三个方向的单元划分未达到题面下限。', {'actual': counts, 'minimum': contract['min_elements']})
        expected_lo, expected_hi = (0., -height/2, -width/2), (length, height/2, width/2)
        if not point_close(tuple(a[0]*eps for a in axes), expected_lo) or not point_close(tuple(a[-1]*eps for a in axes), expected_hi):
            issue('mesh', 'geometry_mismatch', '网格外包络与梁的长度、截面或原点不一致。')
        indices = [{v:i for i,v in enumerate(a)} for a in axes]
        seen = set(); tiled = True
        for lo, hi in cells:
            lower = tuple(indices[d][round(lo[d]/eps)] for d in range(3))
            upper = tuple(indices[d][round(hi[d]/eps)] for d in range(3))
            if lower in seen or any(upper[d] != lower[d]+1 for d in range(3)): tiled = False
            seen.add(lower)
        if not tiled or len(seen) != math.prod(counts):
            issue('mesh', 'incomplete_structured_mesh', '网格存在重复单元、空缺、重叠或非一致的结构化分区。')

    assignments = defaultdict(list)
    for es, mat, line in deck['sections']:
        if es not in deck['esets'] or mat not in deck['materials']:
            issue('material', 'undefined_section', '实体截面引用未定义的单元集合或材料。', line=line)
        else:
            for eid in deck['esets'][es]: assignments[eid].append(mat)
    invalid_assignments = [eid for eid in elements if len(assignments[eid]) != 1]
    if invalid_assignments:
        issue('material', 'material_assignment', '每个单元必须且只能分配一份实体材料。', {'element_ids': invalid_assignments[:20], 'count': len(invalid_assignments)})
    wanted = contract['material']
    for name in {m for values in assignments.values() for m in values}:
        mat = deck['materials'][name]
        actual = mat.get('ELASTIC', []) + mat.get('DENSITY', [])
        expected = [wanted['youngs_modulus_mpa'], wanted['poisson_ratio'], wanted['density_tonne_mm3']]
        if len(actual) != 3 or not all(close(a, b) for a, b in zip(actual, expected)):
            issue('material', 'material_mismatch', '实际分配材料的弹性模量、泊松比或密度不符（含缺失）。', {'material': name, 'actual_E_nu_rho': actual, 'expected_E_nu_rho': expected})

    root = {n for n in used & nodes.keys() if abs(nodes[n][0]) <= eps}
    tip = {n for n in used & nodes.keys() if abs(nodes[n][0]-length) <= eps}
    for label, expected, check in [('NROOT', root, 'boundary'), ('NTIP', tip, 'load')]:
        actual = deck['nsets'].get(label, set())
        if not expected or actual != expected:
            issue(check, 'face_set_mismatch', f'{label} 必须恰好包含对应端面所有网格节点。', {'set': label, 'missing': sorted(expected-actual), 'extra': sorted(actual-expected)})
    fixed, invalid_bc = set(), []
    for ns, start, end, value, line in deck['boundaries']:
        if not ns <= root or value != 0:
            invalid_bc.append(line)
        for n in ns:
            for dof in range(start, min(end, 3)+1): fixed.add((n, dof))
    required = {(n, dof) for n in root for dof in (1, 2, 3)}
    if invalid_bc or fixed != required:
        issue('boundary', 'clamp_mismatch', '根部需固定三个平移自由度，且不得额外固定其他位置或施加非零位移。', {'lines': invalid_bc, 'missing_dofs': len(required-fixed)})

    loads = defaultdict(float)
    for ns, dof, value, line in deck['loads']:
        if dof not in (1,2,3):
            issue('load', 'unsupported_load_dof', '实体单元集中力自由度只允许 1、2、3。', line=line)
        for n in ns: loads[n, dof] += value
    total = sum(v for (n,d),v in loads.items() if d == 2)
    if not math.isfinite(total) or any(not math.isfinite(v) for v in loads.values()):
        issue('load', 'nonfinite_load_sum', '累加载荷溢出；请使用有限且合理的力值。')
    else:
        summary.update(declared_fy_n=total, connected_fy_n=sum(v for (n,d),v in loads.items() if d == 2 and n in used), tip_mesh_nodes=len(tip))
        unwanted = [(n,d) for (n,d),v in loads.items() if v and (n not in tip or d != 2)]
        per_node = contract['total_fy_n'] / max(1, len(tip))
        unequal = [n for n in tip if not close(loads[n,2], per_node)]
        if unwanted or unequal or not close(total, contract['total_fy_n']):
            issue('load', 'tip_load_mismatch', '合载荷或均分方式不符：只允许在全部尖端网格节点施加相等的 Y 向集中力。', {'total_fy_n': total, 'expected_fy_n': contract['total_fy_n'], 'unequal_nodes': unequal[:20], 'unexpected_node_dof': unwanted[:20]})
    if sorted((label, tuple(fields)) for label, fields in deck['prints']) != [('NROOT', ('RF',)), ('NTIP', ('U',))]:
        issue('output', 'print_contract_mismatch', '步内必须且只能请求 NTIP 的 U 与 NROOT 的 RF 两份 NODE PRINT。')
