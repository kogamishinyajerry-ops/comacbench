
import re
def text_lowercase_underscore(text):
        return bool(re.match('^[a-z]+(_[a-z]+)*$', text))
