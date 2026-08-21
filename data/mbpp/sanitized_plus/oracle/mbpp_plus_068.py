
def is_Monotonic(A): 
    return all(a <= b for a, b in zip(A, A[1:])) or all(a >= b for a, b in zip(A, A[1:]))
