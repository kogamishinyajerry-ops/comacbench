
def count_Primes_nums(n):
    return sum(all(i % j != 0 for j in range(2, i)) for i in range(2, n))
