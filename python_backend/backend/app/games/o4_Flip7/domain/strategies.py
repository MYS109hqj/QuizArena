from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Protocol


class Strategy(Protocol):
    def choose_turn(self, *, round_score: int, bust_probability: float,
                    must_hit: bool, rng: random.Random) -> str: ...


@dataclass(frozen=True)
class RandomStrategy:
    draw_chance: float = 0.6

    def choose_turn(self, *, round_score: int, bust_probability: float,
                    must_hit: bool, rng: random.Random) -> str:
        return "draw" if must_hit or rng.random() < self.draw_chance else "stop"


@dataclass(frozen=True)
class ScoreThresholdStrategy:
    threshold: int = 20

    def choose_turn(self, *, round_score: int, bust_probability: float,
                    must_hit: bool, rng: random.Random) -> str:
        return "draw" if must_hit or round_score < self.threshold else "stop"


@dataclass(frozen=True)
class RiskThresholdStrategy:
    threshold: float = 0.25

    def choose_turn(self, *, round_score: int, bust_probability: float,
                    must_hit: bool, rng: random.Random) -> str:
        return "draw" if must_hit or bust_probability <= self.threshold else "stop"


def build_strategy(config: Dict[str, Any]) -> Strategy:
    kind = config.get("strategy", "random")
    if kind == "score_threshold":
        return ScoreThresholdStrategy(max(0, int(config.get("threshold", 20))))
    if kind == "risk_threshold":
        value = float(config.get("threshold", 0.25))
        return RiskThresholdStrategy(min(1.0, max(0.0, value)))
    return RandomStrategy()
