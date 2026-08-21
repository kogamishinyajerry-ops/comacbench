
from collections import defaultdict
def max_occurrences(nums):
    d = defaultdict(int)
    for n in nums:
        d[n] += 1
    return max(d, key=d.get)
