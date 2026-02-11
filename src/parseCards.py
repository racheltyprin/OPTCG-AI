import re
import sys
import os
from typing import Dict, List, Optional, Any

# Ensure we can find featureslist in the same directory
sys.path.append(os.path.dirname(__file__))
from featureslist import TIMING_KEYS, KEYWORD_KEYS, ACTION_KEYS, CONDITION_KEYS, COST_KEYS

class CardEffectParser:
    def __init__(self):
        # 1. TIMING PATTERNS
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
        
        # 2. KEYWORD PATTERNS (These are also passive effects)
        self.keyword_patterns = {
            r'\[Rush\]': 'rush',
            r'\[Rush: Character\]': 'rush',
            r'\[Blocker\]': 'blocker',
            r'\[Double Attack\]': 'double_attack',
            r'\[Banish\]': 'banish',
            r'\[Unblockable\]': 'unblockable',
        }

    def _extract_amount(self, text: str, default: int = 1) -> int:
        """Helper to extract the first number found in a string, or return default."""
        match = re.search(r'([+−-]?\d+)', text)
        if match:
            val_str = match.group(1).replace('−', '-')
            return int(val_str)
        return default

    def parse_to_flags(self, text: str) -> Dict[str, Dict[str, int]]:
        flags = {
            "timing": {k: 0 for k in TIMING_KEYS},
            "keywords": {k: 0 for k in KEYWORD_KEYS},
            "actions": {k: 0 for k in ACTION_KEYS},
            "conditions": {k: 0 for k in CONDITION_KEYS},
            "costs": {k: 0 for k in COST_KEYS}
        }
        
        flags["conditions"]["cost_req"] = -999
        flags["conditions"]["power_req"] = -999
        
        if not text or text == '-':
            return flags

        # Clean HTML and normalize
        text_clean = re.sub(r'<[^>]+>', ' ', text)
        
        # --- 1. TIMING & KEYWORDS ---
        for pattern, key in self.timing_patterns.items():
            match = re.search(pattern, text_clean)
            if match:
                if key == 'don_x':
                    flags["timing"][key] = int(match.group(1))
                else:
                    flags["timing"][key] = 1
        
        for pattern, key in self.keyword_patterns.items():
            if re.search(pattern, text_clean):
                flags["keywords"][key] = 1
                # Keywords like Banish, Double Attack, Rush, Blocker are passive effects
                flags["timing"]["passive"] = 1

        # --- 2. PASSIVE DETECTION (Sentences) ---
        sentences = [s.strip() for s in re.split(r'<br>|\. (?=\[|This|Your|Opponent|If|All)', text_clean) if s.strip()]
        for sentence in sentences:
            if not sentence.startswith('[') and not re.search(r'^Then,', sentence):
                if re.search(r'cannot|must|gain|is|has|If|can attack', sentence, re.IGNORECASE):
                    flags["timing"]["passive"] = 1
                    break

        # --- 3. SPLIT INTO COST AND EFFECT ---
        cost_split_match = re.search(r'([^:]*(?:DON!! [−-]\d+|rest this Character|ⓧ|➀|➁|trash \d+ card.*from your hand))[:]', text_clean, re.IGNORECASE)
        
        if cost_split_match:
            cost_part = cost_split_match.group(1)
            effect_part = text_clean[cost_split_match.end():]
        else:
            don_return_match = re.search(r'DON!! [−-]\d+', text_clean)
            if don_return_match:
                cost_part = don_return_match.group(0)
                effect_part = text_clean
            else:
                cost_part = ""
                effect_part = text_clean

        # --- 4. COST PARSING ---
        if cost_part:
            if re.search(r'DON!! x(\d+)', cost_part): 
                flags["costs"]["don_attach"] = self._extract_amount(re.search(r'DON!! x(\d+)', cost_part).group(0))
            don_minus = re.search(r'DON!! [−-](\d+)', cost_part)
            if don_minus: 
                flags["costs"]["don_return"] = int(don_minus.group(1))
            if re.search(r'[ⓧ➀➁]|rest \d+ of your DON!!', cost_part):
                if 'ⓧ' in cost_part or '➀' in cost_part: flags["costs"]["don_rest"] = 1
                elif '➁' in cost_part: flags["costs"]["don_rest"] = 2
                else: flags["costs"]["don_rest"] = self._extract_amount(cost_part)
            if re.search(r'trash (\d+) card.*from your hand', cost_part, re.IGNORECASE):
                flags["costs"]["trash_hand"] = self._extract_amount(cost_part)
            if re.search(r'trash (\d+) card.*from (?:the top of )?your deck', cost_part, re.IGNORECASE):
                flags["costs"]["trash_deck"] = self._extract_amount(cost_part)
            if re.search(r'trash (\d+) card.*from your Life', cost_part, re.IGNORECASE):
                flags["costs"]["trash_life"] = self._extract_amount(cost_part)
            if re.search(r'rest this (?:Character|Stage|card)', cost_part, re.IGNORECASE):
                flags["costs"]["rest_self"] = 1
            if re.search(r'rest (\d+) of your (?:Characters|cards)', cost_part, re.IGNORECASE):
                flags["costs"]["rest_other"] = self._extract_amount(cost_part)

        # --- 5. ACTION PARSING ---
        action_text = re.sub(r'\[[^\]]+\]', '', text_clean)
        
        if re.search(r'\bDraw (\d+) card', action_text, re.IGNORECASE):
            flags["actions"]["draw"] = self._extract_amount(re.search(r'\bDraw (\d+) card', action_text, re.IGNORECASE).group(0))
        if re.search(r'Look at (\d+) cards', action_text, re.IGNORECASE):
            flags["actions"]["look"] = self._extract_amount(re.search(r'Look at (\d+) cards', action_text, re.IGNORECASE).group(0))
        if re.search(r'reveal up to (\d+)', action_text, re.IGNORECASE):
            flags["actions"]["reveal"] = self._extract_amount(re.search(r'reveal up to (\d+)', action_text, re.IGNORECASE).group(0))
        if re.search(r'add .* to your hand', action_text, re.IGNORECASE):
            flags["actions"]["add_to_hand"] = 1
        if re.search(r'place .* at (?:the )?(?:top|bottom) of (?:your |your opponent\'s )?deck', action_text, re.IGNORECASE):
            flags["actions"]["place_deck"] = 1
        if re.search(r'shuffle (?:your |your opponent\'s )?deck', action_text, re.IGNORECASE):
            flags["actions"]["shuffle"] = 1
        if re.search(r'\bPlay up to (\d+)', action_text, re.IGNORECASE):
            flags["actions"]["play"] = self._extract_amount(re.search(r'\bPlay up to (\d+)', action_text, re.IGNORECASE).group(0))
        if re.search(r'\bRest (?:up to (\d+)|all|the)', action_text, re.IGNORECASE):
            match = re.search(r'\bRest (?:up to (\d+)|all|the)', action_text, re.IGNORECASE)
            flags["actions"]["rest"] = 99 if 'all' in match.group(0).lower() else self._extract_amount(match.group(0))
        if re.search(r'Set (?:up to (\d+)|all|the) .* as active', action_text, re.IGNORECASE):
            match = re.search(r'Set (?:up to (\d+)|all|the) .* as active', action_text, re.IGNORECASE)
            flags["actions"]["active"] = 99 if 'all' in match.group(0).lower() else self._extract_amount(match.group(0))
        if re.search(r'\bK\.O\.', action_text) and not re.search(r'cannot be K\.O\.\'d', action_text, re.IGNORECASE):
            match = re.search(r'K\.O\. (?:up to (\d+)|all|the)', action_text, re.IGNORECASE)
            flags["actions"]["ko"] = self._extract_amount(match.group(0)) if match else 1
        if re.search(r'Remove .* from the field', action_text, re.IGNORECASE):
            flags["actions"]["remove_field"] = 1
        if re.search(r'Return .* to (?:the )?owner\'s hand', action_text, re.IGNORECASE):
            flags["actions"]["return_to_hand"] = 1
        if re.search(r'Add (\d+) card.* to (?:the )?(?:top|bottom) of .* Life', action_text, re.IGNORECASE):
            flags["actions"]["add_life"] = self._extract_amount(re.search(r'Add (\d+) card.* to (?:the )?(?:top|bottom) of .* Life', action_text, re.IGNORECASE).group(0))
        if re.search(r'trash (\d+) card.* from .* Life', action_text, re.IGNORECASE):
            flags["actions"]["trash_life"] = self._extract_amount(re.search(r'trash (\d+) card.* from .* Life', action_text, re.IGNORECASE).group(0))
        if re.search(r'Look at (\d+) card.* from .* Life', action_text, re.IGNORECASE):
            flags["actions"]["look_life"] = self._extract_amount(re.search(r'Look at (\d+) card.* from .* Life', action_text, re.IGNORECASE).group(0))
        
        # Power/Cost mods
        power_matches = re.findall(r'([+−-])(\d+) power', action_text, re.IGNORECASE)
        if power_matches:
            total_power = 0
            for sign, val in power_matches:
                total_power += int(val) * (1 if sign == '+' else -1)
            flags["actions"]["give_power"] = total_power
            
        cost_matches = re.findall(r'([+−-])(\d+) cost', action_text, re.IGNORECASE)
        if cost_matches:
            total_cost = 0
            for sign, val in cost_matches:
                total_cost += int(val) * (1 if sign == '+' else -1)
            flags["actions"]["give_cost"] = total_cost
        
        if re.search(r'set up to (\d+) of your DON!! cards as active', action_text, re.IGNORECASE):
            flags["actions"]["set_don"] = self._extract_amount(re.search(r'set up to (\d+) of your DON!! cards as active', action_text, re.IGNORECASE).group(0))
        elif re.search(r'Set up to (\d+) of your DON!! cards as active', action_text, re.IGNORECASE):
            flags["actions"]["set_don"] = self._extract_amount(re.search(r'Set up to (\d+) of your DON!! cards as active', action_text, re.IGNORECASE).group(0))
        if re.search(r'Add up to (\d+) DON!! card.* from your DON!! deck', action_text, re.IGNORECASE):
            flags["actions"]["add_don"] = self._extract_amount(re.search(r'Add up to (\d+) DON!! card.* from your DON!! deck', action_text, re.IGNORECASE).group(0))
        if re.search(r'return (\d+) DON!! card.* to your DON!! deck', action_text, re.IGNORECASE):
            flags["actions"]["remove_don"] = self._extract_amount(re.search(r'return (\d+) DON!! card.* to your DON!! deck', action_text, re.IGNORECASE).group(0))
        if re.search(r'Give .* up to (\d+) .* DON!! card', action_text, re.IGNORECASE):
            flags["actions"]["attach_don"] = self._extract_amount(re.search(r'Give .* up to (\d+) .* DON!! card', action_text, re.IGNORECASE).group(0))
        
        if re.search(r'gains? \[?(?:Rush|Blocker|Double Attack|Banish|Unblockable)\]?', action_text, re.IGNORECASE):
            flags["actions"]["gain_ability"] = 1
        if re.search(r'cannot attack', action_text, re.IGNORECASE):
            flags["actions"]["cannot_attack"] = 1
        if re.search(r'cannot be K\.O\.\'d', action_text, re.IGNORECASE):
            flags["actions"]["cannot_be_ko"] = 1
        if re.search(r'must attack', action_text, re.IGNORECASE):
            flags["actions"]["must_attack"] = 1
        if re.search(r'Change the attack target', action_text, re.IGNORECASE):
            flags["actions"]["change_target"] = 1
        if re.search(r'cannot be removed from the field', action_text, re.IGNORECASE):
            flags["actions"]["cannot_be_removed"] = 1
        if re.search(r'can attack Characters on the turn in which (?:it is|they are) played', action_text, re.IGNORECASE):
            flags["actions"]["can_attack_played_turn"] = 1

        # --- 6. CONDITION PARSING ---
        if re.search(r'If your Leader', action_text, re.IGNORECASE): flags["conditions"]["leader_req"] = 1
        if re.search(r'If you have (\d+) or (?:less|more) (?:cards|Life|DON!!)', action_text, re.IGNORECASE):
            flags["conditions"]["count_req"] = self._extract_amount(action_text)
        if re.search(r'If the number of DON!!', action_text, re.IGNORECASE): flags["conditions"]["don_req"] = 1
        if re.search(r'If you have (?:no other|a) .* Character', action_text, re.IGNORECASE): flags["conditions"]["character_req"] = 1
        if re.search(r'If you have (?:less|more|equal) Life', action_text, re.IGNORECASE): flags["conditions"]["life_req"] = 1
        if re.search(r'in battle', action_text, re.IGNORECASE): flags["conditions"]["battle_req"] = 1
        if re.search(r'\{[^}]+\} type', action_text, re.IGNORECASE): flags["conditions"]["type_req"] = 1
        if re.search(r'(?:red|blue|green|purple|black|yellow) Character', action_text, re.IGNORECASE): flags["conditions"]["color_req"] = 1
        
        cost_req_match = re.search(r'with a cost of (\d+)', action_text, re.IGNORECASE)
        if cost_req_match:
            flags["conditions"]["cost_req"] = int(cost_req_match.group(1))
            
        power_req_match = re.search(r'with (\d+) power or less', action_text, re.IGNORECASE)
        if power_req_match:
            flags["conditions"]["power_req"] = int(power_req_match.group(1))
            
        threshold_match = re.search(r'(\d+) or (?:more|less) cards in your trash', action_text, re.IGNORECASE)
        if threshold_match:
            flags["conditions"]["threshold_req"] = int(threshold_match.group(1))
            
        if re.search(r'by &lt;([^&]+)&gt; attribute cards', action_text, re.IGNORECASE):
            flags["conditions"]["attribute_req"] = 1

        return flags