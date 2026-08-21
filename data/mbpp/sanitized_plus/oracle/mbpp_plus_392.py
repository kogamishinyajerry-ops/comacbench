
def get_max_sum (n):
	# if n = 0, f(0) = max(5(f(0), 0)), so f(0) = 5f(0) or f(0) = 0, for both cases f(0) = 0
	res = [0]
	for i in range(1, n + 1):
		res.append(max(res[i // 2] + res[i // 3] + res[i // 4] + res[i // 5], i))
	return res[n]
