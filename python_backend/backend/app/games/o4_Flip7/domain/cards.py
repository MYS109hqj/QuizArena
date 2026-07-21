from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(eq=False)
class Flip7Card:
    card_type: str
    name: str
    value: int = 0
    multiplier: float = 1.0
    ability: str = ""
    id: str = ""
    face_down: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid.uuid4().hex[:10]

    def public(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.card_type, "name": self.name,
            "value": self.value, "multiplier": self.multiplier,
            "ability": self.ability, "face_down": self.face_down,
        }
