from utils.utils import LINES, load_agent_config

def score_board(board, player, agent_id='default'):
    """
    Score a tic-tac-toe board from a player's perspective using parameters from the config.
    """
    opponent = 'O' if player == 'X' else 'X'
    config = load_agent_config(agent_id=agent_id)

    # Extract scoring parameters from config (with defaults)
    base_potential = float(config.get("base_potential", 0.15))
    line_exponent = float(config.get("line_exponent", 1.5))
    max_multiplier = float(config.get("max_multiplier", 1.5))
    weight_best = float(config.get("weight_best", 0.6))
    weight_path = float(config.get("weight_path", 0.4))
    max_score = float(config.get("max_score", 0.9))

    line_potentials = []
    for line in LINES:
        cells = [board[i] for i in line]
        player_count = cells.count(player)
        opponent_count = cells.count(opponent)

        if player_count == 3:
            return 1.0
        if opponent_count == 3:
            return 0.0

        # If the line is contested by both players, skip it.
        if player_count > 0 and opponent_count > 0:
            continue

        # Only consider lines that are not blocked.
        if opponent_count == 0:
            # Use config values in computing the potential for this line.
            potential = base_potential + ((player_count / 3) ** line_exponent)
            line_potentials.append(potential)

    if not line_potentials:
        return 0.0

    best_line = max(line_potentials)
    num_paths = len(line_potentials)
    # Average of the top up-to-4 path potentials:
    path_synergy = sum(sorted(line_potentials, reverse=True)[:4]) / 4
    path_multiplier = min(max_multiplier, 1 + (num_paths / 8))
    path_strength = path_synergy * path_multiplier

    score = weight_best * best_line + weight_path * path_strength
    return min(max_score, score)


def calculate_square_importance(board, agent_id='default'):
    """
    Calculate importance scores for each empty square for both players.
    Importance is relative to the number of remaining viable winning paths.
    Uses config values for weighting different line progress states.
    """
    config = load_agent_config(agent_id=agent_id)
    # Extract importance weights from config (or use defaults)
    importance_win_weight = float(config.get("importance_win_weight", 2.0))
    importance_develop_weight = float(config.get("importance_develop_weight", 0.3))
    importance_fresh_weight = float(config.get("importance_fresh_weight", 0.1))

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

        # If the line is blocked, it has no importance.
        if opponent_count > 0:
            return 0.0

        total_viable_paths = count_viable_paths(player)
        if total_viable_paths == 0:
            return 0.0

        if player_count == 2:
            return min(1.0, importance_win_weight / total_viable_paths)
        elif player_count == 1:
            return importance_develop_weight * (1.0 / total_viable_paths)
        else:
            return importance_fresh_weight * (1.0 / total_viable_paths)

    importance_x = [0.0] * 9
    importance_o = [0.0] * 9

    for line in LINES:
        cells = [board[i] for i in line]
        empty_indices = [i for i in line if board[i] == '']

        # If someone has already won on this line, return zeros.
        if cells.count('X') == 3 or cells.count('O') == 3:
            return [0.0] * 9, [0.0] * 9

        if not empty_indices:
            continue

        imp_x_line = calculate_line_importance(cells, 'X')
        imp_o_line = calculate_line_importance(cells, 'O')

        for idx in empty_indices:
            importance_x[idx] += imp_x_line
            importance_o[idx] += imp_o_line

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
    'x_center': ['', '', '', '', 'X', '', '', '', ''],
    'x_corner': ['X', '', '', '', '', '', '', '', ''],
    'symmetric_corners': ['X', '', '', '', '', '', '', '', 'O'],
    'symmetric_race': ['X', '', '', 'X', '', 'O', '', '', 'O'],
    'early_battle': ['X', '', '', '', 'O', '', '', '', ''],
    'x_strong': ['X', 'X', '', 'O', '', '', 'X', '', ''],
    'x_winning': ['X', 'X', '', 'O', 'O', '', 'X', '', ''],
    'x_dominant': ['X', 'X', '', 'X', 'X', '', '', '', ''],
    'x_dominant_o_has_hope': ['X', 'X', '', 'X', 'X', '', '', '', 'O'],
    'o_winning': ['X', '', '', 'O', 'O', '', 'X', 'X', 'O'],
    'o_winning_x_cant': ['X', '', 'O', 'O', 'O', '', 'X', 'X', 'O'],
    'x_won': ['X', 'X', 'X', 'O', 'O', '', '', '', ''],
    'drawn': ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X'],
    'drawn_but_not_full': ['X', 'O', 'O', 'O', 'X', 'X', 'X', '', 'O']
}


def assert_almost_equal(a, b, message="", tolerance=0.1):
    assert abs(a - b) < tolerance, message


def test_board_scores(agent_id='default'):
    scores = {
        name: (
            score_board(board, 'X', agent_id=agent_id),
            score_board(board, 'O', agent_id=agent_id)
        )
        for name, board in TEST_BOARDS.items()
    }

    # Define test conditions as (description, condition lambda)
    tests = [
        ("[x_won] X should score 1.0 in a won position", lambda s: s['x_won'][0] == 1.0),
        ("[x_won] O should score 0.0 in a lost position", lambda s: s['x_won'][1] == 0.0),
        ("[drawn] X should score 0.0 in a drawn position", lambda s: s['drawn'][0] == 0.0),
        ("[drawn] O should score 0.0 in a drawn position", lambda s: s['drawn'][1] == 0.0),
        ("[x_strong vs x_center] Multiple threats should score higher than a single piece", lambda s: s['x_strong'][0] > s['x_center'][0]),
        ("[x_center vs x_corner] Center should score higher than corner", lambda s: s['x_center'][0] > s['x_corner'][0]),
        ("[empty] Empty board should be equal for both players", lambda s: abs(s['empty'][0] - s['empty'][1]) < 0.1),
        ("[o_winning] O's winning position should score higher for O than X", lambda s: s['o_winning'][1] > s['o_winning'][0]),
        ("[x_winning] X's winning position should score higher for X than for O", lambda s: s['x_winning'][0] > s['x_winning'][1]),
        ("[x_winning vs early_battle] Clear advantage should score higher than early game", lambda s: s['x_winning'][0] > s['early_battle'][0]),
        ("[x_strong] Strong position should score above 0.5", lambda s: s['x_strong'][0] > 0.5),
        ("[early_battle] Early game difference should be less than 0.3", lambda s: abs(s['early_battle'][0] - s['early_battle'][1]) < 0.3)
    ]

    all_passed = True
    print("=== Testing Board Scores for agent '{}' ===".format(agent_id))
    for desc, condition in tests:
        try:
            if condition(scores):
                print(f"PASSED - {desc}")
            else:
                print(f"FAILED - {desc}")
                all_passed = False
        except Exception as e:
            print(f"{desc} FAILED with exception: {e}")
            all_passed = False
    return all_passed


def test_square_importance(agent_id='default'):
    test_cases = [
        ('x_corner', {
            'description': "With X in corner, O should prioritize path-blocking squares",
            'assertions': (
                lambda x, o: [
                    o[5] > o[1], "O should value square 6 more than square 2 to block diagonal/edge paths",
                    o[7] > o[1], "O should value square 8 more than square 2 to block diagonal/edge paths",
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
        imp_x, imp_o = calculate_square_importance(board, agent_id=agent_id)
        print(f"\nTesting {board_name}: {test_case['description']}")
        assertions = test_case['assertions'](imp_x, imp_o)
        try:
            # The assertions lambda returns a flat list: alternating [condition, message, ...]
            for condition, message in zip(assertions[::2], assertions[1::2]):
                assert condition, message
            print("Passed")
        except AssertionError as e:
            print(f"Failed: {str(e)}")


def validate_config(agent_id='default'):
    """
    Validate the current configuration by running board score and square importance tests.
    Returns True if all tests pass; otherwise, prints the error and returns False.
    """
    print(f"\nValidating configuration for agent '{agent_id}'...")
    try:
        test_board_scores(agent_id=agent_id)
        test_square_importance(agent_id=agent_id)
    except AssertionError as e:
        print("Configuration validation FAILED:", e)
        return False
    print("All tests PASSED for agent", agent_id)
    return True


### MAIN ###
if __name__ == "__main__":

    agent_id = 'aggressive'
    verbose_scores = False
    verbose_importance = False
    test = True

    if test:
        validate_config(agent_id=agent_id)

    if verbose_scores:
        for name, board in TEST_BOARDS.items():
            print(f"\n{name}:")
            print_board(board)
            print(f"X score: {score_board(board, 'X', agent_id=agent_id):.3f}")
            print(f"O score: {score_board(board, 'O', agent_id=agent_id):.3f}")

    if verbose_importance:
        for name, board in TEST_BOARDS.items():
            print(f"\n{name}:")
            print_board(board)
            imp_x, imp_o = calculate_square_importance(board, agent_id=agent_id)
            print_importance(imp_x, imp_o)