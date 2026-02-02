from dataclasses import dataclass, field
from typing import List, Dict
import torch
from featureslist import (
    TIMING_KEYS,
    KEYWORD_KEYS,
    ACTION_KEYS,
    CONDITION_KEYS
)

@dataclass
class Card:
    #ID
    card_id: str
    name: str
    category: str #event, character, stage, leader
    set: str

    #Main Card Descriptors
    cost: int
    power: int
    counter: int
    life: int
    colors: List[str]
    types: List[str] #ex strawhat crew, kuja pirates, navy, etc.
    attributes: List[str] #ex strike, slash, ranged, etc.
    trigger: bool

    #Effect Structure -- see PersonalReferences/CardCategorization.txt
    timing_flags: Dict[str, int]
    keyword_flags: Dict[str, int]
    effect_action_flags: Dict[str, int]
    conditions: Dict[str, int]

    #cards can exist with or without an embedding value
    learned_embedding: torch.Tensor | None = field(default=None)

    #translates numeric features to tensor
    def numeric_features(self) -> torch.Tensor:
        return torch.tensor([
            self.cost,
            self.power or 0,
            self.counter or 0
        ], dtype=torch.float32)

    #uses set ordering of flags and translates them to tensor
    def flags_to_tensor(self) -> torch.Tensor:
        timing = [self.timing_flags[k] for k in TIMING_KEYS]
        keywords = [self.keyword_flags[k] for k in KEYWORD_KEYS]
        actions = [self.effect_action_flags[k] for k in ACTION_KEYS]
        conds = [self.conditions[k] for k in CONDITION_KEYS]

        return torch.tensor(
            timing + keywords + actions + conds,
            dtype=torch.float32
        )
    
    #combines numeric and flag tensors
    def to_tensor(self) -> torch.Tensor:
        parts = [
            self.numeric_features(),
            self.flags_to_tensor()
        ]

        if self.learned_embedding is not None:
            parts.append(self.learned_embedding)

        return torch.cat(parts)