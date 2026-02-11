# Comprehensive keys for OPTCG card features based on the new Effect-Step architecture

TIMING_KEYS = [
    "on_play", "when_attacking", "activate_main", "counter", 
    "trigger", "blocker", "on_ko", "on_block", "on_opponent_attack",
    "your_turn", "opponent_turn", "end_of_your_turn", "end_of_opponent_turn",
    "once_per_turn", "don_x", "passive"
]

KEYWORD_KEYS = [
    "rush", "blocker", "double_attack", "banish", "unblockable"
]

ACTION_KEYS = [
    "draw", "look", "reveal", "add_to_hand", "place_deck", "shuffle",
    "play", "rest", "active", "ko", "remove_field", "return_to_hand",
    "trash", "add_life", "trash_life", "look_life", "give_power", 
    "give_cost", "set_don", "add_don", "remove_don", "attach_don",
    "gain_ability", "cannot_attack", "cannot_be_ko", "must_attack", 
    "change_target", "cannot_be_removed", "can_attack_played_turn"
]

CONDITION_KEYS = [
    "leader_req", "count_req", "don_req", "character_req", 
    "life_req", "battle_req", "type_req", "color_req", "cost_req", 
    "attribute_req", "power_req", "threshold_req"
]

COST_KEYS = [
    "don_attach", "don_return", "don_rest", "trash_hand", 
    "trash_deck", "trash_life", "rest_self", "rest_other"
]

# New keys for Target and Scope within an Effect Step
TARGET_KEYS = [
    "target_self", "target_your_leader", "target_your_character", 
    "target_opponent_leader", "target_opponent_character", "target_don",
    "target_deck", "target_hand", "target_life"
]

SCOPE_KEYS = [
    "scope_1", "scope_up_to_1", "scope_up_to_2", "scope_up_to_3", 
    "scope_up_to_5", "scope_all"
]