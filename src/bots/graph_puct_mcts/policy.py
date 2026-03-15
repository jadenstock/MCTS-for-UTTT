from bots.pragmatic_mcts.eval import evaluate_game_state, score_local


CELL_BONUS = [0.18, 0.04, 0.18, 0.04, 0.24, 0.04, 0.18, 0.04, 0.18]


class GraphPUCTPolicy:
    def __init__(self, config):
        self.config = dict(config)
        self.rollout_depth = int(self.config.get("rollout_depth", 6))
        self.c_puct = float(self.config.get("c_puct", 1.4))

    def evaluate(self, game, player):
        return evaluate_game_state(game.board, player, self.config)

    def score_local_board(self, board, player):
        return score_local(board, player, self.config)

    def _opponent_immediate_global_win_exists(self, game, opponent):
        for move in game.legal_moves():
            if not game.make_move(move[0], move[1], opponent):
                continue
            won = game.board.winner == opponent
            game.undo_last_move()
            if won:
                return True
        return False

    def _forced_board_control_score(self, game, move, player):
        opponent = "o" if player == "x" else "x"
        target_board_idx = move[1]
        target_board = game.board.boards[target_board_idx]
        target_open = target_board.winner == "" and any(cell == "" for cell in target_board.cells)
        if not target_open:
            # Sending to a closed board gives the opponent a free move anywhere.
            return -0.30

        board_weight = 1.0 if target_board_idx == 4 else (0.9 if target_board_idx in (0, 2, 6, 8) else 0.8)
        local_delta = self.score_local_board(target_board.cells, player) - self.score_local_board(target_board.cells, opponent)
        return 0.35 * board_weight * local_delta

    def _move_tactical_score(self, game, move, player):
        opponent = "o" if player == "x" else "x"
        if not game.make_move(move[0], move[1], player):
            return -100.0
        score = 0.0
        if game.board.winner == player:
            score += 10.0
        if game.board.boards[move[0]].winner == player:
            score += 1.2
        score += CELL_BONUS[move[1]]
        score += self._forced_board_control_score(game, move, player)
        score += 0.25 * self.evaluate(game, player)
        if self._opponent_immediate_global_win_exists(game, opponent):
            score -= 4.0
        game.undo_last_move()
        return score

    def priors(self, game, legal_moves):
        player = game.next_to_move
        raw = {}
        min_score = float("inf")
        for move in legal_moves:
            s = self._move_tactical_score(game, move, player)
            raw[move] = s
            if s < min_score:
                min_score = s
        # Shift to positive and normalize.
        shifted = {m: (v - min_score + 1e-3) for m, v in raw.items()}
        denom = sum(shifted.values()) or 1.0
        return {m: shifted[m] / denom for m in shifted}

    def rollout_move(self, game):
        legal = game.legal_moves()
        if not legal:
            return None
        priors = self.priors(game, legal)
        return max(legal, key=lambda m: (priors.get(m, 0.0), -m[0], -m[1]))

    def select_final_move(self, game, root_node):
        legal = game.legal_moves()
        if not legal:
            return None
        best = None
        best_key = None
        for move in legal:
            visits = int(root_node.edge_visits.get(move, 0))
            q = root_node.edge_q(move)
            key = (visits, q, -move[0], -move[1])
            if best_key is None or key > best_key:
                best_key = key
                best = move
        return best
