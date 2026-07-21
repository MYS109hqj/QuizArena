import asyncio

from app.games.o4_Flip7.game import Flip7Card, o4Flip7Game
from app.games.o4_Flip7.domain.deck_spec import DeckSpec, DeckSpecError
from app.games.o4_Flip7.domain.probability import next_draw_bust_probability


def game(vengeance=False, brutal=False):
    result = o4Flip7Game("test")
    result.round_end_delay = 0
    result.game_rules["vengeance_mode"] = vengeance
    result.game_rules["deck_preset"] = "vengeance" if vengeance else "base"
    result.game_rules["brutal_mode"] = brutal
    result.player_order = ["a", "b"]
    result.player_state = {pid: result._blank_player_state() for pid in result.player_order}
    return result


def test_base_deck_has_94_cards_and_no_thirteen():
    subject = game()
    subject._init_deck()
    assert len(subject.deck) == 94
    numbers = [card.value for card in subject.deck if card.card_type == "number"]
    assert len(numbers) == 79
    assert max(numbers) == 12


def test_vengeance_deck_components():
    subject = game(vengeance=True)
    subject._init_deck()
    assert len([c for c in subject.deck if c.card_type == "number"]) == 92
    assert len([c for c in subject.deck if c.card_type == "action"]) == 10
    assert len([c for c in subject.deck if c.card_type == "modifier"]) == 6
    assert len(subject.deck) == 108
    assert len([c for c in subject.deck if c.ability == "lucky_13"]) == 1
    assert len([c for c in subject.deck if c.value == 13 and not c.ability]) == 12


def test_modifiers_are_scored_at_end_not_draw_order():
    subject = game()
    state = subject.player_state["a"]
    state["hand"] = [
        Flip7Card("modifier", "×2", multiplier=2),
        Flip7Card("number", "10", value=10),
        Flip7Card("modifier", "+4", value=4),
    ]
    assert subject._score_hand(state) == 24


def test_vengeance_floor_and_brutal_negative_score():
    subject = game(vengeance=True)
    state = subject.player_state["a"]
    state["hand"] = [Flip7Card("number", "2", value=2), Flip7Card("modifier", "-10", value=-10)]
    assert subject._score_hand(state) == 0
    subject.game_rules["brutal_mode"] = True
    assert subject._score_hand(state) == -8


def test_second_chance_is_consumed_by_duplicate():
    subject = game()
    state = subject.player_state["a"]
    state["second_chance"] = True
    state["hand"] = [Flip7Card("number", "8", value=8)]
    result = asyncio.run(subject._accept_card("a", Flip7Card("number", "8", value=8)))
    assert result["used_sc"] is True
    assert state["second_chance"] is False
    assert state["busted"] is False


def test_lucky_thirteen_busts_on_third_copy():
    subject = game(vengeance=True)
    state = subject.player_state["a"]
    state["hand"] = [subject._new_number(13, "lucky_13"), subject._new_number(13, "lucky_13")]
    result = asyncio.run(subject._accept_card("a", subject._new_number(13, "lucky_13")))
    assert result["bust"] is True


def test_lucky_thirteen_allows_a_normal_thirteen_in_either_draw_order():
    for first, second in [
        (Flip7Card("number", "Lucky 13", 13, ability="lucky_13"), Flip7Card("number", "13", 13)),
        (Flip7Card("number", "13", 13), Flip7Card("number", "Lucky 13", 13, ability="lucky_13")),
    ]:
        subject = game(vengeance=True)
        subject.player_state["a"]["hand"] = [first]
        result = asyncio.run(subject._accept_card("a", second))
        assert result["bust"] is False


def test_losing_lucky_thirteen_makes_two_plain_thirteens_bust():
    subject = game(vengeance=True)
    state = subject.player_state["a"]
    lucky = Flip7Card("number", "Lucky 13", 13, ability="lucky_13")
    state["hand"] = [lucky, Flip7Card("number", "13", 13)]
    state["hand"].remove(lucky)
    state["hand"].append(Flip7Card("number", "13", 13))
    result = subject._reconcile_hand("a")
    assert result["bust"] is True


def test_zero_scores_only_flip7_bonus_and_forces_future_hits():
    subject = game(vengeance=True)
    state = subject.player_state["a"]
    state["hand"] = [subject._new_number(0, "zero"), Flip7Card("number", "12", 12)]
    state["must_hit"] = True
    assert subject._score_hand(state) == 0
    state["has_flip7"] = True
    assert subject._score_hand(state) == subject.game_rules["flip7_bonus"]
    assert state["must_hit"] is True


def test_unlucky_seven_takes_precedence_over_an_existing_seven():
    subject = game(vengeance=True)
    state = subject.player_state["a"]
    state["hand"] = [Flip7Card("number", "7", 7), Flip7Card("number", "10", 10),
                     Flip7Card("modifier", "-4", -4)]
    result = asyncio.run(subject._accept_card("a", subject._new_number(7, "unlucky_7")))
    assert result["bust"] is False
    assert len(state["hand"]) == 1
    assert state["hand"][0].ability == "unlucky_7"


def test_new_round_discards_second_chance_and_hand():
    subject = game()
    subject.player_state["a"]["score"] = 20
    subject.player_state["a"]["second_chance"] = True
    subject.player_state["a"]["hand"] = [Flip7Card("action", "Second Chance")]
    subject._reset_round()
    assert subject.player_state["a"]["score"] == 20
    assert subject.player_state["a"]["second_chance"] is False
    assert subject.player_state["a"]["hand"] == []


def test_normal_draw_rotates_to_next_active_player():
    subject = game()
    subject.state = "player_turn"
    subject.current_player = "a"
    subject.turn_cursor = 0
    subject.deck = [Flip7Card("number", "5", value=5)]
    subject.broadcast = lambda data: _noop()
    subject.broadcast_game_state = _noop
    asyncio.run(subject._draw_for("a"))
    assert subject.current_player == "b"


def test_rotation_skips_stopped_frozen_and_busted_players():
    subject = o4Flip7Game("test")
    subject.player_order = ["a", "b", "c", "d"]
    subject.player_state = {pid: subject._blank_player_state() for pid in subject.player_order}
    subject.current_player = "a"
    subject.turn_cursor = 0
    subject.player_state["b"]["stopped"] = True
    subject.player_state["c"]["frozen"] = True
    subject.broadcast_game_state = _noop
    asyncio.run(subject._advance_turn())
    assert subject.current_player == "d"


def test_round_ends_when_every_player_is_inactive():
    subject = game()
    subject.player_state["a"]["stopped"] = True
    subject.player_state["b"]["busted"] = True
    ended = []

    async def mark_ended():
        ended.append(True)

    subject._end_round = mark_ended
    asyncio.run(subject._advance_turn())
    assert ended == [True]


def test_seventh_unique_number_ends_round_immediately():
    subject = game()
    subject.state = "player_turn"
    subject.current_player = "a"
    subject.turn_cursor = 0
    subject.player_state["a"]["hand"] = [Flip7Card("number", str(n), value=n) for n in range(1, 7)]
    subject.deck = [Flip7Card("number", "7", value=7)]
    ended = []
    subject.broadcast = lambda data: _noop()

    async def mark_ended():
        ended.append(True)

    subject._end_round = mark_ended
    asyncio.run(subject._draw_for("a"))
    assert ended == [True]
    assert subject.player_state["a"]["has_flip7"] is True


async def _noop(*args, **kwargs):
    return None


def forced_game(vengeance=False):
    subject = game(vengeance=vengeance)
    subject.state = "player_turn"
    subject.current_player = "a"
    subject.turn_cursor = 0
    subject.broadcast = _noop
    subject.broadcast_game_state = _noop
    subject._resume_after_effect = _noop
    return subject


def put_deck_in_draw_order(subject, cards):
    subject.deck = list(reversed(cards))


def start_effect(subject, actor, card, target, forced_cards=None):
    asyncio.run(subject._request_effect({"actor": actor, "card": card}))
    assert subject.pending_action is not None
    if forced_cards is not None:
        put_deck_in_draw_order(subject, forced_cards)
    asyncio.run(subject._resolve_selection(actor, {"target_id": target}))


def test_flip_four_defers_modifier_until_all_four_cards_are_drawn():
    subject = forced_game(vengeance=True)
    start_effect(subject, "a", Flip7Card("action", "Flip 4"), "b", [
        Flip7Card("modifier", "-6", -6), Flip7Card("number", "1", 1),
        Flip7Card("number", "2", 2), Flip7Card("number", "3", 3)])
    assert subject.pending_action["type"] == "modifier"
    assert [c.value for c in subject.player_state["b"]["hand"] if c.card_type == "number"] == [1, 2, 3]


def test_flip_three_bust_discards_actions_revealed_during_the_sequence():
    subject = forced_game()
    subject.player_state["b"]["hand"] = [Flip7Card("number", "5", 5)]
    start_effect(subject, "a", Flip7Card("action", "Flip 3"), "b", [
        Flip7Card("action", "Freeze"), Flip7Card("number", "5", 5)])
    assert subject.player_state["b"]["busted"] is True
    assert subject.pending_action is None
    assert subject.forced_stack == []


def test_second_chance_revealed_in_flip_three_immediately_saves_later_duplicate():
    subject = forced_game()
    subject.player_state["b"]["hand"] = [Flip7Card("number", "5", 5)]
    start_effect(subject, "a", Flip7Card("action", "Flip 3"), "b", [
        Flip7Card("action", "Second Chance"), Flip7Card("number", "5", 5),
        Flip7Card("number", "6", 6)])
    assert subject.player_state["b"]["busted"] is False
    assert subject.player_state["b"]["second_chance"] is False
    assert 6 in [c.value for c in subject.player_state["b"]["hand"] if c.card_type == "number"]
    assert subject.pending_action is None


def test_nested_flip_four_resolves_inner_actions_before_outer_remaining_actions():
    subject = forced_game(vengeance=True)
    # Give every card-moving action a legal target.
    subject.player_state["a"]["hand"] = [Flip7Card("number", "9", 9)]
    subject.player_state["b"]["hand"] = [Flip7Card("number", "8", 8)]
    start_effect(subject, "a", Flip7Card("action", "Flip 4"), "b", [
        Flip7Card("action", "Flip 4"), Flip7Card("action", "Discard"),
        Flip7Card("number", "1", 1), Flip7Card("number", "2", 2)])
    assert subject.pending_action["type"] == "flip4"
    put_deck_in_draw_order(subject, [Flip7Card("action", "Steal"),
                                     Flip7Card("number", "3", 3),
                                     Flip7Card("number", "4", 4),
                                     Flip7Card("number", "5", 5)])
    asyncio.run(subject._resolve_selection("b", {"target_id": "a"}))
    # The nested Steal must resolve before the outer Discard.
    assert subject.pending_action["type"] == "steal"
    steal_target = subject.pending_action["targets"][0]
    stolen = subject.player_state[steal_target]["hand"][0]
    asyncio.run(subject._resolve_selection("a", {"target_id": steal_target, "card_id": stolen.id}))
    assert subject.pending_action["type"] == "discard"


def test_bust_from_nested_just_one_more_keeps_outer_flip_four_actions():
    subject = forced_game(vengeance=True)
    subject.player_state["b"]["hand"] = [Flip7Card("number", "6", 6)]
    subject.player_state["a"]["hand"] = [Flip7Card("number", "10", 10)]
    start_effect(subject, "a", Flip7Card("action", "Flip 4"), "b", [
        Flip7Card("action", "Just One More"), Flip7Card("action", "Discard"),
        Flip7Card("number", "1", 1), Flip7Card("number", "2", 2)])
    assert subject.pending_action["type"] == "just_one_more"
    put_deck_in_draw_order(subject, [Flip7Card("number", "6", 6)])
    asyncio.run(subject._resolve_selection("b", {"target_id": "b"}))
    assert subject.player_state["b"]["busted"] is True
    assert subject.pending_action["type"] == "discard"


def test_swap_can_bust_two_players_and_can_be_between_two_other_players():
    subject = forced_game(vengeance=True)
    subject.player_order = ["a", "b", "c"]
    subject.player_state["c"] = subject._blank_player_state()
    b10, b11 = Flip7Card("number", "10", 10), Flip7Card("number", "11", 11)
    c10, c11 = Flip7Card("number", "10", 10), Flip7Card("number", "11", 11)
    subject.player_state["b"]["hand"] = [b10, b11]
    subject.player_state["c"]["hand"] = [c10, c11]
    result = asyncio.run(subject._resolve_card_movement("swap", "a", "b", {
        "card_id": b10.id, "second_target_id": "c", "second_card_id": c11.id,
    }))
    assert result["bust"] is True
    assert subject.player_state["b"]["busted"] is True
    assert subject.player_state["c"]["busted"] is True


def test_flip_four_stops_on_first_duplicate_keeps_bust_card_and_selects_live_next_player():
    subject = game(vengeance=True)
    subject.player_order = ["a", "b", "c"]
    subject.player_state = {pid: subject._blank_player_state() for pid in subject.player_order}
    subject.state = "player_turn"
    subject.current_player = "a"
    subject.turn_cursor = 0
    subject.player_state["b"]["hand"] = [Flip7Card("number", "8", 8)]
    subject.broadcast = _noop
    subject.broadcast_game_state = _noop
    asyncio.run(subject._request_effect({"actor": "a", "card": Flip7Card("action", "Flip 4")}))
    put_deck_in_draw_order(subject, [Flip7Card("number", "8", 8),
                                     Flip7Card("number", "1", 1),
                                     Flip7Card("number", "2", 2),
                                     Flip7Card("number", "3", 3)])
    asyncio.run(subject._resolve_selection("a", {"target_id": "b"}))
    assert subject.player_state["b"]["busted"] is True
    assert [c.value for c in subject.player_state["b"]["hand"]] == [8, 8]
    assert all(c.face_down for c in subject.player_state["b"]["hand"])
    assert len(subject.deck) == 3
    assert subject.current_player == "c"


def test_swap_is_discarded_when_fewer_than_two_players_have_face_up_cards():
    subject = forced_game(vengeance=True)
    subject.player_state["a"]["hand"] = [Flip7Card("number", "4", 4),
                                          Flip7Card("modifier", "-2", -2)]
    swap = Flip7Card("action", "Swap")
    asyncio.run(subject._request_effect({"actor": "a", "card": swap}))
    assert subject.pending_action is None
    assert swap in subject.discard_pile


def test_round_end_broadcasts_round_ending_before_cards_are_cleared():
    subject = game()
    subject.player_state["a"]["hand"] = [Flip7Card("number", "9", 9)]
    states = []

    async def capture_state():
        states.append((subject.state, len(subject.player_state["a"]["hand"])))

    subject.broadcast_game_state = capture_state
    subject.broadcast = _noop
    subject._continue_initial_deal = _noop
    asyncio.run(subject._end_round())
    assert states[0] == ("round_ending", 1)


def test_brutal_mode_actions_and_modifiers_can_target_inactive_or_busted_players():
    subject = game(vengeance=True, brutal=True)
    subject.player_order = ["a", "b", "c", "d"]
    subject.player_state = {pid: subject._blank_player_state() for pid in subject.player_order}
    subject.player_state["b"]["busted"] = True
    subject.player_state["c"]["stopped"] = True
    subject.player_state["d"]["frozen"] = True
    subject.broadcast = _noop
    asyncio.run(subject._request_effect({"actor": "a", "card": Flip7Card("action", "Flip 4")}))
    assert set(subject.pending_action["targets"]) == {"a", "b", "c", "d"}
    subject.pending_action = None
    asyncio.run(subject._request_effect({"actor": "a", "card": Flip7Card("modifier", "-6", -6)}))
    assert set(subject.pending_action["targets"]) == {"a", "b", "c", "d"}


def test_brutal_card_movement_never_exposes_busted_face_down_cards():
    subject = game(vengeance=True, brutal=True)
    subject.player_order = ["a", "b", "c"]
    subject.player_state = {pid: subject._blank_player_state() for pid in subject.player_order}
    for pid, value in [("a", 3), ("b", 4), ("c", 5)]:
        subject.player_state[pid]["hand"] = [Flip7Card("number", str(value), value)]
    subject.player_state["b"]["busted"] = True
    subject.player_state["b"]["hand"][0].face_down = True
    subject.broadcast = _noop
    asyncio.run(subject._request_effect({"actor": "a", "card": Flip7Card("action", "Swap")}))
    assert set(subject.pending_action["targets"]) == {"a", "c"}


def test_brutal_flip7_can_subtract_bonus_from_selected_player():
    subject = game(vengeance=True, brutal=True)
    subject.broadcast = _noop
    subject.broadcast_game_state = _noop
    subject._continue_initial_deal = _noop
    subject.player_state["a"]["hand"] = [Flip7Card("number", str(n), n) for n in range(1, 8)]
    subject.player_state["a"]["has_flip7"] = True
    subject.player_state["b"]["score"] = 40
    subject.pending_action = {
        "type": "brutal_flip7", "actor": "a", "player_id": "a",
        "card": Flip7Card("action", "Flip 7 reward").public(), "targets": ["a", "b"],
    }
    asyncio.run(subject._resolve_selection("a", {"target_id": "b"}))
    assert subject.player_state["b"]["score"] == 25
    assert subject.player_state["a"]["has_flip7"] is False


def test_brutal_negative_modifier_given_after_bust_stays_face_up_and_scores():
    subject = forced_game(vengeance=True)
    subject.game_rules["brutal_mode"] = True
    busted = subject.player_state["b"]
    old_card = Flip7Card("number", "9", 9, face_down=True)
    busted["hand"] = [old_card]
    busted["busted"] = True
    modifier = Flip7Card("modifier", "-6", -6)
    asyncio.run(subject._request_effect({"actor": "a", "card": modifier}))
    asyncio.run(subject._resolve_selection("a", {"target_id": "b"}))
    received = next(c for c in busted["hand"] if c.card_type == "modifier")
    assert received.face_down is False
    assert old_card.face_down is True
    assert subject._score_hand(busted) == -6


def test_swap_busts_and_flips_stopped_and_frozen_players_lines():
    subject = game(vengeance=True)
    subject.player_order = ["a", "b", "c"]
    subject.player_state = {pid: subject._blank_player_state() for pid in subject.player_order}
    b7, b9 = Flip7Card("number", "7", 7), Flip7Card("number", "9", 9)
    c7, c9 = Flip7Card("number", "7", 7), Flip7Card("number", "9", 9)
    subject.player_state["b"]["hand"] = [b7, b9]
    subject.player_state["b"]["stopped"] = True
    subject.player_state["c"]["hand"] = [c7, c9]
    subject.player_state["c"]["frozen"] = True
    result = asyncio.run(subject._resolve_card_movement("swap", "a", "b", {
        "card_id": b9.id, "second_target_id": "c", "second_card_id": c7.id,
    }))
    assert result["bust"] is True
    assert subject.player_state["b"]["busted"] is True
    assert subject.player_state["c"]["busted"] is True
    assert all(card.face_down for card in subject.player_state["b"]["hand"])
    assert all(card.face_down for card in subject.player_state["c"]["hand"])
    assert subject._score_hand(subject.player_state["b"]) == 0
    assert subject._score_hand(subject.player_state["c"]) == 0


def test_base_times_two_precedes_flat_additions_regardless_of_draw_order():
    subject = game()
    state = subject.player_state["a"]
    state["hand"] = [
        Flip7Card("modifier", "+10", 10),
        Flip7Card("number", "5", 5),
        Flip7Card("modifier", "×2", multiplier=2),
        Flip7Card("number", "4", 4),
    ]
    assert subject._score_hand(state) == 28


def test_vengeance_divide_two_rounds_down_before_negative_modifiers():
    subject = game(vengeance=True, brutal=True)
    state = subject.player_state["a"]
    state["hand"] = [
        Flip7Card("modifier", "-10", -10),
        Flip7Card("number", "5", 5),
        Flip7Card("modifier", "÷2", multiplier=0.5),
        Flip7Card("number", "4", 4),
    ]
    assert subject._score_hand(state) == -6


def test_custom_deck_keeps_zero_to_n_distribution_and_mixes_all_card_families():
    spec = DeckSpec.from_dict({
        "name": "mixed", "number_max": 5,
        "actions": {"flip_3": 2, "flip_4": 1, "swap": 3},
        "modifiers": {"times_2": 1, "divide_2": 1, "minus_2": 2, "plus_10": 4},
    })
    cards = spec.build()
    numbers = [card for card in cards if card.card_type == "number"]
    assert len(numbers) == 16
    assert {n: len([card for card in numbers if card.value == n]) for n in range(6)} == {
        0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
    }
    assert len(cards) == 30


def test_custom_special_numbers_require_their_numeric_face():
    try:
        DeckSpec.from_dict({"number_max": 12, "special_numbers": {"lucky_13": True}})
    except DeckSpecError:
        pass
    else:
        raise AssertionError("Lucky 13 must require number_max >= 13")


def test_probability_is_only_next_card_and_ignores_second_chance():
    hand = [Flip7Card("number", "7", 7), Flip7Card("action", "Second Chance")]
    pile = [Flip7Card("number", "7", 7), Flip7Card("number", "8", 8),
            Flip7Card("action", "Flip 4")]
    result = next_draw_bust_probability(hand, pile)
    assert result == {"probability": 1 / 3, "bust_cards": 1, "remaining_cards": 3}


def test_probability_handles_lucky13_and_unlucky7_faces():
    hand = [Flip7Card("number", "13", 13), Flip7Card("number", "7", 7)]
    pile = [Flip7Card("number", "Lucky 13", 13, ability="lucky_13"),
            Flip7Card("number", "13", 13),
            Flip7Card("number", "Unlucky 7", 7, ability="unlucky_7")]
    result = next_draw_bust_probability(hand, pile)
    assert result["bust_cards"] == 1
    assert result["probability"] == 1 / 3


def test_seeded_custom_deck_order_is_reproducible():
    rules = {"deck_preset": "custom", "random_seed": 20260721,
             "deck_spec": {"number_max": 4, "actions": {"flip_3": 2},
                           "modifiers": {"times_2": 1}}}
    first, second = game(), game()
    for subject in (first, second):
        subject.game_rules.update(rules)
        subject.rng.seed(rules["random_seed"])
        subject._init_deck()
    signature = lambda deck: [(card.card_type, card.name, card.value, card.ability) for card in deck]
    assert signature(first.deck) == signature(second.deck)


def test_custom_scoring_applies_numeric_multipliers_before_all_flat_modifiers():
    subject = game()
    subject.game_rules.update({"deck_preset": "custom", "brutal_mode": True})
    subject.player_state["a"]["hand"] = [
        Flip7Card("number", "5", 5), Flip7Card("number", "4", 4),
        Flip7Card("modifier", "×2", multiplier=2),
        Flip7Card("modifier", "÷2", multiplier=.5),
        Flip7Card("modifier", "+10", 10), Flip7Card("modifier", "-2", -2),
    ]
    assert subject._score_hand(subject.player_state["a"]) == 17
