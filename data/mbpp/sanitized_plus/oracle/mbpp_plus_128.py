
def long_words(n, s):
    return list(filter(lambda x: len(x) > n, s.split(' ')))
