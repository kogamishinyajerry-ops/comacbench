
def is_undulating(n): 
	digits = [int(digit) for digit in str(n)]
	if len(set(digits)) != 2:
		return False
	return all(a != b for a, b in zip(digits, digits[1:]))
