import itertools
import copy

from utils.board_utils import three_in_a_row, game_value

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

    def score(self, s, win_score=20, lose_score=-20):
        if self.winner == s:
            return win_score
        if ((self.winner != "") and (self.winner != s)):
            return lose_score
        return game_value(self.cells, s, win_score=win_score, lose_score=lose_score)


class Board:
    def __init__(self):
        self.boards = [MiniBoard() for _ in range(9)]
        self.winner = ""

    def evaluate_winner(self):
        boards = [b.winner for b in self.boards]
        return three_in_a_row(boards)

    def score(self, s):
        # if we only look at won or lost games then we wont know what to do in the early game.
        # normalize board score to always be in [0,1] with 1 as win and 0 as loss
        if self.winner == s:
            return 1
        if ((self.winner != "") and (self.winner != s)):
            return 0

        score = 0
        # best we can get here is something like 20*9 = 180.
        for i in range(9):
            score += game_value(self.boards[i].cells, s, win_score=20, lose_score=-20)

        # win and lose score here dont matter. Best we could get is 1000
        boards = [b.winner for b in self.boards]
        score += 50 * game_value(boards, s, win_score=1, lose_score=0)

        # max a score could be is -1200<->1200 so add 1200 and divide by 2400
        return (score + 1200) / 2400.0


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
            print("({}, {}) is not a valid move".format(i, j))
            return False
        legal_moves = self.legal_moves()
        if (((i, j) not in legal_moves) or (len(legal_moves) == 0)):
            print("({}, {}) is not a legal move".format(i, j))
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