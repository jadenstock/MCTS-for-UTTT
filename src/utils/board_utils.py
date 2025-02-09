def three_in_a_row(arr):
    """Return "x" if "x" has three in a row, return "o" if "o" has a three in a row, else ""
    Cells are arranged as:
        0 | 1 | 2
        ---------
        3 | 4 | 5
        ---------
        6 | 7 | 8
    """
    if (arr[0] == arr[1] == arr[2]) or (arr[0] == arr[3] == arr[6]) or (arr[0] == arr[4] == arr[8]):
        if arr[0] != "":
            return arr[0]

    if (arr[1] == arr[4] == arr[7]) or (arr[3] == arr[4] == arr[5]) or (arr[2] == arr[4] == arr[6]):
        if arr[4] != "":
            return arr[4]

    if (arr[6] == arr[7] == arr[8]) or (arr[2] == arr[5] == arr[8]):
        if arr[8] != "":
            return arr[8]

    return ""


def game_value(board, s, win_score=20, lose_score=-20):
    """Return the 'value' of this game for player s.
    Uses classic Russell and Norvig Tic Tac Toe eval function:
    3 * x2 + x1 - (3*o2+o1) where x2 and o2 are number of lines with two x's or o's
    and x1 and o1 defined likewise.
    """
    t = "o" if s == "x" else "x"
    for_us, for_them = 0, 0

    # Define all possible winning lines
    l1, l2, l3 = board[:3], board[3:6], board[6:]  # Rows
    l4, l5, l6 = board[0::3], board[1::3], board[2::3]  # Columns
    l7, l8 = [board[0], board[4], board[8]], [board[2], board[4], board[6]]  # Diagonals

    # Check each line
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