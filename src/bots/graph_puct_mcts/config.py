GRAPH_PUCT_BOT_ID = "graph_puct_v1"


GRAPH_PUCT_PRESETS = {
    GRAPH_PUCT_BOT_ID: {
        "c_puct": 1.4,
        "rollout_depth": 6,
        "ucb_constant": 1.2,
        "base_potential": 0.18,
        "line_exponent": 1.6,
        "max_multiplier": 1.6,
        "weight_best": 0.62,
        "weight_path": 0.38,
        "max_score": 0.92,
        "importance_win_weight": 2.1,
        "importance_develop_weight": 0.34,
        "importance_fresh_weight": 0.1,
        "global_score_weight": 0.62,
        "strategic_score_weight": 0.38,
        "offensive_weight": 0.56,
        "defensive_weight": 0.44,
        "final_max_score": 0.92,
        "won_board_bonus": 0.16,
        "open_two_bonus": 0.03,
    }
}


def get_preset(bot_id: str):
    return dict(GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID])

