
def next_power_of_2(n): 
  if n and not n & (n - 1):
    return n
  res = 1
  while n != 0: 
    n >>= 1
    res <<= 1
  return res; 
