#return "x" if "x" has three in a row, return "o" if "o" has a three in a row, else ""
# cells are like:
	# 0 | 1 | 2
	# - - - - -
	# 3 | 4 | 5
	# - - - - - 
	# 6 | 7 | 8
def three_in_a_row(arr):
	if (arr[0]==arr[1]==arr[2]) or (arr[0]==arr[3]==arr[6]) or (arr[0]==arr[4]==arr[8]):
		if arr[0] != "":
			return arr[0]

	if (arr[1]==arr[4]==arr[7]) or (arr[3]==arr[4]==arr[5]) or (arr[2]==arr[4]==arr[6]):
		if arr[4] != "":
			return arr[4]

	if (arr[6]==arr[7]==arr[8]) or (arr[2]==arr[5]==arr[8]):
		if arr[8] != "":
			return arr[8]

	return ""

# return the 'value' of this game for player s.
# we want more possible wins to be rated higher, we want closer wins to be rated higher "e.g. two in a row"
# and even if we can't win we want block opponents to be given value. We also want the win score to be higher than just potential wins because
# we want to incentivise wins.
#
# use classic Russell and Norvig Tic Tac Toe eval function
# 3 * x2 + x1 - (3*o2+o1) where x2 and o2 or number fo lines with two x's or 0's and x1 and o1 defined likewise.
# score can be something like += 20
def game_value(board, s, win_score=20, lose_score=-20):
	t = "o" if s=="x" else "x"
	for_us, for_them = 0, 0
	l1, l2, l3 = board[:3], board[3:6], board[6:]
	l4, l5, l6 = board[0::3], board[1::3], board[2::3]
	l7, l8 = [board[0], board[4], board[8]], [board[2], board[4], board[6]]
	#most you could get from potential wins is 18
	for l in [l1, l2, l3, l4, l5, l6, l7, l8]:
		tmp = sorted(l)
		if tmp[0] == s:
			if tmp[1] == s:
				if tmp[2] == s:
					return win_score
				elif tmp[2] == '':
					for_us += 3
					continue
			elif (tmp[1] == '') and (tmp[2] == ''):
				for_us += 1
				continue

		if tmp[0] == t:
			if tmp[1] == t:
				if tmp[2] == t:
					return lose_score
				elif tmp[2] == '':
					for_us -= 3
					continue
			elif (tmp[1] == '') and (tmp[2] == ''):
				for_us -= 1
				continue

	return (for_us + for_them)


"""def game_value(board, s, win_score=20, lose_score=-20):
	t = "o" if s=="x" else "x"
	if three_in_a_row(board) == s:
		return win_score
	elif three_in_a_row(board) == t:
		return lose_score
	
	for_us, for_them = 0, 0
	l1, l2, l3 = board[:3], board[3:6], board[6:]
	l4, l5, l6 = board[0::3], board[1::3], board[2::3]
	l7, l8 = [board[0], board[4], board[8]], [board[2], board[4], board[6]]
	#most you could get from potential wins is 18
	for l in [l1, l2, l3, l4, l5, l6, l7, l8]:
		tmp = sorted(l)
		if tmp == [s, s, ""]:
			for_us += 3
			continue
		if tmp == [s, "", ""]:
			for_us += 1
			continue
		if tmp == [t, "", ""]:
			for_them -= 1
			continue
		if tmp == [t, t, ""]:
			for_them -= 3
			continue
	return (for_us + for_them)"""

