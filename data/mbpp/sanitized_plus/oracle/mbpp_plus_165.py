
def count_char_position(str1): 
    return sum(ord(ch.lower()) - ord('a') == i for i, ch in enumerate(str1))
