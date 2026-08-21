
def add_pairwise(test_tup):
  return tuple(a + b for a, b in zip(test_tup, test_tup[1:]))
