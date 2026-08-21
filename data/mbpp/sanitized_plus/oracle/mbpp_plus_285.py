
import re
def text_match_two_three(text):
    patterns = 'ab{2,3}'
    return re.search(patterns, text) is not None
