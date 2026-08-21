
def max_sub_array_sum_repeated(a, n, k): 
	modifed = a * k
	pre = 0	# dp[i-1]
	res = modifed[0]
	for n in modifed:
		pre = max(pre + n, n)
		res = max(pre, res)
	return res
