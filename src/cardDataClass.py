from dataclasses import dataclass, field
from typing import List, Dict, Optional
import torch
import sys
import os

# Ensure we can find featureslist in the same directory
sys.path.append(os.path.dirname(__file__))
from featureslist import (
    TIMING_KEYS,
    KEYWORD_KEYS,
    ACTION_KEYS,
    CONDITION_KEYS,
    COST_KEYS
)

@dataclass
class Card:
    # ID
    card_id: str
    name: str
    category: str  # event, character, stage, leader
    set: str

    # Main Card Descriptors
    cost: int
    power: int
    counter: int
    life: int
    colors: List[str]
    types: List[str]
    attributes: List[str]
    trigger: bool

    # Effect Structure
    timing_flags: Dict[str, int]
    keyword_flags: Dict[str, int]
    effect_action_flags: Dict[str, int]
    conditions: Dict[str, int]
    cost_flags: Dict[str, int] = field(default_factory=dict)

    learned_embedding: Optional[torch.Tensor] = field(default=None)

    def numeric_features(self) -> torch.Tensor:
        return torch.tensor([
            float(self.cost or 0),
            float(self.power or 0),
            float(self.counter or 0),
            float(self.life or 0)
        ], dtype=torch.float32)

    def flags_to_tensor(self) -> torch.Tensor:
        timing = [float(self.timing_flags.get(k, 0)) for k in TIMING_KEYS]
        keywords = [float(self.keyword_flags.get(k, 0)) for k in KEYWORD_KEYS]
        actions = [float(self.effect_action_flags.get(k, 0)) for k in ACTION_KEYS]
        
        # Special handling for cost_req and power_req to replace sentinel -999 with 0
        conds = []
        for k in CONDITION_KEYS:
            val = float(self.conditions.get(k, 0))
            if val == -999:
                val = 0.0
            conds.append(val)
            
        costs = [float(self.cost_flags.get(k, 0)) for k in COST_KEYS]

        return torch.tensor(
            timing + keywords + actions + conds + costs,
            dtype=torch.float32
        )

    def to_tensor(self) -> torch.Tensor:
        parts = [
            self.numeric_features(),
            self.flags_to_tensor()
        ]
        if self.learned_embedding is not None:
            parts.append(self.learned_embedding)
        return torch.cat(parts)