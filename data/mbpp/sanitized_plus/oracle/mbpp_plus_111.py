
def common_in_nested_lists(nestedlist):
    return list(set.intersection(*map(set, nestedlist)))
