PRAGMATIC_BOT_ID = "pragmatic_v1"


PRAGMATIC_PRESETS = {
    PRAGMATIC_BOT_ID: {
        "ucb_constant": 1.25,
        "rollout_depth": 8,
        "base_potential": 0.18,
        "line_exponent": 1.6,
        "max_multiplier": 1.6,
        "weight_best": 0.62,
        "weight_path": 0.38,
        "max_score": 0.92,
        "importance_win_weight": 2.2,
        "importance_develop_weight": 0.35,
        "importance_fresh_weight": 0.1,
        "global_score_weight": 0.62,
        "strategic_score_weight": 0.38,
        "offensive_weight": 0.58,
        "defensive_weight": 0.42,
        "final_max_score": 0.92,
        "won_board_bonus": 0.18,
        "open_two_bonus": 0.03,
    }
}


def get_preset(bot_id: str):
    return dict(PRAGMATIC_PRESETS[PRAGMATIC_BOT_ID])

