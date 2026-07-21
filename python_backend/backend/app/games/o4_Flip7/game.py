"""Server-authoritative Flip 7 rules engine.

The room owns connections/readiness.  This module owns only the card game and
keeps the existing websocket message contract used by the Vue client.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

from app.games.roundBase import RoundBaseGame
from app.models.player import Player
from .domain.cards import Flip7Card
from .domain.deck_spec import (DeckSpec, DeckSpecError, official_base_spec,
                               official_vengeance_spec)
from .domain.probability import next_draw_bust_probability
from .domain.scoring import score_hand


class o4Flip7Game(RoundBaseGame):
    BASE_ACTIONS = ("Flip 3", "Freeze", "Second Chance")
    VENGEANCE_ACTIONS = ("Just One More", "Swap", "Steal", "Discard", "Flip 4")

    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.config = {"max_players": 18, "min_players": 2}
        self.game_rules: Dict[str, Any] = {
            "deck_preset": "base",
            "deck_spec": official_base_spec().public(),
            "vengeance_mode": False,
            "brutal_mode": False,
            "win_score": 200,
            "flip7_bonus": 15,
            "probability_enabled": False,
            "probability_visibility": "all",
            "random_seed": None,
        }
        self.deck_spec = official_base_spec()
        self.rng = random.Random()
        self.deck: List[Flip7Card] = []
        self.discard_pile: List[Flip7Card] = []
        self.player_state: Dict[str, Dict[str, Any]] = {}
        self.persistent_players: Dict[str, Player] = {}
        self.pending_action: Optional[Dict[str, Any]] = None
        self.forced_draw: Optional[Dict[str, Any]] = None
        # Each Flip 3 / Flip 4 / Just One More owns its own deferred effects.
        # Keeping frames separate is essential for depth-first nested resolution.
        self.forced_stack: List[Dict[str, Any]] = []
        self.turn_cursor = 0
        self.dealer_index = 0
        self.last_round_scores: Dict[str, int] = {}
        self.initial_deal_queue: List[str] = []
        self.dealing_initial = False
        self.round_end_delay = 3.0
        self.round_ending = False

    async def connect(self, websocket: WebSocket, player: Player):
        reconnecting = player.id in self.persistent_players
        self.connections[websocket] = player.id
        self.persistent_players[player.id] = player
        await self.broadcast({
            "type": "player_reconnected" if reconnecting else "player_joined",
            "player": {"id": player.id, "name": player.name, "avatar": player.avatar},
        })
        if self.player_order:
            await self.broadcast_game_state()

    async def disconnect(self, websocket: WebSocket):
        player_id = self.connections.pop(websocket, None)
        if player_id:
            await self.broadcast({"type": "player_disconnected", "player_id": player_id})

    def _init_player_order(self) -> List[str]:
        return list(self.persistent_players)

    def _new_number(self, value: int, ability: str = "") -> Flip7Card:
        name = str(value)
        if ability == "unlucky_7":
            name = "Unlucky 7"
        elif ability == "lucky_13":
            name = "Lucky 13"
        return Flip7Card("number", name, value=value, ability=ability)

    def _resolve_deck_spec(self) -> DeckSpec:
        preset = self.game_rules.get("deck_preset", "base")
        if preset == "vengeance":
            return official_vengeance_spec()
        if preset == "custom":
            return DeckSpec.from_dict(self.game_rules.get("deck_spec"), preset="custom")
        return official_base_spec()

    def _init_deck(self) -> None:
        self.deck_spec = self._resolve_deck_spec()
        self.deck = self.deck_spec.build()
        self.discard_pile = []
        self.rng.shuffle(self.deck)
        self.game_rules["deck_spec"] = self.deck_spec.public()

    def _init_deck_legacy(self) -> None:
        self.deck = []
        self.discard_pile = []
        vengeance = self.game_rules["vengeance_mode"]

        # Both editions use one zero and N copies of number N for 1..12.
        self.deck.append(self._new_number(0, "zero" if vengeance else ""))
        for value in range(1, 13):
            for copy_index in range(value):
                ability = "unlucky_7" if vengeance and value == 7 and copy_index == 0 else ""
                self.deck.append(self._new_number(value, ability))

        if vengeance:
            # There are thirteen 13 cards total; exactly one is Lucky 13.
            for copy_index in range(13):
                self.deck.append(self._new_number(13, "lucky_13" if copy_index == 0 else ""))
            for name in self.VENGEANCE_ACTIONS:
                for _ in range(2):
                    self.deck.append(Flip7Card("action", name))
            self.deck.append(Flip7Card("modifier", "÷2", multiplier=0.5))
            for value in (-2, -4, -6, -8, -10):
                self.deck.append(Flip7Card("modifier", str(value), value=value))
        else:
            for name in self.BASE_ACTIONS:
                for _ in range(3):
                    self.deck.append(Flip7Card("action", name))
            for value in (2, 4, 6, 8, 10):
                self.deck.append(Flip7Card("modifier", f"+{value}", value=value))
            self.deck.append(Flip7Card("modifier", "×2", multiplier=2))
        random.shuffle(self.deck)

    def _blank_player_state(self, total_score: int = 0) -> Dict[str, Any]:
        return {
            "score": total_score,
            "hand": [],
            "busted": False,
            "stopped": False,
            "frozen": False,
            "has_flip7": False,
            "second_chance": False,
            "must_hit": False,
        }

    def _reset_round(self) -> None:
        for pid in self.player_order:
            total = self.player_state.get(pid, {}).get("score", 0)
            self.player_state[pid] = self._blank_player_state(total)
        self.pending_action = None
        self.forced_draw = None
        self.forced_stack = []
        self.turn_cursor = (self.dealer_index + 1) % len(self.player_order)
        self.current_player = self.player_order[self.turn_cursor]

    async def start_game(self, mode="multi", total_rounds=1):
        self.mode = mode
        self.player_order = self._init_player_order()
        self.rng = random.Random(self.game_rules.get("random_seed"))
        self._init_deck()
        self.player_state = {pid: self._blank_player_state() for pid in self.player_order}
        self.round = 1
        self.state = "player_turn"
        self.dealer_index = 0
        self._reset_round()
        self._prepare_initial_deal()
        await self._continue_initial_deal()

    def _prepare_initial_deal(self) -> None:
        self.initial_deal_queue = [
            self.player_order[(self.dealer_index + 1 + offset) % len(self.player_order)]
            for offset in range(len(self.player_order))
        ]
        self.dealing_initial = True

    async def handle_event(self, websocket, event, player_id):
        if not event:
            return await self._error(player_id, "无效事件")
        if event.get("type") == "update_rules":
            await self.update_rules(event)
        elif event.get("type") == "action":
            await self.handle_player_action(player_id, event.get("action"), event.get("data") or {})

    async def update_rules(self, settings):
        rules = settings.get("rules", settings)
        if self.state == "player_turn" and self.player_order:
            return
        preset = rules.get("deck_preset")
        if preset not in {"base", "vengeance", "custom"}:
            preset = "vengeance" if rules.get("vengeance_mode") else "base"
        try:
            if preset == "base":
                deck_spec = official_base_spec()
            elif preset == "vengeance":
                deck_spec = official_vengeance_spec()
            else:
                deck_spec = DeckSpec.from_dict(rules.get("deck_spec"), preset="custom")
        except (DeckSpecError, TypeError, ValueError) as exc:
            return await self.broadcast({"type": "rules_error", "message": str(exc)})
        visibility = rules.get("probability_visibility", "all")
        if visibility not in {"self", "current", "all"}:
            visibility = "all"
        seed = rules.get("random_seed")
        if seed in ("", None):
            seed = None
        else:
            try:
                seed = int(seed)
            except (TypeError, ValueError):
                return await self.broadcast({"type": "rules_error", "message": "随机种子必须是整数"})
        self.game_rules.update({
            "deck_preset": preset,
            "deck_spec": deck_spec.public(),
            "vengeance_mode": preset == "vengeance",
            "brutal_mode": preset in {"vengeance", "custom"} and bool(rules.get("brutal_mode", False)),
            "win_score": max(1, int(rules.get("win_score", self.game_rules["win_score"]))),
            "flip7_bonus": max(0, int(rules.get("flip7_bonus", self.game_rules["flip7_bonus"]))),
            "probability_enabled": bool(rules.get("probability_enabled", False)),
            "probability_visibility": visibility,
            "random_seed": seed,
        })
        self.deck_spec = deck_spec
        await self.broadcast({"type": "rules_updated", "rules": self.game_rules})

    async def handle_player_action(self, player_id: str, action: str, data: Dict[str, Any]):
        if self.state != "player_turn":
            return await self._error(player_id, "游戏当前不可操作")
        if self.pending_action:
            if self.pending_action["actor"] != player_id or action != "select_target":
                return await self._error(player_id, "请先完成卡牌效果")
            return await self._resolve_selection(player_id, data)
        if player_id != self.current_player:
            return await self._error(player_id, "还没有轮到你")
        if action == "draw":
            await self._draw_for(player_id)
        elif action == "stop":
            state = self.player_state[player_id]
            if self.forced_draw or state["must_hit"]:
                return await self._error(player_id, "当前必须继续翻牌")
            state["stopped"] = True
            await self.broadcast({"type": "player_stopped", "player_id": player_id,
                                  "round_score": self._score_hand(state)})
            await self._advance_turn()
        else:
            await self._error(player_id, "未知操作")

    def _draw_card(self) -> Optional[Flip7Card]:
        if not self.deck:
            if not self.discard_pile:
                return None
            self.deck, self.discard_pile = self.discard_pile, []
            self.rng.shuffle(self.deck)
        return self.deck.pop()

    async def _draw_for(self, player_id: str) -> None:
        card = self._draw_card()
        if not card:
            return await self._error(player_id, "牌库已经耗尽")
        forced = bool(self.forced_stack)
        result = await self._accept_card(player_id, card, defer_action=forced)
        await self.broadcast({"type": "card_drawn", "player_id": player_id,
                              "card": card.public(), "is_flip3": forced, **result})

        if result.get("flip7"):
            return await self._end_round()
        if result.get("bust"):
            if forced:
                frame = self.forced_stack[-1]
                frame["remaining"] = 0
                frame["remaining_flips"] = 0
                frame["effects"] = []
                return await self._continue_effect_resolution()
            return await self._resume_after_effect()
        if self.pending_action:
            return await self.broadcast_game_state()
        if forced:
            frame = self.forced_stack[-1]
            frame["remaining"] -= 1
            frame["remaining_flips"] = frame["remaining"]
            self._sync_forced_draw()
            if frame["remaining"] <= 0:
                return await self._continue_effect_resolution()
            return await self.broadcast_game_state()
        # A normal hit consumes this visit in the table rotation. The player
        # may choose Hit/Stay again only after every other active player has
        # had their visit. Forced draws are handled above and remain together.
        await self._advance_turn()

    async def _accept_card(self, pid: str, card: Flip7Card, defer_action=False) -> Dict[str, Any]:
        state = self.player_state[pid]
        result = {"bust": False, "used_sc": False, "flip7": False}
        if card.card_type == "number":
            if card.ability == "unlucky_7":
                self._discard_hand(state)
                state["hand"].append(card)
            else:
                same = [c for c in state["hand"] if c.card_type == "number" and c.value == card.value]
                has_lucky_13 = card.ability == "lucky_13" or any(
                    c.ability == "lucky_13" for c in same
                )
                duplicate_limit = 2 if card.value == 13 and has_lucky_13 else 1
                if len(same) >= duplicate_limit:
                    if state["second_chance"]:
                        state["second_chance"] = False
                        self.discard_pile.append(card)
                        result["used_sc"] = True
                        return result
                    # Keep the duplicate in the busted line so every client can
                    # show exactly which card caused the bust. The whole line is
                    # turned face-down until round cleanup.
                    state["hand"].append(card)
                    for held_card in state["hand"]:
                        held_card.face_down = True
                    state["busted"] = True
                    return {**result, "bust": True}
                state["hand"].append(card)
                if card.ability == "zero":
                    state["must_hit"] = True
            if len({c.value for c in state["hand"] if c.card_type == "number"}) >= 7:
                state["has_flip7"] = True
                if self.game_rules["brutal_mode"]:
                    self.pending_action = {
                        "type": "brutal_flip7", "actor": pid, "player_id": pid,
                        "card": Flip7Card("action", "Flip 7 reward").public(),
                        "targets": list(self.player_order),
                    }
                    await self.broadcast({"type": "pending_action", "action": self.pending_action})
                else:
                    result["flip7"] = True
        elif card.card_type == "modifier":
            if self.game_rules.get("deck_preset") != "base":
                await self._queue_or_request_effect(pid, card, defer_action)
            else:
                state["hand"].append(card)
        elif card.card_type == "action":
            # Second Chance is the exception inside Flip 3: the first copy is
            # acquired immediately and can protect against a later card in the
            # same forced sequence. Extra copies still require reassignment.
            if card.name == "Second Chance" and not state["second_chance"]:
                state["second_chance"] = True
                state["hand"].append(card)
            else:
                await self._queue_or_request_effect(pid, card, defer_action)
        return result

    async def _queue_or_request_effect(self, actor: str, card: Flip7Card, deferred: bool) -> None:
        effect = {"actor": actor, "card": card}
        if deferred:
            self.forced_stack[-1]["effects"].append(effect)
        else:
            await self._request_effect(effect)

    def _eligible_targets(self, card: Flip7Card) -> List[str]:
        vengeance = self.game_rules.get("deck_preset") != "base"
        brutal = self.game_rules["brutal_mode"]
        result = []
        for pid in self.player_order:
            state = self.player_state[pid]
            if brutal:
                # Project rule: in Brutal Mode both Action and Modifier cards
                # may name stayed, frozen, or busted players.
                result.append(pid)
            elif card.card_type == "modifier":
                if not state["busted"]:
                    result.append(pid)
            elif vengeance:
                if not state["busted"]:
                    result.append(pid)
            elif not state["busted"] and not state["stopped"] and not state["frozen"]:
                result.append(pid)
        return result

    async def _request_effect(self, effect: Dict[str, Any]) -> None:
        actor, card = effect["actor"], effect["card"]
        if card.name == "Second Chance":
            targets = [p for p in self._eligible_targets(card)
                       if not self.player_state[p]["second_chance"]]
        else:
            targets = self._eligible_targets(card)
        if card.name in ("Steal",):
            targets = [p for p in targets if p != actor and self._has_face_up_cards(p)]
        if card.name in ("Swap",):
            targets = [p for p in targets if self._has_face_up_cards(p)]
            if len(targets) < 2:
                targets = []
        if card.name == "Discard":
            targets = [p for p in targets if self._has_face_up_cards(p)]
        if not targets:
            self.discard_pile.append(card)
            return
        self.pending_action = {
            "type": self._effect_type(card), "actor": actor, "player_id": actor,
            "card": card.public(), "targets": targets,
        }
        await self.broadcast({"type": "pending_action", "action": self.pending_action})

    def _has_face_up_cards(self, pid: str) -> bool:
        state = self.player_state[pid]
        return any(not card.face_down for card in state["hand"])

    @staticmethod
    def _effect_type(card: Flip7Card) -> str:
        return {
            "Freeze": "freeze", "Flip 3": "flip3", "Second Chance": "transfer_sc",
            "Just One More": "just_one_more", "Swap": "swap", "Steal": "steal",
            "Discard": "discard", "Flip 4": "flip4",
        }.get(card.name, "modifier")

    async def _resolve_selection(self, actor: str, data: Dict[str, Any]) -> None:
        action = self.pending_action
        target = data.get("target_id")
        if target not in action["targets"]:
            return await self._error(actor, "无效目标")
        card = Flip7Card(action["card"]["type"], action["card"]["name"],
                         action["card"]["value"], action["card"]["multiplier"],
                         action["card"].get("ability", ""), action["card"]["id"])
        kind = action["type"]
        if kind in ("steal", "discard", "swap"):
            if not any(c.id == data.get("card_id") and not c.face_down
                       for c in self.player_state[target]["hand"]):
                return await self._error(actor, "请选择一张有效卡牌")
        if kind == "swap":
            other_pid = data.get("second_target_id") or actor
            allowed = set(action["targets"])
            if other_pid == target or other_pid not in allowed:
                return await self._error(actor, "请选择另一名有效玩家")
            other_id = data.get("second_card_id") or data.get("own_card_id")
            if not any(c.id == other_id and not c.face_down
                       for c in self.player_state[other_pid]["hand"]):
                return await self._error(actor, "请选择另一张有效卡牌")
        self.pending_action = None

        if kind == "freeze":
            self.player_state[target]["frozen"] = True
            self.player_state[target]["stopped"] = True
            await self.broadcast({"type": "player_frozen", "target_id": target, "by_player": actor})
        elif kind in ("flip3", "flip4", "just_one_more"):
            count = {"flip3": 3, "flip4": 4, "just_one_more": 1}[kind]
            frame = {"active": True, "kind": kind, "target": target, "target_player": target,
                     "source": actor, "source_player": actor, "remaining": count,
                     "remaining_flips": count, "stay_after": kind == "just_one_more",
                     "was_inactive": self.player_state[target]["stopped"], "effects": []}
            self.forced_stack.append(frame)
            self._sync_forced_draw()
            self.current_player = target
            await self.broadcast({"type": "flip3_start", "target_player": target,
                                  "source_player": actor, "count": count})
        elif kind == "transfer_sc":
            self.player_state[target]["second_chance"] = True
            self.player_state[target]["hand"].append(card)
        elif kind == "modifier":
            self.player_state[target]["hand"].append(card)
        elif kind in ("steal", "discard", "swap"):
            movement = await self._resolve_card_movement(kind, actor, target, data)
            if movement.get("flip7"):
                return await self._end_round()
        elif kind == "brutal_flip7":
            if target != actor:
                self.player_state[actor]["has_flip7"] = False
                self.player_state[target]["score"] -= self.game_rules["flip7_bonus"]
            return await self._end_round()
        if kind not in ("transfer_sc", "modifier"):
            self.discard_pile.append(card)

        await self._continue_effect_resolution()

    async def _resolve_card_movement(self, kind: str, actor: str, target: str,
                                     data: Dict[str, Any]) -> Dict[str, bool]:
        target_hand = self.player_state[target]["hand"]
        selected = next((c for c in target_hand
                         if c.id == data.get("card_id") and not c.face_down), None)
        if not selected:
            return {"bust": False, "flip7": False}
        target_hand.remove(selected)
        affected = {target}
        if kind == "discard":
            self.discard_pile.append(selected)
        elif kind == "steal":
            self.player_state[actor]["hand"].append(selected)
            affected.add(actor)
        else:
            other_pid = data.get("second_target_id") or actor
            if other_pid not in self.player_state or other_pid == target:
                target_hand.append(selected)
                return {"bust": False, "flip7": False}
            other_hand = self.player_state[other_pid]["hand"]
            other_id = data.get("second_card_id") or data.get("own_card_id")
            other = next((c for c in other_hand if c.id == other_id and not c.face_down), None)
            if not other:
                target_hand.append(selected)
                return {"bust": False, "flip7": False}
            other_hand.remove(other)
            target_hand.append(other)
            other_hand.append(selected)
            affected.add(other_pid)
        results = [self._reconcile_hand(pid) for pid in affected]
        return {"bust": any(r["bust"] for r in results),
                "flip7": any(r["flip7"] for r in results)}

    def _reconcile_hand(self, pid: str) -> Dict[str, bool]:
        """Re-apply special-number rules after cards are stolen/swapped/discarded."""
        state = self.player_state[pid]
        was_busted = state["busted"]
        unlucky = next((c for c in state["hand"] if c.ability == "unlucky_7"), None)
        if unlucky:
            removed = [c for c in state["hand"]
                       if c is not unlucky and c.card_type in ("number", "modifier")]
            for card in removed:
                state["hand"].remove(card)
            self.discard_pile.extend(removed)
        self._refresh_special_flags(pid)
        numbers = [c for c in state["hand"] if c.card_type == "number"]
        counts: Dict[int, int] = {}
        for card in numbers:
            counts[card.value] = counts.get(card.value, 0) + 1
        has_lucky = any(c.ability == "lucky_13" for c in numbers)
        state["busted"] = any(
            count > (2 if value == 13 and has_lucky else 1)
            for value, count in counts.items()
        )
        if state["busted"] and not was_busted:
            for card in state["hand"]:
                card.face_down = True
        state["has_flip7"] = len(counts) >= 7 and not state["busted"]
        return {"bust": state["busted"], "flip7": state["has_flip7"]}

    def _sync_forced_draw(self) -> None:
        self.forced_draw = self.forced_stack[-1] if self.forced_stack else None

    async def _continue_effect_resolution(self) -> None:
        """Resolve forced-draw frames depth-first and preserve parent effects."""
        while self.forced_stack and not self.pending_action:
            frame = self.forced_stack[-1]
            if frame["remaining"] > 0:
                self.current_player = frame["target"]
                self._sync_forced_draw()
                return await self._run_forced_draws()
            if frame["effects"]:
                effect = frame["effects"].pop(0)
                await self._request_effect(effect)
                if self.pending_action:
                    self._sync_forced_draw()
                    return await self.broadcast_game_state()
                continue
            completed = self.forced_stack.pop()
            if completed["stay_after"]:
                self.player_state[completed["target"]]["stopped"] = True
            # A stayed target forced by Flip Four remains stayed after all nested actions.
            if completed["was_inactive"]:
                self.player_state[completed["target"]]["stopped"] = True
            self._sync_forced_draw()
        if self.pending_action:
            return await self.broadcast_game_state()
        await self._resume_after_effect()

    async def _run_forced_draws(self) -> None:
        """Automatically exhaust the top forced-draw frame.

        The loop pauses only when a revealed effect requires a human target
        choice. Resolving that choice calls back into the same stack and
        automatically continues nested and parent frames.
        """
        while self.forced_stack and not self.pending_action:
            frame = self.forced_stack[-1]
            if frame["remaining"] <= 0:
                return await self._continue_effect_resolution()
            player_id = frame["target"]
            self.current_player = player_id
            card = self._draw_card()
            if not card:
                return await self._error(player_id, "牌库已经耗尽")
            result = await self._accept_card(player_id, card, defer_action=True)
            await self.broadcast({"type": "card_drawn", "player_id": player_id,
                                  "card": card.public(), "is_flip3": True, **result})
            if result.get("flip7"):
                return await self._end_round()
            if result.get("bust"):
                frame["remaining"] = 0
                frame["remaining_flips"] = 0
                frame["effects"] = []
                self._sync_forced_draw()
                return await self._continue_effect_resolution()
            if self.pending_action:
                return await self.broadcast_game_state()
            frame["remaining"] -= 1
            frame["remaining_flips"] = frame["remaining"]
            self._sync_forced_draw()
        if self.pending_action:
            await self.broadcast_game_state()

    async def _continue_initial_deal(self) -> None:
        while self.initial_deal_queue and not self.pending_action and not self.forced_draw:
            pid = self.initial_deal_queue.pop(0)
            card = self._draw_card()
            if not card:
                break
            result = await self._accept_card(pid, card)
            await self.broadcast({"type": "card_drawn", "player_id": pid,
                                  "card": card.public(), "is_flip3": False, **result})
            if result.get("flip7"):
                return await self._end_round()
        if not self.initial_deal_queue and not self.pending_action and not self.forced_draw:
            self.dealing_initial = False
            self._select_initial_active_player()
        await self.broadcast_game_state()

    def _select_initial_active_player(self) -> None:
        """Restore turn ownership after setup effects changed current_player."""
        for offset in range(len(self.player_order)):
            idx = (self.turn_cursor + offset) % len(self.player_order)
            pid = self.player_order[idx]
            state = self.player_state[pid]
            if not state["busted"] and not state["stopped"] and not state["frozen"]:
                self.turn_cursor = idx
                self.current_player = pid
                return

    async def _resume_after_effect(self) -> None:
        if self.dealing_initial:
            await self._continue_initial_deal()
        else:
            await self._advance_turn()

    def _refresh_special_flags(self, pid: str) -> None:
        state = self.player_state[pid]
        state["must_hit"] = any(c.ability == "zero" for c in state["hand"])
        state["second_chance"] = any(c.name == "Second Chance" for c in state["hand"])

    def _discard_hand(self, state: Dict[str, Any]) -> None:
        self.discard_pile.extend(state["hand"])
        state["hand"] = []
        state["second_chance"] = False
        state["must_hit"] = False

    def _score_hand(self, state: Dict[str, Any]) -> int:
        return score_hand(
            state["hand"], busted=state["busted"], brutal=self.game_rules["brutal_mode"],
            preset=self.game_rules.get("deck_preset", "base"),
            has_flip7=state["has_flip7"], flip7_bonus=self.game_rules["flip7_bonus"],
        )

    async def _advance_turn(self) -> None:
        if self.pending_action or self.forced_draw:
            return await self.broadcast_game_state()
        if all(s["busted"] or s["stopped"] or s["frozen"] for s in self.player_state.values()):
            return await self._end_round()
        for _ in range(len(self.player_order)):
            self.turn_cursor = (self.turn_cursor + 1) % len(self.player_order)
            pid = self.player_order[self.turn_cursor]
            state = self.player_state[pid]
            if not state["busted"] and not state["stopped"] and not state["frozen"]:
                self.current_player = pid
                return await self.broadcast_game_state()
        await self._end_round()

    async def _end_round(self) -> None:
        if self.round_ending:
            return
        self.round_ending = True
        self.state = "round_ending"
        await self.broadcast_game_state()
        if self.round_end_delay > 0:
            await asyncio.sleep(self.round_end_delay)
        self.last_round_scores = {pid: self._score_hand(state)
                                  for pid, state in self.player_state.items()}
        for pid, points in self.last_round_scores.items():
            self.player_state[pid]["score"] += points
            self._discard_hand(self.player_state[pid])
        leaders = sorted(self.player_order, key=lambda p: self.player_state[p]["score"], reverse=True)
        if leaders and self.player_state[leaders[0]]["score"] >= self.game_rules["win_score"]:
            self.state = "finished"
            self.round_ending = False
            top = self.player_state[leaders[0]]["score"]
            winners = [p for p in leaders if self.player_state[p]["score"] == top]
            await self.broadcast({"type": "game_finished", "winner": winners[0],
                                  "winners": winners,
                                  "player_scores": {p: self.player_state[p]["score"] for p in self.player_order}})
            return await self.broadcast_game_state()
        self.round += 1
        self.round_ending = False
        self.state = "player_turn"
        self.dealer_index = (self.dealer_index + 1) % len(self.player_order)
        self._reset_round()
        self._prepare_initial_deal()
        await self._continue_initial_deal()

    def _public_player_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        numbers = {c.value for c in state["hand"] if c.card_type == "number"}
        return {
            "score": state["score"], "round_score": self._score_hand(state),
            "flip7_count": len(numbers), "second_chances": int(state["second_chance"]),
            "frozen": state["frozen"], "stopped": state["stopped"],
            "busted": state["busted"], "face_down": state["busted"],
            "active": not (state["busted"] or state["stopped"]),
            "has_flip7": state["has_flip7"], "must_hit": state["must_hit"],
            "round_numbers": sorted(numbers), "hand": [c.public() for c in state["hand"]],
        }

    def _probability_for(self, player_id: str) -> Dict[str, Any]:
        # This deliberately answers only “what if this player draws one card now”.
        # It does not simulate Flip X and does not consume Second Chance.
        source = self.deck if self.deck else self.discard_pile
        return next_draw_bust_probability(self.player_state[player_id]["hand"], source)

    async def broadcast_game_state(self):
        if not self.player_order:
            return
        probabilities: Dict[str, Any] = {}
        visibility = self.game_rules.get("probability_visibility", "all")
        if self.game_rules.get("probability_enabled") and visibility == "all":
            probabilities = {pid: self._probability_for(pid) for pid in self.player_order}
        elif self.game_rules.get("probability_enabled") and visibility == "current" and self.current_player:
            probabilities = {self.current_player: self._probability_for(self.current_player)}
        payload = {
            "type": "game_state", "state": self.state, "current_player": self.current_player,
            "round": self.round, "total_rounds": self.total_rounds,
            "dealer": self.player_order[self.dealer_index],
            "player_states": {p: self._public_player_state(s) for p, s in self.player_state.items()},
            "pending_action": self.pending_action, "flip3_state": self.forced_draw or {"active": False},
            "remaining_cards": len(self.deck), "discard_count": len(self.discard_pile),
            "last_round_scores": self.last_round_scores, "rules": self.game_rules,
            "deck_spec": self.deck_spec.public(), "deck_summary": self.deck_spec.summary(),
            "probabilities": probabilities,
            "players": {pid: {"id": p.id, "name": p.name, "avatar": p.avatar,
                                "connected": pid in self.connections.values()}
                        for pid, p in self.persistent_players.items()},
        }
        await self.broadcast(payload)
        if self.game_rules.get("probability_enabled") and visibility == "self":
            for pid in self.player_order:
                await self.broadcast_to_player(pid, {
                    "type": "probability_state",
                    "probabilities": {pid: self._probability_for(pid)},
                })

    async def _error(self, player_id: str, message: str):
        await self.broadcast_to_player(player_id, {"type": "error", "message": message, "msg": message})

    def is_game_finished(self) -> bool:
        return self.state == "finished"
