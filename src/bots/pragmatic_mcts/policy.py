from bots.pragmatic_mcts.eval import evaluate_game_state, score_local


CELL_BONUS = [0.18, 0.04, 0.18, 0.04, 0.24, 0.04, 0.18, 0.04, 0.18]


class PragmaticMCTSPolicy:
    def __init__(self, config):
        self.config = dict(config)
        self.ucb_constant = float(self.config.get("ucb_constant", 1.25))
        self.rollout_depth = int(self.config.get("rollout_depth", 8))

    def evaluate(self, game, player):
        return evaluate_game_state(game.board, player, self.config)

    def score_local_board(self, board, player):
        return score_local(board, player, self.config)

    def _opponent_immediate_global_win_exists(self, game, opponent):
        for move in game.legal_moves():
            if not game.make_move(move[0], move[1], opponent):
                continue
            opponent_wins = game.board.winner == opponent
            game.undo_last_move()
            if opponent_wins:
                return True
        return False

    def opponent_immediate_threat_level(self, game, move, player):
        opponent = "o" if player == "x" else "x"
        if not game.make_move(move[0], move[1], player):
            return 2

        threat_level = 0
        for opp_move in game.legal_moves():
            if not game.make_move(opp_move[0], opp_move[1], opponent):
                continue
            if game.board.winner == opponent:
                threat_level = 2
                game.undo_last_move()
                break
            if game.board.boards[opp_move[0]].winner == opponent:
                threat_level = max(threat_level, 1)
            game.undo_last_move()

        game.undo_last_move()
        return threat_level

    def _quick_move_value(self, game, move, player):
        opponent = "o" if player == "x" else "x"
        if not game.make_move(move[0], move[1], player):
            return -999.0

        score = 0.0
        if game.board.winner == player:
            score += 10.0
        if game.board.boards[move[0]].winner == player:
            score += 1.4

        score += CELL_BONUS[move[1]]
        score += 0.30 * self.evaluate(game, player)

        if self._opponent_immediate_global_win_exists(game, opponent):
            score -= 6.0

        game.undo_last_move()
        return score

    def rollout_move(self, game):
        legal = game.legal_moves()
        if not legal:
            return None
        player = game.next_to_move

        best_move = None
        best_score = -float("inf")
        for move in legal:
            move_score = self._quick_move_value(game, move, player)
            if move_score > best_score:
                best_score = move_score
                best_move = move
        return best_move

    def select_final_move(self, game, root_node):
        player = game.next_to_move
        opponent = "o" if player == "x" else "x"
        legal = game.legal_moves()
        if not legal:
            return None

        opponent_has_direct_win_now = self._opponent_immediate_global_win_exists(game, opponent)
        best_move = None
        best_key = None

        for move in legal:
            child = root_node.children.get(move)
            mean_score = 0.0 if child is None else child.total_score / float(child.number_of_plays)
            rollouts = 0 if child is None else int(child.number_of_plays)

            game.make_move(move[0], move[1], player)
            immediate_global_win = int(game.board.winner == player)
            immediate_local_win = int(game.board.boards[move[0]].winner == player)
            blocks_opp_global = int(opponent_has_direct_win_now and not self._opponent_immediate_global_win_exists(game, opponent))
            game.undo_last_move()

            threat_level = self.opponent_immediate_threat_level(game, move, player)
            key = (
                immediate_global_win,
                blocks_opp_global,
                immediate_local_win,
                -threat_level,
                mean_score,
                rollouts,
                -move[0],
                -move[1],
            )
            if best_key is None or key > best_key:
                best_key = key
                best_move = move
        return best_move

