from __future__ import annotations

import asyncio
import json
import random
import uuid
from typing import Any, Dict

from fastapi import WebSocket

from app.database import SessionLocal
from app.games.base import BaseGame
from app.game_record_service import GameRecordService
from app.models.player import Player
from app.models.question_bank import QuestionBank, QuestionBankMember, QuestionBankVersion

from .domain import (AnswerSubmission, RankedCorrectScoringStrategy, SystemClock,
                     TimeSyncRecord, ValidatedSynchronizedTimestampPolicy,
                     question_from_snapshot)


class NewQuizGame(BaseGame):
    """Server-authoritative, question-bank driven synchronous quiz prototype."""

    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.config = {"min_players": 1, "max_players": 12}
        self.game_rules = {"bank_id": None, "question_count": 10, "time_limit_seconds": 20,
                           "result_seconds": 4, "random_order": False,
                           "rank_scores": [10, 8, 7], "fallback_correct_score": 5}
        self.persistent_players: Dict[str, Player] = {}
        self.clock = SystemClock()
        self.timestamp_policy = ValidatedSynchronizedTimestampPolicy()
        self.sync_records: dict[str, TimeSyncRecord] = {}
        self.questions = []
        self.current_question_index = -1
        self.current_question = None
        self.question_opened_at_ms = 0
        self.question_closes_at_ms = 0
        self.submissions: dict[str, AnswerSubmission] = {}
        self.attempt_counts: dict[str, int] = {}
        self.submission_sequence = 0
        self.scores: dict[str, int] = {}
        self.correct_counts: dict[str, int] = {}
        self.round_results: list[dict] = []
        self.phase = "waiting"
        self.timer_task: asyncio.Task | None = None
        self.round_lock = asyncio.Lock()
        self.bank_title = ""
        self.started_at_ms = 0

    async def connect(self, websocket: WebSocket, player: Player) -> None:
        self.connections[websocket] = player.id
        self.persistent_players[player.id] = player
        self.disconnected_players.discard(player.id)
        if self.state != "waiting":
            await self.broadcast_game_state()

    async def update_rules(self, rules: Dict[str, Any]) -> None:
        requested = rules.get("rules", rules)
        if self.state != "waiting": return
        if "bank_id" in requested:
            self.game_rules["bank_id"] = int(requested["bank_id"]) if requested["bank_id"] else None
        for key, low, high in (("question_count", 1, 100), ("time_limit_seconds", 5, 300),
                               ("result_seconds", 1, 15), ("fallback_correct_score", 0, 10000)):
            if key in requested:
                self.game_rules[key] = max(low, min(high, int(requested[key])))
        if "random_order" in requested:
            self.game_rules["random_order"] = bool(requested["random_order"])
        if "rank_scores" in requested:
            values = [max(0, min(10000, int(value))) for value in requested["rank_scores"]][:12]
            if values: self.game_rules["rank_scores"] = values

    async def handle_event(self, websocket, event, player_id):
        event_type = event.get("type")
        if event_type == "time_sync_request":
            await self._sync_time(websocket, player_id, event)
        elif event_type == "action" and event.get("action") == "submit_answer":
            await self._submit_answer(player_id, event)

    async def start_game(self, mode="multi") -> None:
        try:
            snapshot = self._load_snapshot()
            self.questions = [question_from_snapshot(item) for item in snapshot["questions"]]
        except (ValueError, RuntimeError) as exc:
            self.room.status = "waiting"
            await self.room.broadcast_state(extra_message={"error": str(exc)})
            return
        if self.game_rules["random_order"]:
            random.SystemRandom().shuffle(self.questions)
        self.questions = self.questions[:self.game_rules["question_count"]]
        ids = list(self.room.players)
        self.scores = {pid: 0 for pid in ids}
        self.correct_counts = {pid: 0 for pid in ids}
        self.round_results = []
        self.current_question_index = -1
        self.state = "playing"
        self.started_at_ms = self.clock.epoch_ms()
        self.phase = "preparing"
        await self._open_next_question()

    def _load_snapshot(self) -> dict:
        bank_id = self.game_rules.get("bank_id")
        if not bank_id: raise ValueError("请先选择已发布的题库")
        db = SessionLocal()
        try:
            bank = db.query(QuestionBank).filter_by(id=bank_id, status="published").first()
            if not bank: raise ValueError("所选题库不存在或尚未发布")
            owner_id = int(self.room.owner["id"])
            member = db.query(QuestionBankMember).filter_by(bank_id=bank.id, user_id=owner_id).first()
            if bank.owner_id != owner_id and bank.visibility not in {"public", "unlisted"} and not member:
                raise ValueError("房主没有使用该题库的权限")
            version = db.query(QuestionBankVersion).filter_by(bank_id=bank.id,
                version=bank.current_version).first()
            if not version: raise ValueError("题库发布版本不存在")
            self.bank_title = version.title
            return json.loads(version.snapshot_json)
        finally:
            db.close()

    async def _sync_time(self, websocket, player_id: str, event: dict) -> None:
        received = self.clock.epoch_ms(); sync_id = str(uuid.uuid4())
        record = TimeSyncRecord(sync_id, player_id, int(event.get("client_request_at_ms") or 0),
                                received, self.clock.epoch_ms(), received)
        self.sync_records[player_id] = record
        await websocket.send_json({"type": "time_sync_response", "sync_id": sync_id,
            "client_request_at_ms": record.client_request_at_ms,
            "server_received_at_ms": record.server_received_at_ms,
            "server_responded_at_ms": record.server_responded_at_ms})

    async def _open_next_question(self) -> None:
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            return await self._finish_game()
        self.current_question = self.questions[self.current_question_index]
        self.submissions = {}; self.attempt_counts = {}; self.submission_sequence = 0
        self.question_opened_at_ms = self.clock.epoch_ms()
        self.question_closes_at_ms = self.question_opened_at_ms + self.game_rules["time_limit_seconds"] * 1000
        self.phase = "answering"
        await self.broadcast_game_state()
        self.timer_task = asyncio.create_task(self._round_timeout(self.current_question_index))

    async def _round_timeout(self, question_index: int) -> None:
        await asyncio.sleep(self.game_rules["time_limit_seconds"])
        if self.phase == "answering" and self.current_question_index == question_index:
            await self._close_question()

    async def _submit_answer(self, player_id: str, event: dict) -> None:
        received = self.clock.epoch_ms()
        if self.phase != "answering" or player_id in self.submissions or not self.current_question:
            return
        if str(event.get("question_id")) != self.current_question.id:
            return await self.broadcast_to_player(player_id, {"type": "error", "message": "题目已变化，请刷新状态"})
        try:
            answer = self.current_question.parse_answer(event.get("answer"))
        except ValueError as exc:
            return await self.broadcast_to_player(player_id, {"type": "error", "message": str(exc)})
        self.attempt_counts[player_id] = self.attempt_counts.get(player_id, 0) + 1
        grading = self.current_question.grade(answer)
        if getattr(self.current_question, "allows_retry", False) and not grading.is_correct:
            return await self.broadcast_to_player(player_id, {"type": "answer_feedback",
                "question_id": self.current_question.id, "correct": False,
                "can_retry": True, "attempt_count": self.attempt_counts[player_id],
                "message": "答案不对，可以继续尝试"})
        self.submission_sequence += 1
        sync = self.sync_records.get(player_id)
        if sync and sync.sync_id != event.get("sync_id"): sync = None
        raw_time = event.get("client_submitted_at_ms")
        client_time = int(raw_time) if isinstance(raw_time, (int, float)) else None
        submission_time = self.timestamp_policy.resolve(player_id=player_id,
            client_submitted_at_ms=client_time, server_received_at_ms=received,
            question_opened_at_ms=self.question_opened_at_ms,
            question_closes_at_ms=self.question_closes_at_ms, sync_record=sync,
            receive_sequence=self.submission_sequence)
        self.submissions[player_id] = AnswerSubmission(player_id, self.current_question.id,
            answer, grading, submission_time,
            max(0, submission_time.effective_at_ms - self.question_opened_at_ms))
        await self.broadcast_to_player(player_id, {"type": "answer_received",
            "question_id": self.current_question.id, "correct": grading.is_correct,
            "attempt_count": self.attempt_counts[player_id],
            "timestamp_source": submission_time.source})
        await self.broadcast({"type": "submission_progress", "submitted": len(self.submissions),
                              "total": len(self.scores)})
        if len(self.submissions) >= len(self.scores):
            await self._close_question()

    async def _close_question(self) -> None:
        async with self.round_lock:
            if self.phase != "answering": return
            self.phase = "result"
            if self.timer_task and self.timer_task is not asyncio.current_task(): self.timer_task.cancel()
            scoring = RankedCorrectScoringStrategy(self.game_rules["rank_scores"],
                                                    self.game_rules["fallback_correct_score"])
            results = scoring.score_round(self.scores.keys(), self.submissions.values())
            for pid, item in results.items():
                self.scores[pid] += item.awarded_score
                if item.is_correct: self.correct_counts[pid] += 1
            public_results = {pid: {"score": item.awarded_score, "rank": item.correct_rank,
                "correct": item.is_correct, "elapsed_ms": item.elapsed_ms, "reason": item.reason}
                for pid, item in results.items()}
            self.round_results.append({"question_id": self.current_question.id,
                "correct_answer": self.current_question.result_view(),
                "submissions": {pid: item.answer.serialize() for pid, item in self.submissions.items()},
                "results": public_results})
            await self.broadcast({"type": "question_result", "question": self.current_question.result_view(),
                "results": public_results, "scores": self.scores,
                "next_question_at_ms": self.clock.epoch_ms() + self.game_rules["result_seconds"] * 1000})
            await asyncio.sleep(self.game_rules["result_seconds"])
            if self.state == "playing": await self._open_next_question()

    async def _finish_game(self) -> None:
        self.phase = "finished"; self.state = "finished"; self.room.status = "ended"
        ranking = sorted(self.scores, key=lambda pid: (-self.scores[pid], -self.correct_counts[pid], pid))
        self._persist_game_records()
        await self.broadcast({"type": "game_state", "state": "finished", "phase": "finished",
            "scores": self.scores, "correct_counts": self.correct_counts, "ranking": ranking,
            "round_results": self.round_results, "players": self._players_view(),
            "bank_title": self.bank_title})

    def _persist_game_records(self) -> None:
        db = SessionLocal()
        try:
            duration = max(0, (self.clock.epoch_ms() - self.started_at_ms) // 1000)
            total_rounds = len(self.round_results)
            for player_id in self.scores:
                if not str(player_id).isdigit():
                    continue
                session = GameRecordService.create_game_session(db, int(player_id),
                                                                 "new_quiz_game", self.room_id)
                for index, round_data in enumerate(self.round_results, 1):
                    result = round_data["results"][player_id]
                    answer = round_data["submissions"].get(player_id)
                    GameRecordService.create_game_round(db, session.id, index,
                        target_pattern=round_data["question_id"],
                        user_pattern=json.dumps(answer, ensure_ascii=False) if answer else None,
                        is_correct=result["correct"], response_time_ms=result["elapsed_ms"] or 0,
                        round_score=result["score"])
                accuracy = (self.correct_counts[player_id] / total_rounds * 100) if total_rounds else 0
                GameRecordService.update_game_session(db, session.id, int(player_id),
                    duration_seconds=duration, score=self.scores[player_id], accuracy=accuracy,
                    rounds_played=total_rounds, rounds_total=total_rounds, status="completed")
        except Exception as exc:
            db.rollback()
            print(f"newQuizGame 保存游戏记录失败: {exc}")
        finally:
            db.close()

    def _players_view(self):
        return {pid: {"id": p.id, "name": p.name, "avatar": p.avatar,
                      "connected": pid in self.connections.values()}
                for pid, p in self.persistent_players.items() if pid in self.scores or self.state == "waiting"}

    async def broadcast_game_state(self) -> None:
        payload = {"type": "game_state", "state": self.state, "phase": self.phase,
            "bank_title": self.bank_title, "question_index": self.current_question_index,
            "question_count": len(self.questions), "question": self.current_question.public_view() if self.current_question else None,
            "question_opened_at_ms": self.question_opened_at_ms,
            "question_closes_at_ms": self.question_closes_at_ms,
            "submitted_player_ids": list(self.submissions), "scores": self.scores,
            "players": self._players_view(), "rules": self.game_rules}
        await self.broadcast(payload)
