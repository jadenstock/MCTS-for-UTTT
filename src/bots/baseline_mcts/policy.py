from bots.baseline_mcts.eval import evaluate_game_state, score_local_board


class BaselineMCTSPolicy:
    def __init__(self, config):
        self.config = dict(config)
        self.ucb_constant = float(self.config.get("ucb_constant", 1.414))
        self.rollout_depth = int(self.config.get("rollout_depth", 6))
        self.terminal_draw_value = float(self.config.get("terminal_draw_value", 0.5))
        self.exact_endgame_legal_cells_threshold = int(self.config.get("exact_endgame_legal_cells_threshold", -1))

    def evaluate(self, game, player):
        return evaluate_game_state(game.board, player, self.config)

    def score_local_board(self, board, player):
        return score_local_board(board, player, self.config)

    def rollout_move(self, game):
        legal = game.legal_moves()
        if not legal:
            return None
        player = game.next_to_move
        best_move = None
        best_score = -float("inf")
        for move in legal:
            game.make_move(move[0], move[1], player)
            score = self.evaluate(game, player)
            game.undo_last_move()
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

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

    def select_final_move(self, game, root_node):
        player = game.next_to_move
        legal = game.legal_moves()
        if not legal:
            return None
        best_move = None
        best_key = None
        for move in legal:
            child = root_node.children.get(move)
            mean_score = 0.0 if child is None else child.total_score / float(child.number_of_plays)
            threat_level = self.opponent_immediate_threat_level(game, move, player)
            key = (-threat_level, mean_score, -move[0], -move[1])
            if best_key is None or key > best_key:
                best_key = key
                best_move = move
        return best_move
