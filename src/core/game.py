import itertools

from utils.board_utils import three_in_a_row
from utils.game_score_utils import score_board, calculate_square_importance

class MiniBoard:
    def __init__(self):
        self.cells = ["" for _ in range(9)]
        self.winner = ""  # either "", "x", or "o"

    def evaluate_winner(self):
        return three_in_a_row(self.cells)

    def legal_cells(self):
        if self.winner == "":
            return [i for i, c in enumerate(self.cells) if c == ""]
        else:
            return []


class Board:
    def __init__(self):
        self.boards = [MiniBoard() for _ in range(9)]
        self.winner = ""

    def evaluate_winner(self):
        boards = [b.winner for b in self.boards]
        return three_in_a_row(boards)

    def score(self, player):
        """
        Score a UTTT board position combining global winning potential with strategic control.
        Returns a value between 0 and 1, where:
        - 1.0 means player has won
        - 0.0 means opponent has won
        - Other values combine global winning potential (60%) with strategic board control (40%)
        """
        opponent = "o" if player == "x" else "x"

        # Terminal state checks
        if self.winner == player:
            return 1.0
        if self.winner == opponent:
            return 0.0

        # Calculate global board and importance metrics
        global_board = [b.winner for b in self.boards]
        global_importance_player, global_importance_opp = calculate_square_importance(global_board)

        # Calculate global winning potential (60% weight)
        global_score = score_board(global_board, player)

        # Calculate strategic control score (40% weight)
        strategic_score = 0.0
        total_weight = 0.0

        # Evaluate each mini-board for strategic control
        for i, mini_board in enumerate(self.boards):
            if mini_board.winner != "":
                continue

            # Calculate winnability for both players
            winnability_player = score_board(mini_board.cells, player)
            winnability_opp = score_board(mini_board.cells, opponent)

            # Weight based on global importance
            board_importance = max(global_importance_player[i],
                                   global_importance_opp[i])

            # Score combines offensive potential and defensive necessity
            board_score = (0.7 * winnability_player * global_importance_player[i] -
                           0.3 * winnability_opp * global_importance_opp[i])

            strategic_score += board_score * board_importance
            total_weight += board_importance

        # Normalize strategic score
        if total_weight > 0:
            strategic_score = (strategic_score / total_weight + 1) / 2
        else:
            strategic_score = 0.0

        # Combine global and strategic scores with 60/40 weighting
        final_score = 0.65 * global_score + 0.35 * strategic_score

        # Ensure score stays in [0, 1] range, reserving 1.0 for won positions
        return max(0.0, min(0.9, final_score))


class Game:
    def __init__(self):
        self.board = Board()
        self.move_stack = [] # tuple (i,j,s) meaning s was placed on position j in board i.
        self.next_to_move = "x"

    def evaluate_winners(self):
        """Evaluate and update all winners based on current board state"""
        for board in self.board.boards:
            board.winner = board.evaluate_winner()
        self.board.winner = self.board.evaluate_winner()

    def legal_moves(self):
        # if the game is over, stop returning legal moves
        if self.board.winner != "":
            return []

        # Get last move from stack
        last_move = self.move_stack[-1] if self.move_stack else None

        # if it's the first move, the target board is won, or the target board is full, go anywhere
        if (last_move is None or
                (self.board.boards[last_move[1]].winner != "") or
                len(self.board.boards[last_move[1]].legal_cells()) == 0):
            return list(itertools.chain(*[[(i, j) for j in self.board.boards[i].legal_cells()]
                                          for i in range(9)]))
        else:
            # Must play in the board corresponding to the last move's cell
            return [(last_move[1], x) for x in self.board.boards[last_move[1]].legal_cells()]

    def make_move(self, i, j, s):
        # check conditions to not do anything
        if ((s != self.next_to_move) or (self.board.winner != "")):
            return False
        legal_moves = self.legal_moves()
        if (((i, j) not in legal_moves) or (len(legal_moves) == 0)):
            return False
        # edit game state
        self.move_stack.append((i, j, s))
        self.board.boards[i].cells[j] = s
        self.evaluate_winners()
        self.next_to_move = "x" if s == "o" else "o"
        return True

    def undo_last_move(self):
        if not self.move_stack:
            return False
        board_idx, cell_idx, player = self.move_stack.pop()
        self.board.boards[board_idx].cells[cell_idx] = ""
        self.evaluate_winners()
        self.next_to_move = player
        return True

    def greedy_next_move(self):
        best_move = None
        best_move_score = -float("inf")
        for m in self.legal_moves():
            # Make the move directly on our current state
            self.make_move(m[0], m[1], self.next_to_move)
            # Evaluate score
            s = self.board.score(self.next_to_move)
            # Undo the move to restore previous state
            self.undo_last_move()

            if s > best_move_score:
                best_move_score = s
                best_move = m
        return best_move  # will be None in case of drawn game

    def execute_greedy_next_move(self):
        m = self.greedy_next_move()
        if m != None:  # else there are no legal moves and do nothing
            self.make_move(m[0], m[1], self.next_to_move)

    def run_n_greedy_moves(self, n):
        for _ in range(n):
            self.execute_greedy_next_move()

    def __repr__(self):
        return "{\"move stack\":{}, \"board\":{}}".format(
            self.move_stack, [b.cells for b in self.board.boards])

    def __str__(self):
        # Format the game board as a string representation
        f = lambda x: x if x != "" else " "
        rows = []
        for i in range(3):
            for j in range(3):
                row = []
                for k in range(3):
                    board_idx = i * 3 + k
                    cell_start = j * 3
                    cells = self.board.boards[board_idx].cells[cell_start:cell_start + 3]
                    row.extend([f(cell) for cell in cells])
                    if k < 2:
                        row.append("||")
                rows.append(" | ".join(row))
            if i < 2:
                rows.append("-----------   ------------  -------------")
            else:
                rows.append("===========   ============  ==============")
        return "\n".join(rows)


def make_game(game_board, move_stack):
    """Create a game instance from a board state and last move"""
    g = Game()
    g.move_stack = move_stack
    g.next_to_move = "x" if move_stack[-1][2].lower() == "o" else "o"
    for i, b in enumerate(g.board.boards):
        b.cells = [l.lower() for l in game_board[i]]
        b.winner = b.evaluate_winner()
    g.board.winner = g.board.evaluate_winner()
    return g