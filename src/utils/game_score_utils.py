LINES = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]

def score_board(board, player):
    """
    Score a tic-tac-toe board from a player's perspective based purely on line analysis.

    Args:
        board: List[str] - length 9 array representing the board
        player: str - either 'X' or 'O'

    Returns:
        float - score in range [0,1] indicating winnability
    """
    opponent = 'O' if player == 'X' else 'X'

    # Calculate potential for each line
    line_potentials = []
    for line in LINES:
        cells = [board[i] for i in line]
        player_count = cells.count(player)
        opponent_count = cells.count(opponent)

        if player_count == 3:
            return 1.0
        if opponent_count == 3:
            return 0.0

        # If line is blocked, skip it
        if player_count > 0 and opponent_count > 0:
            continue

        # Calculate potential based on progress in this line
        if opponent_count == 0:
            line_potentials.append(.15 + ((player_count / 3) ** 1.5))

    # If no viable lines remain, score is 0
    if not line_potentials:
        return 0.0

    # Final score combines best line and number of viable paths
    best_line = max(line_potentials)

    # New path synergy calculation
    num_paths = len(line_potentials)
    path_synergy = sum(sorted(line_potentials, reverse=True)[:4]) / 4  # Average of top 3 paths
    path_multiplier = min(1.5, 1 + (num_paths / 8))  # Bonus for having many paths

    path_strength = path_synergy * path_multiplier

    # Combine best single line with overall position strength
    score = 0.6 * best_line + 0.4 * path_strength
    return min(0.9, score) # never return 1 unless the board is won


def calculate_square_importance(board):
    """
    Calculate importance scores for each empty square for both players.
    Importance is relative to the number of remaining viable winning paths.

    Args:
        board: List[str] - length 9 array representing the board

    Returns:
        tuple(List[float], List[float]) - Importance scores for X and O
    """
    def count_viable_paths(player):
        opponent = 'O' if player == 'X' else 'X'
        viable_paths = 0
        for line in LINES:
            cells = [board[i] for i in line]
            if opponent not in cells:
                viable_paths += 1
        return viable_paths

    def calculate_line_importance(cells, player):
        player_count = cells.count(player)
        opponent = 'O' if player == 'X' else 'X'
        opponent_count = cells.count(opponent)

        # If line is blocked by opponent, it has no importance
        if opponent_count > 0:
            return 0.0

        total_viable_paths = count_viable_paths(player)
        if total_viable_paths == 0:
            return 0.0

        # Value based purely on how many of your pieces are already in the line
        if player_count == 2:
            return min(1.0, 2.0 / total_viable_paths)  # Very important - could win
        elif player_count == 1:
            return 0.3 * (1.0 / total_viable_paths)  # Moderately important - developing line
        else:
            return 0.1 * (1.0 / total_viable_paths)  # Fresh line

        return 0.0

    importance_x = [0.0] * 9
    importance_o = [0.0] * 9

    for line in LINES:
        cells = [board[i] for i in line]
        empty_indices = [i for i in line if board[i] == '']

        if cells.count('X') == 3 or cells.count('O') == 3:
            return [0.0] * 9, [0.0] * 9

        if not empty_indices:
            continue

        importance_x_line = calculate_line_importance(cells, 'X')
        importance_o_line = calculate_line_importance(cells, 'O')

        for idx in empty_indices:
            importance_x[idx] += importance_x_line
            importance_o[idx] += importance_o_line

    max_x = max(importance_x) if max(importance_x) > 0 else 1
    max_o = max(importance_o) if max(importance_o) > 0 else 1

    importance_x = [min(1.0, score / max_x) for score in importance_x]
    importance_o = [min(1.0, score / max_o) for score in importance_o]

    return importance_x, importance_o


### VIZ ###

def print_board(board):
    """Pretty print a board with its values"""
    print("\nBoard:")
    for i in range(0, 9, 3):
        print(f"{board[i]:^3}|{board[i + 1]:^3}|{board[i + 2]:^3}")
        if i < 6:
            print("-" * 11)


def print_importance(imp_x, imp_o):
    """Pretty print importance scores"""
    print("\nImportance scores (X):")
    for i in range(0, 9, 3):
        print(f"{imp_x[i]:^5.2f}|{imp_x[i + 1]:^5.2f}|{imp_x[i + 2]:^5.2f}")
        if i < 6:
            print("-" * 17)

    print("\nImportance scores (O):")
    for i in range(0, 9, 3):
        print(f"{imp_o[i]:^5.2f}|{imp_o[i + 1]:^5.2f}|{imp_o[i + 2]:^5.2f}")
        if i < 6:
            print("-" * 17)


### TESTS ###

TEST_BOARDS = {
        'empty': [''] * 9,

        'x_center': [
            '', '', '',
            '', 'X', '',
            '', '', ''
        ],

        'x_corner': [
            'X', '', '',
            '', '', '',
            '', '', ''
        ],

        'symmetric_corners': [
            'X', '', '',
            '', '', '',
            '', '', 'O'
        ],

        'symmetric_race': [
            'X', '', '',
            'X', '', 'O',
            '', '', 'O'
        ],

        'early_battle': [
            'X', '', '',
            '', 'O', '',
            '', '', ''
        ],

        'x_strong': [
            'X', 'X', '',
            'O', '', '',
            'X', '', ''
        ],

        'x_winning': [
            'X', 'X', '',
            'O', 'O', '',
            'X', '', ''
        ],

        'x_dominant': [
            'X', 'X', '',
            'X', 'X', '',
            '', '', ''
        ],

        'x_dominant_o_has_hope': [
            'X', 'X', '',
            'X', 'X', '',
            '', '', 'O'
        ],

        'o_winning': [
            'X', '', '',
            'O', 'O', '',
            'X', 'X', 'O'
        ],

        'o_winning_x_cant': [
            'X', '', 'O',
            'O', 'O', '',
            'X', 'X', 'O'
        ],

        'x_won': [
            'X', 'X', 'X',
            'O', 'O', '',
            '', '', ''
        ],

        'drawn': [
            'X', 'O', 'X',
            'X', 'O', 'O',
            'O', 'X', 'X'
        ],

        'drawn_but_not_full': [
            'X', 'O', 'O',
            'O', 'X', 'X',
            'X', '', 'O'
        ]
    }

def assert_almost_equal(a, b, message="", tolerance=0.1):
    assert abs(a - b) < tolerance, message

def test_board_scores():
    scores = {name: (score_board(board, 'X'), score_board(board, 'O'))
              for name, board in TEST_BOARDS.items()}

    assert scores['x_won'][0] == 1.0, "X should have score 1.0 in won position"
    assert scores['x_won'][1] == 0.0, "O should have score 0.0 in lost position"
    assert scores['drawn'][0] == 0.0, "Drawn position should score 0 for X"
    assert scores['drawn'][1] == 0.0, "Drawn position should score 0 for O"
    assert scores['x_strong'][0] > scores['x_center'][0], "Multiple threats should score higher than single piece"
    assert scores['x_center'][0] > scores['x_corner'][0], "Center position should score higher than corner"
    assert_almost_equal(scores['empty'][0], scores['empty'][1], "Empty board should be equal for both players")
    assert scores['o_winning'][1] > scores['o_winning'][0], "O's winning position should score higher for O"
    assert scores['x_winning'][0] > scores['x_winning'][1], "X's winning position should score higher than O's"
    assert scores['x_winning'][0] > scores['early_battle'][0], "Clear advantage should score higher than early game"
    assert scores['x_strong'][0] > 0.5, "Strong position should score above 0.5"
    assert scores['early_battle'][0] - scores['early_battle'][1] < 0.3, "Early game shouldn't show huge advantage"


def test_square_importance():
    test_cases = [
        ('x_corner', {
            'description': "With X in corner, O should prioritize path-blocking squares",
            'assertions': (
                lambda x, o: [
                    # Test O's priorities
                    o[5] > o[1], "O should value square 6 more than square 2 to block diagonal/edge paths",
                    o[7] > o[1], "O should value square 8 more than square 2 to block diagonal/edge paths",
                    # Test relative values of squares
                    o[4] > o[1], "Center should be more important than non-critical edges for O",
                    o[8] > o[1], "Far corner should be more important than non-critical edges for O"
                ]
            )
        }),

        ('empty', {
            'description': "Empty board should have center and corners as most important",
            'assertions': (
                lambda x, o: [
                    x[4] > x[1], "Center should be more important than edges",
                    x[0] > x[1], "Corners should be more important than edges"
                ]
            )
        }),

        ('x_won', {
            'description': "Won board should have zero importance everywhere",
            'assertions': (
                lambda x, o: [
                    all(v == 0 for v in x), "All squares should have zero importance for X in won position",
                    all(v == 0 for v in o), "All squares should have zero importance for O in won position"
                ]
            )
        }),

        ('drawn', {
            'description': "Drawn board should have zero importance everywhere",
            'assertions': (
                lambda x, o: [
                    all(v == 0 for v in x), "All squares should have zero importance for X",
                    all(v == 0 for v in o), "All squares should have zero importance for O"
                ]
            )
        })
    ]

    for board_name, test_case in test_cases:
        board = TEST_BOARDS[board_name]
        imp_x, imp_o = calculate_square_importance(board)
        print(f"\nTesting {board_name}: {test_case['description']}")
        print_board(board)
        print_importance(imp_x, imp_o)

        # Run assertions
        assertions = test_case['assertions'](imp_x, imp_o)
        try:
            for condition, message in zip(assertions[::2], assertions[1::2]):
                assert condition, message
            print("✓ Passed")
        except AssertionError as e:
            print(f"✗ Failed: {str(e)}")


if __name__ == "__main__":
    verbose_scores = True
    verbose_importance = True
    test = True

    if verbose_scores:
        for name, board in TEST_BOARDS.items():
            print(f"\n{name}:")
            print_board(board)
            print(f"X score: {score_board(board, 'X'):.3f}")
            print(f"O score: {score_board(board, 'O'):.3f}")

    if verbose_importance:
        for name, board in TEST_BOARDS.items():
            print(f"\n{name}:")
            print_board(board)
            imp_x, imp_o = calculate_square_importance(board)
            print_importance(imp_x, imp_o)

    if test:
        test_board_scores()
        test_square_importance()
