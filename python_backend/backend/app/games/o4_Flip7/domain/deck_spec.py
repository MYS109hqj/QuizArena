from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .cards import Flip7Card


ACTION_NAMES = {
    "flip_3": "Flip 3", "flip_4": "Flip 4", "freeze": "Freeze",
    "second_chance": "Second Chance", "just_one_more": "Just One More",
    "swap": "Swap", "steal": "Steal", "discard": "Discard",
}
MODIFIER_DEFS = {
    "times_2": ("×2", 0, 2.0), "divide_2": ("÷2", 0, 0.5),
    "plus_2": ("+2", 2, 1.0), "plus_4": ("+4", 4, 1.0),
    "plus_6": ("+6", 6, 1.0), "plus_8": ("+8", 8, 1.0),
    "plus_10": ("+10", 10, 1.0), "minus_2": ("-2", -2, 1.0),
    "minus_4": ("-4", -4, 1.0), "minus_6": ("-6", -6, 1.0),
    "minus_8": ("-8", -8, 1.0), "minus_10": ("-10", -10, 1.0),
}


class DeckSpecError(ValueError):
    pass


@dataclass
class DeckSpec:
    preset: str = "base"
    name: str = "官方基础版"
    number_max: int = 12
    special_numbers: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, int] = field(default_factory=dict)
    modifiers: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None, preset: str = "custom") -> "DeckSpec":
        data = data or {}
        return cls(
            preset=preset,
            name=str(data.get("name") or "自定义牌组")[:40],
            number_max=int(data.get("number_max", 12)),
            special_numbers=dict(data.get("special_numbers") or {}),
            actions={key: int(value) for key, value in (data.get("actions") or {}).items()},
            modifiers={key: int(value) for key, value in (data.get("modifiers") or {}).items()},
        ).validated()

    def validated(self) -> "DeckSpec":
        if not 1 <= self.number_max <= 30:
            raise DeckSpecError("最大数字必须在1至30之间")
        unknown_actions = set(self.actions) - set(ACTION_NAMES)
        unknown_modifiers = set(self.modifiers) - set(MODIFIER_DEFS)
        if unknown_actions or unknown_modifiers:
            raise DeckSpecError("牌组包含未知卡牌")
        for count in [*self.actions.values(), *self.modifiers.values()]:
            if count < 0 or count > 100:
                raise DeckSpecError("单种卡牌数量必须在0至100之间")
        if self.special_numbers.get("unlucky_7") and self.number_max < 7:
            raise DeckSpecError("数字范围包含7时才能启用Unlucky 7")
        if self.special_numbers.get("lucky_13") and self.number_max < 13:
            raise DeckSpecError("数字范围包含13时才能启用Lucky 13")
        if self.total_cards > 2000:
            raise DeckSpecError("牌组总数不能超过2000张")
        return self

    @property
    def number_count(self) -> int:
        return 1 + self.number_max * (self.number_max + 1) // 2

    @property
    def total_cards(self) -> int:
        return self.number_count + sum(self.actions.values()) + sum(self.modifiers.values())

    def build(self) -> List[Flip7Card]:
        self.validated()
        cards: List[Flip7Card] = []
        zero_ability = "zero" if self.special_numbers.get("zero") else ""
        cards.append(Flip7Card("number", "0", value=0, ability=zero_ability))
        for value in range(1, self.number_max + 1):
            for copy_index in range(value):
                ability = ""
                name = str(value)
                if value == 7 and copy_index == 0 and self.special_numbers.get("unlucky_7"):
                    ability, name = "unlucky_7", "Unlucky 7"
                elif value == 13 and copy_index == 0 and self.special_numbers.get("lucky_13"):
                    ability, name = "lucky_13", "Lucky 13"
                cards.append(Flip7Card("number", name, value=value, ability=ability))
        for key, count in self.actions.items():
            cards.extend(Flip7Card("action", ACTION_NAMES[key]) for _ in range(count))
        for key, count in self.modifiers.items():
            name, value, multiplier = MODIFIER_DEFS[key]
            cards.extend(Flip7Card("modifier", name, value=value, multiplier=multiplier)
                         for _ in range(count))
        return cards

    def public(self) -> Dict[str, Any]:
        return {
            "preset": self.preset, "name": self.name, "number_max": self.number_max,
            "number_count": self.number_count, "total_cards": self.total_cards,
            "special_numbers": self.special_numbers, "actions": self.actions,
            "modifiers": self.modifiers,
        }

    def summary(self) -> str:
        return f"{self.name} · 0–{self.number_max} · {self.total_cards}张"


def official_base_spec() -> DeckSpec:
    return DeckSpec(
        preset="base", name="官方基础版", number_max=12,
        actions={"flip_3": 3, "freeze": 3, "second_chance": 3},
        modifiers={"times_2": 1, "plus_2": 1, "plus_4": 1,
                   "plus_6": 1, "plus_8": 1, "plus_10": 1},
    )


def official_vengeance_spec() -> DeckSpec:
    return DeckSpec(
        preset="vengeance", name="官方复仇版", number_max=13,
        special_numbers={"zero": True, "unlucky_7": 1, "lucky_13": 1},
        actions={"flip_4": 2, "just_one_more": 2, "swap": 2,
                 "steal": 2, "discard": 2},
        modifiers={"divide_2": 1, "minus_2": 1, "minus_4": 1,
                   "minus_6": 1, "minus_8": 1, "minus_10": 1},
    )
