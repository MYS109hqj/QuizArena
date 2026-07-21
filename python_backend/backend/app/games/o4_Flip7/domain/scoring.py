from __future__ import annotations

from typing import Any, Dict, Iterable

from .cards import Flip7Card


def score_hand(hand: Iterable[Flip7Card], *, busted: bool, brutal: bool,
               preset: str, has_flip7: bool, flip7_bonus: int) -> int:
    if busted and not brutal:
        return 0
    face_up = [card for card in hand if not card.face_down]
    numbers = [card for card in face_up if card.card_type == "number"]
    modifiers = [card for card in face_up if card.card_type == "modifier"]
    number_total = 0 if any(card.ability == "zero" for card in numbers) else sum(
        card.value for card in numbers
    )
    has_times_two = any(card.multiplier == 2 for card in modifiers)
    has_divide_two = any(card.multiplier == 0.5 for card in modifiers)
    if preset == "base":
        score = number_total * 2 if has_times_two else number_total
        score += sum(card.value for card in modifiers if card.multiplier == 1 and card.value > 0)
    elif preset == "vengeance":
        score = number_total // 2 if has_divide_two else number_total
        score += sum(card.value for card in modifiers if card.multiplier == 1 and card.value < 0)
    else:
        score = number_total * 2 if has_times_two else number_total
        score = score // 2 if has_divide_two else score
        score += sum(card.value for card in modifiers if card.multiplier == 1)
    if has_flip7:
        score += flip7_bonus
    return score if brutal else max(0, score)
