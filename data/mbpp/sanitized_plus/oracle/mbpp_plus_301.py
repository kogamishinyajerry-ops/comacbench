
def dict_depth_aux(d):
    if isinstance(d, dict):
        return 1 + (max(map(dict_depth_aux, d.values())) if d else 0)
    return 0
def dict_depth(d):
    return dict_depth_aux(d)
