
def find_Max_Num(arr) : 
    arr.sort(reverse = True)
    return int("".join(map(str,arr)))
