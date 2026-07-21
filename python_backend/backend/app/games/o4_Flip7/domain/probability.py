from __future__ import annotations

from typing import Any, Dict, Iterable

from .cards import Flip7Card


def would_immediately_duplicate(hand: Iterable[Flip7Card], incoming: Flip7Card) -> bool:
    """Card-face risk only: intentionally ignores Second Chance."""
    if incoming.card_type != "number" or incoming.ability == "unlucky_7":
        return False
    face_up_numbers = [card for card in hand
                       if card.card_type == "number" and not card.face_down]
    same = [card for card in face_up_numbers if card.value == incoming.value]
    if not same:
        return False
    if incoming.value == 13:
        has_lucky = incoming.ability == "lucky_13" or any(
            card.ability == "lucky_13" for card in same
        )
        return len(same) >= (2 if has_lucky else 1)
    return True


def next_draw_bust_probability(hand: Iterable[Flip7Card],
                               draw_pile: Iterable[Flip7Card]) -> Dict[str, Any]:
    pile = list(draw_pile)
    bust_cards = sum(1 for card in pile if would_immediately_duplicate(hand, card))
    total = len(pile)
    return {
        "probability": bust_cards / total if total else 0.0,
        "bust_cards": bust_cards,
        "remaining_cards": total,
    }
