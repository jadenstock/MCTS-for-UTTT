# Confidence thresholds for adaptive thinking
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MODERATE = 0.6

# Number of stable checks required for each confidence level
STABLE_CHECKS_HIGH = 3
STABLE_CHECKS_MODERATE = 5
STABLE_CHECKS_LOW = 8

# Time management
MIN_TIME_RATIO = 0.2  # Minimum fraction of max time to spend
CHECK_INTERVAL = 0.5  # How often to check for early stopping

# Computation distributions for different board states
COMP_DIST_AGGRESSIVE = [1, 0.5, 0.1]      # Few legal moves
COMP_DIST_BALANCED = [0.5, 0.1, 0.05]     # Medium number of legal moves
COMP_DIST_CONSERVATIVE = [0.1, 0.05, 0.05] # Many legal moves

# Node expansion limits
DEFAULT_NODE_LIMIT = float("inf")
DEFAULT_SECONDS_LIMIT = 15

# Strategy thresholds
GREEDY_TIME_THRESHOLD = 5  # Use greedy strategy below this time limit
COMPLEX_POSITION_THRESHOLD = 9  # Number of moves that indicates a complex position