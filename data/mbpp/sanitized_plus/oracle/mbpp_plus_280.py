
def sequential_search(dlist, item):
    return item in dlist, (dlist.index(item) if item in dlist else -1)
