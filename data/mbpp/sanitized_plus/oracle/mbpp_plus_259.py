
def maximize_elements(test_tup1, test_tup2):
  return tuple((max(a, c), max(b, d)) for (a, b), (c, d) in zip(test_tup1, test_tup2))
