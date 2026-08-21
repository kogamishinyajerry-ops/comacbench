
def is_sublist(l, s):
	if len(l) < len(s):
		return False
	return any(l[i:i+len(s)] == s for i in range(len(l)-len(s)+1))
