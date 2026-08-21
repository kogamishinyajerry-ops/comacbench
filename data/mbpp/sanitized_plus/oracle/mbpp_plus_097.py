
def frequency_lists(list1):
    list1 = [item for sublist in list1 for item in sublist]
    return {x: list1.count(x) for x in list1}
