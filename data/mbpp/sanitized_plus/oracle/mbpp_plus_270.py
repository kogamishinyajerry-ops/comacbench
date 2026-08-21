
def sum_even_and_even_index(arr):  
    return sum(x for x in arr[::2] if x % 2 == 0)
