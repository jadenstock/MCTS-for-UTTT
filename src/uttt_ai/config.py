# Confidence and stability thresholds
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MODERATE = 0.6
SCORE_DIFF_NORMALIZER = 0.5

STABLE_CHECKS_HIGH = 3
STABLE_CHECKS_MODERATE = 5
STABLE_CHECKS_LOW = 8

# Time management
MIN_TIME_RATIO = 0.2  # Minimum fraction of max time to spend
CHECK_INTERVAL = 0.5  # How often to check for early stopping

# Computation distributions for different scenarios
COMP_DIST_MANY_MOVES = [0.1, 0.05, 0.05]  # When >=9 legal moves
COMP_DIST_MEDIUM_MOVES = [0.5, 0.1, 0.05]  # Default case
COMP_DIST_FEW_MOVES = [1.0, 0.5, 0.1]     # When few legal moves

# Strategy thresholds
GREEDY_TIME_THRESHOLD = 5
MEDIUM_TIME_THRESHOLD = 10
COMPLEX_POSITION_THRESHOLD = 9  # Number of moves that indicates a complex position
MEDIUM_POSITION_THRESHOLD = 5   # Threshold for medium complexity positions

# Default limits
DEFAULT_NODE_LIMIT = float("inf")
DEFAULT_SECONDS_LIMIT = 15
DEFAULT_OPPONENT_NODE_LIMIT = 75
DEFAULT_UCB_CONSTANT = 1