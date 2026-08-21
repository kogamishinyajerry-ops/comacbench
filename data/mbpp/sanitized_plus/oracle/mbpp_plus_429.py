
def and_tuples(test_tup1, test_tup2):
  return tuple(x & y for x, y in zip(test_tup1, test_tup2))
