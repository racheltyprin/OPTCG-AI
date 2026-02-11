import re
import sys
import os
from typing import Dict, List, Optional, Any

# Ensure we can find featureslist in the same directory
sys.path.append(os.path.dirname(__file__))
from featureslist import TIMING_KEYS, KEYWORD_KEYS, ACTION_KEYS, CONDITION_KEYS, COST_KEYS, TARGET_KEYS, SCOPE_KEYS
from cardDataClass import EffectStep

class CardEffectParser:
    def __init__(self):
        self.timing_patterns = {
            r'\[On Play\]': 'on_play',
            r'\[When Attacking\]': 'when_attacking',
            r'\[Activate: Main\]': 'activate_main',
            r'\[Counter\]': 'counter',
            r'\[Trigger\]': 'trigger',
            r'\[Blocker\]': 'blocker',
            r'\[On K\.O\.\]': 'on_ko',
            r'\[On Block\]': 'on_block',
            r'\[On Your Opponent\'s Attack\]': 'on_opponent_attack',
            r'\[Your Turn\]': 'your_turn',
            r'\[Opponent\'s Turn\]': 'opponent_turn',
            r'\[End of Your Turn\]': 'end_of_your_turn',
            r'\[End of Your Opponent\'s Turn\]': 'end_of_opponent_turn',
            r'\[Once Per Turn\]': 'once_per_turn',
            r'\[DON!! x(\d+)\]': 'don_x',
        }
        
        self.keyword_patterns = {
            r'\[Rush\]': 'rush',
            r'\[Rush: Character\]': 'rush',
            r'\[Blocker\]': 'blocker',
            r'\[Double Attack\]': 'double_attack',
            r'\[Banish\]': 'banish',
            r'\[Unblockable\]': 'unblockable',
        }

    def _extract_amount(self, text: str, default: int = 1) -> int:
        match = re.search(r'([+−-]?\d+)', text)
        if match:
            val_str = match.group(1).replace('−', '-')
            return int(val_str)
        return default

    def _get_empty_step_flags(self) -> Dict[str, Dict[str, int]]:
        return {
            "timing": {k: 0 for k in TIMING_KEYS},
            "actions": {k: 0 for k in ACTION_KEYS},
            "conditions": {k: 0 for k in CONDITION_KEYS},
            "costs": {k: 0 for k in COST_KEYS},
            "targets": {k: 0 for k in TARGET_KEYS},
            "scopes": {k: 0 for k in SCOPE_KEYS}
        }

    def parse_card_effects(self, text: str) -> List[EffectStep]:
        if not text or text == '-':
            return []

        # 1. Split into logical blocks (by <br> or double newline)
        blocks = [b.strip() for b in re.split(r'<br>|\n\n', text) if b.strip()]
        effect_steps = []

        for block in blocks:
            # Extract timing for this block
            block_timing = {k: 0 for k in TIMING_KEYS}
            for pattern, key in self.timing_patterns.items():
                match = re.search(pattern, block)
                if match:
                    if key == 'don_x': block_timing[key] = int(match.group(1))
                    else: block_timing[key] = 1
            
            # Identify if the block is passive (no bracketed timing)
            if not re.search(r'\[[^\]]+\]', block):
                block_timing["passive"] = 1

            # 2. Split block into sequential steps (by "Then," or periods)
            # We use a lookahead to avoid splitting on decimal points or common abbreviations
            steps_text = [s.strip() for s in re.split(r'\. (?=[A-Z])|Then,', block) if s.strip()]
            
            for step_text in steps_text:
                # Clean timing tags from step text for action parsing
                clean_step = re.sub(r'\[[^\]]+\]', '', step_text).strip()
                if not clean_step: continue

                step_flags = self._get_empty_step_flags()
                step_flags["timing"] = block_timing.copy()
                step_flags["conditions"]["cost_req"] = -999
                step_flags["conditions"]["power_req"] = -999

                # --- TARGET ATTRIBUTION ---
                if re.search(r'your opponent', clean_step, re.IGNORECASE):
                    if re.search(r'Character', clean_step): step_flags["targets"]["target_opponent_character"] = 1
                    if re.search(r'Leader', clean_step): step_flags["targets"]["target_opponent_leader"] = 1
                elif re.search(r'your (?!opponent)', clean_step, re.IGNORECASE):
                    if re.search(r'Character', clean_step): step_flags["targets"]["target_your_character"] = 1
                    if re.search(r'Leader', clean_step): step_flags["targets"]["target_your_leader"] = 1
                
                if re.search(r'this Character|this card', clean_step, re.IGNORECASE):
                    step_flags["targets"]["target_self"] = 1
                if re.search(r'DON!!', clean_step): step_flags["targets"]["target_don"] = 1
                if re.search(r'deck', clean_step): step_flags["targets"]["target_deck"] = 1
                if re.search(r'hand', clean_step): step_flags["targets"]["target_hand"] = 1
                if re.search(r'Life', clean_step): step_flags["targets"]["target_life"] = 1

                # --- SCOPE ATTRIBUTION ---
                if re.search(r'up to 1', clean_step): step_flags["scopes"]["scope_up_to_1"] = 1
                elif re.search(r'up to 2', clean_step): step_flags["scopes"]["scope_up_to_2"] = 1
                elif re.search(r'up to 3', clean_step): step_flags["scopes"]["scope_up_to_3"] = 1
                elif re.search(r'up to 5', clean_step): step_flags["scopes"]["scope_up_to_5"] = 1
                elif re.search(r'all of your|all of their', clean_step): step_flags["scopes"]["scope_all"] = 1
                else: step_flags["scopes"]["scope_1"] = 1

                # --- COST PARSING (if step contains a colon) ---
                if ':' in clean_step:
                    cost_part, effect_part = clean_step.split(':', 1)
                    self._parse_costs(cost_part, step_flags["costs"])
                    clean_step = effect_part # Continue parsing actions from the effect part

                # --- ACTION & CONDITION PARSING ---
                self._parse_actions(clean_step, step_flags["actions"])
                self._parse_conditions(clean_step, step_flags["conditions"])

                effect_steps.append(EffectStep(
                    timing_flags=step_flags["timing"],
                    action_flags=step_flags["actions"],
                    condition_flags=step_flags["conditions"],
                    cost_flags=step_flags["costs"],
                    target_flags=step_flags["targets"],
                    scope_flags=step_flags["scopes"]
                ))

        return effect_steps

    def _parse_costs(self, text: str, flags: Dict[str, int]):
        if re.search(r'DON!! [−-](\d+)', text): flags["don_return"] = self._extract_amount(text)
        if re.search(r'rest this (?:Character|card)', text, re.IGNORECASE): flags["rest_self"] = 1
        if re.search(r'trash (\d+) card.*from your hand', text, re.IGNORECASE): flags["trash_hand"] = self._extract_amount(text)
        if re.search(r'➁|ⓧ|➀', text): flags["don_rest"] = self._extract_amount(text)

    def _parse_actions(self, text: str, flags: Dict[str, int]):
        if re.search(r'Draw (\d+)', text, re.IGNORECASE): flags["draw"] = self._extract_amount(text)
        if re.search(r'K\.O\.', text): flags["ko"] = 1
        if re.search(r'Look at (\d+)', text, re.IGNORECASE): flags["look"] = self._extract_amount(text)
        if re.search(r'reveal up to (\d+)', text, re.IGNORECASE): flags["reveal"] = self._extract_amount(text)
        if re.search(r'add .* to your hand', text, re.IGNORECASE): flags["add_to_hand"] = 1
        
        power_match = re.search(r'([+−-])(\d+) power', text, re.IGNORECASE)
        if power_match:
            val = int(power_match.group(2)) * (1 if power_match.group(1) == '+' else -1)
            flags["give_power"] = val
            
        cost_match = re.search(r'([+−-])(\d+) cost', text, re.IGNORECASE)
        if cost_match:
            val = int(cost_match.group(2)) * (1 if cost_match.group(1) == '+' else -1)
            flags["give_cost"] = val

        if re.search(r'set .* as active', text, re.IGNORECASE): flags["active"] = 1
        if re.search(r'cannot attack', text, re.IGNORECASE): flags["cannot_attack"] = 1
        if re.search(r'gains? \[Rush\]', text, re.IGNORECASE): flags["gain_ability"] = 1
        if re.search(r'returns? (\d+) DON!!', text, re.IGNORECASE): flags["remove_don"] = self._extract_amount(text)

    def _parse_conditions(self, text: str, flags: Dict[str, int]):
        if re.search(r'If your Leader', text, re.IGNORECASE): flags["leader_req"] = 1
        if re.search(r'with a cost of (\d+)', text, re.IGNORECASE): flags["cost_req"] = int(re.search(r'with a cost of (\d+)', text, re.IGNORECASE).group(1))
        if re.search(r'with (\d+) power or less', text, re.IGNORECASE): flags["power_req"] = int(re.search(r'with (\d+) power or less', text, re.IGNORECASE).group(1))
        if re.search(r'\{[^}]+\} type', text, re.IGNORECASE): flags["type_req"] = 1

    def parse_keywords(self, text: str) -> Dict[str, int]:
        flags = {k: 0 for k in KEYWORD_KEYS}
        for pattern, key in self.keyword_patterns.items():
            if re.search(pattern, text):
                flags[key] = 1
        return flags