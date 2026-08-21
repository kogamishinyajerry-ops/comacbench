
def max_length(list1):
    return max([(len(x), x) for x in list1], key=lambda x: x[0])
