GRAPH_PUCT_BOT_ID = "graph_puct_v1"


GRAPH_PUCT_PRESETS = {
    GRAPH_PUCT_BOT_ID: {
        "c_puct": 1.4,
        "rollout_depth": 6,
        "exact_endgame_threshold": 10,
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

# New immutable variants for Elo tracking experiments.
GRAPH_PUCT_PRESETS["graph_puct_legal10_draw050_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 10,
    "terminal_draw_value": 0.5,
}
GRAPH_PUCT_PRESETS["graph_puct_legal14_draw050_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 14,
    "terminal_draw_value": 0.5,
}
GRAPH_PUCT_PRESETS["graph_puct_legal10_draw025_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 10,
    "terminal_draw_value": 0.25,
}
# Practical guidance: around ~10 legal cells is usually safe for exact solve latency.
GRAPH_PUCT_PRESETS["graph_puct_legal6_draw025_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 6,
    "terminal_draw_value": 0.25,
}
GRAPH_PUCT_PRESETS["graph_puct_legal14_draw025_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 14,
    "terminal_draw_value": 0.25,
}
GRAPH_PUCT_PRESETS["graph_puct_legal18_draw025_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 18,
    "terminal_draw_value": 0.25,
}
GRAPH_PUCT_PRESETS["graph_puct_legal10_draw000_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 10,
    "terminal_draw_value": 0.0,
}
GRAPH_PUCT_PRESETS["graph_puct_legal14_draw000_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 14,
    "terminal_draw_value": 0.0,
}
GRAPH_PUCT_PRESETS["graph_puct_legal18_draw000_v2"] = {
    **GRAPH_PUCT_PRESETS[GRAPH_PUCT_BOT_ID],
    "exact_endgame_legal_cells_threshold": 18,
    "terminal_draw_value": 0.0,
}


def get_preset(bot_id: str):
    selected_id = bot_id if bot_id in GRAPH_PUCT_PRESETS else GRAPH_PUCT_BOT_ID
    return dict(GRAPH_PUCT_PRESETS[selected_id])
