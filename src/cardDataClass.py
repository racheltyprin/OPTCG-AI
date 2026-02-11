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
    COST_KEYS,
    TARGET_KEYS,
    SCOPE_KEYS
)

@dataclass
class EffectStep:
    timing_flags: Dict[str, int]
    action_flags: Dict[str, int]
    condition_flags: Dict[str, int]
    cost_flags: Dict[str, int]
    target_flags: Dict[str, int]
    scope_flags: Dict[str, int]

    def to_tensor(self) -> torch.Tensor:
        timing = [float(self.timing_flags.get(k, 0)) for k in TIMING_KEYS]
        actions = [float(self.action_flags.get(k, 0)) for k in ACTION_KEYS]
        
        conds = []
        for k in CONDITION_KEYS:
            val = float(self.condition_flags.get(k, 0))
            if val == -999: val = 0.0
            conds.append(val)
            
        costs = [float(self.cost_flags.get(k, 0)) for k in COST_KEYS]
        targets = [float(self.target_flags.get(k, 0)) for k in TARGET_KEYS]
        scopes = [float(self.scope_flags.get(k, 0)) for k in SCOPE_KEYS]

        return torch.tensor(
            timing + actions + conds + costs + targets + scopes,
            dtype=torch.float32
        )

@dataclass
class Card:
    card_id: str
    name: str
    category: str
    set: str
    cost: int
    power: int
    counter: int
    life: int
    colors: List[str]
    types: List[str]
    attributes: List[str]
    trigger: bool
    
    # Global card keywords (Rush, Blocker, etc.)
    keyword_flags: Dict[str, int]
    
    # List of sequential effect steps
    effects: List[EffectStep] = field(default_factory=list)
    
    learned_embedding: Optional[torch.Tensor] = field(default=None)

    def numeric_features(self) -> torch.Tensor:
        return torch.tensor([
            float(self.cost or 0),
            float(self.power or 0),
            float(self.counter or 0),
            float(self.life or 0)
        ], dtype=torch.float32)

    def to_tensor(self, max_steps: int = 4) -> torch.Tensor:
        # 1. Numeric features
        parts = [self.numeric_features()]
        
        # 2. Global keywords
        keywords = torch.tensor([float(self.keyword_flags.get(k, 0)) for k in KEYWORD_KEYS], dtype=torch.float32)
        parts.append(keywords)
        
        # 3. Effect steps (padded to max_steps)
        step_tensors = []
        for i in range(max_steps):
            if i < len(self.effects):
                step_tensors.append(self.effects[i].to_tensor())
            else:
                # Zero tensor of the same size as an EffectStep tensor
                # Size = len(TIMING) + len(ACTION) + len(CONDITION) + len(COST) + len(TARGET) + len(SCOPE)
                size = len(TIMING_KEYS) + len(ACTION_KEYS) + len(CONDITION_KEYS) + len(COST_KEYS) + len(TARGET_KEYS) + len(SCOPE_KEYS)
                step_tensors.append(torch.zeros(size, dtype=torch.float32))
        
        parts.extend(step_tensors)

        if self.learned_embedding is not None:
            parts.append(self.learned_embedding)

        return torch.cat(parts)