from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class YearlyDelta:
    year_offset: int
    temp_delta_c: float
    humidity_delta_pct: float

@dataclass
class PredictionResult:
    deltas: list
    sources: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    effect_summary: dict = field(default_factory=dict)

class InterventionModule(ABC):
    module_id: str = "base"

    @abstractmethod
    def accepts(self, parsed: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def predict(self, parsed: dict, baseline: dict) -> PredictionResult:
        raise NotImplementedError

    def cite(self) -> list:
        return []

class InterventionRegistry:
    def __init__(self):
        self._modules: list = []

    def register(self, module: InterventionModule) -> None:
        self._modules.append(module)

    def all_modules(self) -> list:
        return list(self._modules)

    def find_for(self, parsed: dict) -> Optional[InterventionModule]:
        for m in self._modules:
            try:
                if m.accepts(parsed):
                    return m
            except Exception:
                continue
        return None

registry = InterventionRegistry()
