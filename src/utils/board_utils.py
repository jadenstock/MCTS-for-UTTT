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


def game_value_experimental(board, s, win_score=20, lose_score=-20):
    """Enhanced scoring function for Tic-Tac-Toe that considers:
    1. Immediate wins/losses
    2. Two-in-a-row opportunities with different weights based on position
    3. Center and corner control
    4. Blocking opponent's opportunities
    5. Fork opportunities (multiple winning paths)
    """
    t = "o" if s == "x" else "x"  # Opponent's symbol
    score = 0

    # Define all possible lines
    rows = [board[:3], board[3:6], board[6:]]
    cols = [board[0::3], board[1::3], board[2::3]]
    diags = [[board[0], board[4], board[8]], [board[2], board[4], board[6]]]
    all_lines = rows + cols + diags

    # Check for immediate wins/losses
    for line in all_lines:
        if line.count(s) == 3:
            return win_score
        if line.count(t) == 3:
            return lose_score

    # Center control (most valuable position)
    if board[4] == s:
        score += 4
    elif board[4] == t:
        score -= 4

    # Corner control (second most valuable positions)
    corners = [0, 2, 6, 8]
    for corner in corners:
        if board[corner] == s:
            score += 2
        elif board[corner] == t:
            score -= 2

    # Evaluate each line for opportunities
    fork_opportunities_s = 0  # Count potential forks for player
    fork_opportunities_t = 0  # Count potential forks for opponent

    for line in all_lines:
        # Two-in-a-row with open space
        if line.count(s) == 2 and line.count('') == 1:
            # Weight based on if it uses center or corner
            if 4 in [i for i, x in enumerate(line) if x == s]:
                score += 6  # Higher weight for center-based threats
            elif any(i in corners for i, x in enumerate(line) if x == s):
                score += 4  # Medium weight for corner-based threats
            else:
                score += 3  # Lower weight for edge-based threats

        # Opponent's two-in-a-row
        if line.count(t) == 2 and line.count('') == 1:
            if 4 in [i for i, x in enumerate(line) if x == t]:
                score -= 6
            elif any(i in corners for i, x in enumerate(line) if x == t):
                score -= 4
            else:
                score -= 3

        # Count potential fork opportunities
        if line.count(s) == 1 and line.count('') == 2:
            fork_opportunities_s += 1
        if line.count(t) == 1 and line.count('') == 2:
            fork_opportunities_t += 1

    # Add fork opportunity scores
    if fork_opportunities_s >= 2:
        score += 5  # Bonus for having multiple winning paths
    if fork_opportunities_t >= 2:
        score -= 5  # Penalty for allowing opponent multiple paths

    # Normalize score to be within win/lose bounds
    max_possible = 50  # Maximum possible score from all bonuses
    normalized_score = ((score + max_possible) * (win_score - lose_score) /
                        (2 * max_possible)) + lose_score

    return normalized_score


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