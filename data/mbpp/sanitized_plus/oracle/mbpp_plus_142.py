
def count_samepair(list1,list2,list3):
    return sum(m == n == o for m, n, o in zip(list1,list2,list3))
