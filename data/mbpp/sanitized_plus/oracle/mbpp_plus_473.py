
def tuple_intersection(test_list1, test_list2):
  return set([tuple(sorted(ele)) for ele in test_list1]) & set([tuple(sorted(ele)) for ele in test_list2])
