
from collections import Counter 
def check_occurences(test_list):
  return dict(Counter(tuple(sorted(t)) for t in test_list))
