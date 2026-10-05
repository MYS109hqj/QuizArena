from __future__ import annotations

import time
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable


class Clock(ABC):
    @abstractmethod
    def epoch_ms(self) -> int: ...


class SystemClock(Clock):
    def epoch_ms(self) -> int:
        return time.time_ns() // 1_000_000


class Answer(ABC):
    @abstractmethod
    def serialize(self) -> object: ...


@dataclass(frozen=True)
class SingleChoiceAnswer(Answer):
    option_id: str

    def serialize(self) -> object:
        return {"option_id": self.option_id}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return "".join(normalized.split()).translate(str.maketrans("", "", "，。！？、,.!?；;：:"))


@dataclass(frozen=True)
class TextAnswer(Answer):
    text: str

    def serialize(self) -> object:
        return {"text": self.text}


@dataclass(frozen=True)
class GradingResult:
    is_valid: bool
    is_correct: bool
    normalized_answer: object | None = None
    feedback: str = ""


class Question(ABC):
    @property
    @abstractmethod
    def question_type(self) -> str: ...

    @abstractmethod
    def validate_definition(self) -> None: ...

    @abstractmethod
    def parse_answer(self, raw_answer: object) -> Answer: ...

    @abstractmethod
    def grade(self, answer: Answer) -> GradingResult: ...

    @abstractmethod
    def public_view(self) -> dict[str, Any]: ...

    @abstractmethod
    def result_view(self) -> dict[str, Any]: ...


class SingleChoiceQuestion(Question):
    question_type = "single_choice"

    def __init__(self, data: dict[str, Any]):
        self.id = str(data["id"])
        self.prompt = str(data["prompt"])
        self.options = tuple(data["options"])
        self.correct_option_id = str(data["correct_option_id"])
        self.explanation = str(data.get("explanation") or "")
        self.default_score = int(data.get("default_score") or 10)
        self.validate_definition()

    def validate_definition(self) -> None:
        ids = [str(option["id"]) for option in self.options]
        if not self.prompt.strip():
            raise ValueError("题干不能为空")
        if len(ids) < 2 or len(ids) != len(set(ids)):
            raise ValueError("单选题需要至少两个且 ID 不重复的选项")
        if self.correct_option_id not in ids:
            raise ValueError("正确选项不存在")

    def parse_answer(self, raw_answer: object) -> SingleChoiceAnswer:
        option_id = raw_answer.get("option_id") if isinstance(raw_answer, dict) else raw_answer
        if not isinstance(option_id, str) or option_id not in {str(item["id"]) for item in self.options}:
            raise ValueError("无效的单选题答案")
        return SingleChoiceAnswer(option_id)

    def grade(self, answer: Answer) -> GradingResult:
        if not isinstance(answer, SingleChoiceAnswer):
            return GradingResult(False, False, feedback="答案类型不匹配")
        return GradingResult(True, answer.option_id == self.correct_option_id, answer.option_id)

    def public_view(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.question_type, "prompt": self.prompt,
                "options": list(self.options)}

    def result_view(self) -> dict[str, Any]:
        return {**self.public_view(), "correct_option_id": self.correct_option_id,
                "explanation": self.explanation}


class TextQuestion(Question):
    question_type = "text"
    allows_retry = False

    def __init__(self, data: dict[str, Any]):
        self.id = str(data["id"])
        self.prompt = str(data["prompt"])
        self.accepted_answers = tuple(str(value) for value in data.get("accepted_answers", []))
        self.explanation = str(data.get("explanation") or "")
        self.default_score = int(data.get("default_score") or 10)
        self.validate_definition()

    def validate_definition(self) -> None:
        if not self.prompt.strip():
            raise ValueError("题干不能为空")
        if not self.accepted_answers or any(not value.strip() for value in self.accepted_answers):
            raise ValueError("问答题至少需要一个非空答案")

    def parse_answer(self, raw_answer: object) -> TextAnswer:
        text = raw_answer.get("text") if isinstance(raw_answer, dict) else raw_answer
        if not isinstance(text, str) or not text.strip() or len(text) > 200:
            raise ValueError("请输入不超过 200 字的答案")
        return TextAnswer(text.strip())

    def grade(self, answer: Answer) -> GradingResult:
        if not isinstance(answer, TextAnswer):
            return GradingResult(False, False, feedback="答案类型不匹配")
        normalized = normalize_text(answer.text)
        correct = normalized in {normalize_text(value) for value in self.accepted_answers}
        return GradingResult(True, correct, normalized, "回答正确" if correct else "回答错误")

    def public_view(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.question_type, "prompt": self.prompt,
                "allows_retry": self.allows_retry}

    def result_view(self) -> dict[str, Any]:
        return {**self.public_view(), "accepted_answers": list(self.accepted_answers),
                "explanation": self.explanation}


class JianyingQuestion(TextQuestion):
    question_type = "jianying"
    allows_retry = True

    def __init__(self, data: dict[str, Any]):
        self.hint_board = dict(data.get("hint_board") or {})
        super().__init__(data)
        if self.hint_board.get("provider") != "jianying":
            raise ValueError("鉴影提示板数据无效")

    def public_view(self) -> dict[str, Any]:
        return {**super().public_view(), "hint_board": self.hint_board}


class MultiHintQuestion(TextQuestion):
    question_type = "multi_hint"
    allows_retry = True

    def __init__(self, data: dict[str, Any]):
        content = dict(data.get("content") or {})
        self.hints = tuple(str(value) for value in content.get("hints", []))
        interval = content.get("hint_interval_seconds")
        self.hint_interval_seconds = int(20 if interval is None else interval)
        super().__init__(data)

    def validate_definition(self) -> None:
        super().validate_definition()
        if len(self.hints) != 6 or any(not value.strip() for value in self.hints):
            raise ValueError("多提示题必须包含六个非空提示")
        if not 1 <= self.hint_interval_seconds <= 300:
            raise ValueError("提示间隔必须在 1 到 300 秒之间")

    def public_view(self) -> dict[str, Any]:
        # Hints are exposed by MultiStageHintFlow only when their stage is reached.
        return {"id": self.id, "type": self.question_type, "prompt": self.prompt,
                "allows_retry": True}

    def result_view(self) -> dict[str, Any]:
        return {**super().result_view(), "hints": list(self.hints)}


class StreamingTextQuestion(TextQuestion):
    question_type = "streaming_text"

    def __init__(self, data: dict[str, Any]):
        content = dict(data.get("content") or {})
        interval = content.get("character_interval_ms")
        after_reveal = content.get("answer_time_after_reveal_seconds")
        self.character_interval_ms = int(120 if interval is None else interval)
        self.answer_time_after_reveal_seconds = int(
            10 if after_reveal is None else after_reveal)
        super().__init__(data)

    def validate_definition(self) -> None:
        super().validate_definition()
        if not 20 <= self.character_interval_ms <= 5000:
            raise ValueError("流文本字符间隔必须在 20 到 5000 毫秒之间")
        if not 0 <= self.answer_time_after_reveal_seconds <= 300:
            raise ValueError("流完后的答题时间必须在 0 到 300 秒之间")

    def public_view(self) -> dict[str, Any]:
        # The complete prompt must never be sent before it has been revealed.
        return {"id": self.id, "type": self.question_type, "prompt": "",
                "allows_retry": False}

    def result_view(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.question_type, "prompt": self.prompt,
                "allows_retry": False, "accepted_answers": list(self.accepted_answers),
                "explanation": self.explanation}


@dataclass
class PlayerAttemptState:
    next_allowed_stage: int = 1
    finalized: bool = False
    attempt_count: int = 0


@dataclass(frozen=True)
class SubmissionPermission:
    allowed: bool
    reason: str = ""
    current_stage: int = 1
    next_allowed_stage: int = 1


@dataclass
class FlowRuntime:
    opened_at_ms: int
    closes_at_ms: int
    player_states: dict[str, PlayerAttemptState] = field(default_factory=dict)
    metadata: dict[str, int] = field(default_factory=dict)


class RetryEligibilityPolicy(ABC):
    @abstractmethod
    def next_allowed_stage(self, current_stage: int, attempt_count: int) -> int: ...


class SkipNextStagePolicy(RetryEligibilityPolicy):
    def next_allowed_stage(self, current_stage: int, attempt_count: int) -> int:
        return current_stage + 2


class QuestionFlowStrategy(ABC):
    @abstractmethod
    def create_runtime(self, question: Question, player_ids: Iterable[str],
                       opened_at_ms: int, default_time_limit_seconds: int) -> FlowRuntime: ...

    def current_stage(self, runtime: FlowRuntime, now_ms: int) -> int:
        return 1

    def permission(self, runtime: FlowRuntime, player_id: str,
                   now_ms: int) -> SubmissionPermission:
        state = runtime.player_states.get(player_id)
        stage = self.current_stage(runtime, now_ms)
        if state is None:
            return SubmissionPermission(False, "玩家不在本轮中", stage, stage)
        if now_ms >= runtime.closes_at_ms:
            return SubmissionPermission(False, "本题答题时间已结束", stage,
                                        state.next_allowed_stage)
        if state.finalized:
            return SubmissionPermission(False, "本题已经完成作答", stage,
                                        state.next_allowed_stage)
        if stage < state.next_allowed_stage:
            return SubmissionPermission(False, f"第 {state.next_allowed_stage} 阶段可再次作答",
                                        stage, state.next_allowed_stage)
        return SubmissionPermission(True, current_stage=stage,
                                    next_allowed_stage=state.next_allowed_stage)

    @abstractmethod
    def apply_result(self, runtime: FlowRuntime, player_id: str,
                     grading: GradingResult, now_ms: int) -> bool:
        """Update eligibility and return whether this attempt is the final submission."""

    def public_question_view(self, question: Question, runtime: FlowRuntime,
                             now_ms: int) -> dict[str, Any]:
        return question.public_view()

    def flow_view(self, runtime: FlowRuntime, player_id: str | None,
                  now_ms: int) -> dict[str, Any]:
        view = {"stage": self.current_stage(runtime, now_ms),
                "closes_at_ms": runtime.closes_at_ms}
        if player_id is not None:
            permission = self.permission(runtime, player_id, now_ms)
            view["answer_permission"] = {
                "can_submit": permission.allowed,
                "reason": permission.reason,
                "next_allowed_stage": permission.next_allowed_stage,
            }
        return view

    def next_update_at_ms(self, runtime: FlowRuntime, now_ms: int) -> int | None:
        return None


class FixedDeadlineFlow(QuestionFlowStrategy):
    def create_runtime(self, question, player_ids, opened_at_ms,
                       default_time_limit_seconds):
        return FlowRuntime(opened_at_ms,
            opened_at_ms + default_time_limit_seconds * 1000,
            {str(pid): PlayerAttemptState() for pid in player_ids})

    def apply_result(self, runtime, player_id, grading, now_ms):
        state = runtime.player_states[player_id]
        state.attempt_count += 1
        retry = getattr(self, "allows_retry", False)
        if grading.is_correct or not retry:
            state.finalized = True
            return True
        return False


class RetryUntilCorrectFlow(FixedDeadlineFlow):
    allows_retry = True


class MultiStageHintFlow(QuestionFlowStrategy):
    def __init__(self, retry_policy: RetryEligibilityPolicy | None = None):
        self.retry_policy = retry_policy or SkipNextStagePolicy()

    def current_stage(self, runtime, now_ms):
        interval_ms = runtime.metadata.get("hint_interval_ms")
        if interval_ms is None:
            # Stored on the runtime to keep all calculations independent of timers.
            raise RuntimeError("多提示题运行时缺少提示间隔")
        maximum = runtime.metadata["stage_count"]
        return min(maximum, max(1, (max(0, now_ms - runtime.opened_at_ms)
                                    // interval_ms) + 1))

    def create_runtime(self, question, player_ids, opened_at_ms,
                       default_time_limit_seconds):
        interval_ms = question.hint_interval_seconds * 1000
        runtime = FlowRuntime(opened_at_ms,
            opened_at_ms + (len(question.hints) + 1) * interval_ms,
            {str(pid): PlayerAttemptState() for pid in player_ids})
        runtime.metadata.update(hint_interval_ms=interval_ms,
                                stage_count=len(question.hints) + 1)
        return runtime

    def apply_result(self, runtime, player_id, grading, now_ms):
        state = runtime.player_states[player_id]
        state.attempt_count += 1
        if grading.is_correct:
            state.finalized = True
            return True
        stage = self.current_stage(runtime, now_ms)
        state.next_allowed_stage = self.retry_policy.next_allowed_stage(
            stage, state.attempt_count)
        return False

    def public_question_view(self, question, runtime, now_ms):
        stage = self.current_stage(runtime, now_ms)
        return {**question.public_view(),
                "visible_hints": list(question.hints[:min(stage, len(question.hints))])}

    def flow_view(self, runtime, player_id, now_ms):
        return {**super().flow_view(runtime, player_id, now_ms),
                "stage_count": runtime.metadata["stage_count"],
                "stage_closes_at_ms": min(runtime.closes_at_ms,
                    runtime.opened_at_ms + self.current_stage(runtime, now_ms)
                    * runtime.metadata["hint_interval_ms"])}

    def next_update_at_ms(self, runtime, now_ms):
        stage = self.current_stage(runtime, now_ms)
        if stage >= runtime.metadata["stage_count"]:
            return runtime.closes_at_ms
        return runtime.opened_at_ms + stage * runtime.metadata["hint_interval_ms"]


class StreamingRevealFlow(FixedDeadlineFlow):
    def create_runtime(self, question, player_ids, opened_at_ms,
                       default_time_limit_seconds):
        reveal_ms = len(question.prompt) * question.character_interval_ms
        runtime = FlowRuntime(opened_at_ms,
            opened_at_ms + reveal_ms + question.answer_time_after_reveal_seconds * 1000,
            {str(pid): PlayerAttemptState() for pid in player_ids})
        runtime.metadata.update(character_interval_ms=question.character_interval_ms,
                                character_count=len(question.prompt))
        return runtime

    def revealed_count(self, runtime, now_ms):
        elapsed = max(0, now_ms - runtime.opened_at_ms)
        return min(runtime.metadata["character_count"],
                   elapsed // runtime.metadata["character_interval_ms"])

    def public_question_view(self, question, runtime, now_ms):
        count = self.revealed_count(runtime, now_ms)
        return {**question.public_view(), "prompt": question.prompt[:count],
                "revealed_chars": count, "total_chars": len(question.prompt)}

    def next_update_at_ms(self, runtime, now_ms):
        count = self.revealed_count(runtime, now_ms)
        if count >= runtime.metadata["character_count"]:
            return runtime.closes_at_ms
        return runtime.opened_at_ms + (count + 1) * runtime.metadata["character_interval_ms"]


def flow_for_question(question: Question) -> QuestionFlowStrategy:
    if isinstance(question, MultiHintQuestion):
        return MultiStageHintFlow()
    if isinstance(question, StreamingTextQuestion):
        return StreamingRevealFlow()
    if isinstance(question, JianyingQuestion):
        return RetryUntilCorrectFlow()
    return FixedDeadlineFlow()


@dataclass(frozen=True)
class TimeSyncRecord:
    sync_id: str
    player_id: str
    client_request_at_ms: int
    server_received_at_ms: int
    server_responded_at_ms: int
    created_at_ms: int


@dataclass(frozen=True)
class SubmissionTime:
    client_submitted_at_ms: int | None
    server_received_at_ms: int
    receive_sequence: int
    effective_at_ms: int
    source: str
    sync_id: str | None = None


class SubmissionTimestampPolicy(ABC):
    @abstractmethod
    def resolve(self, *, player_id: str, client_submitted_at_ms: int | None,
                server_received_at_ms: int, question_opened_at_ms: int,
                question_closes_at_ms: int, sync_record: TimeSyncRecord | None,
                receive_sequence: int) -> SubmissionTime: ...


class ValidatedSynchronizedTimestampPolicy(SubmissionTimestampPolicy):
    def __init__(self, max_sync_age_ms: int = 60_000, max_receive_delta_ms: int = 3_000):
        self.max_sync_age_ms = max_sync_age_ms
        self.max_receive_delta_ms = max_receive_delta_ms

    def resolve(self, **values) -> SubmissionTime:
        client = values["client_submitted_at_ms"]
        received = values["server_received_at_ms"]
        opened = values["question_opened_at_ms"]
        closes = values["question_closes_at_ms"]
        sync = values["sync_record"]
        valid = (isinstance(client, int) and sync is not None
                 and sync.player_id == values["player_id"]
                 and received - sync.created_at_ms <= self.max_sync_age_ms
                 and opened <= client <= closes
                 and abs(received - client) <= self.max_receive_delta_ms)
        effective = client if valid else received
        effective = max(opened, min(effective, closes))
        return SubmissionTime(client if isinstance(client, int) else None, received,
                              values["receive_sequence"], effective,
                              "synced_client" if valid else "server_fallback",
                              sync.sync_id if sync else None)


@dataclass(frozen=True)
class AnswerSubmission:
    player_id: str
    question_id: str
    answer: Answer
    grading: GradingResult
    submission_time: SubmissionTime
    elapsed_ms: int


@dataclass(frozen=True)
class RankedSubmission:
    submission: AnswerSubmission
    rank: int


class RankingPolicy(ABC):
    @abstractmethod
    def rank_correct_submissions(self, submissions: Iterable[AnswerSubmission]) -> tuple[RankedSubmission, ...]: ...


class EffectiveTimestampRankingPolicy(RankingPolicy):
    def rank_correct_submissions(self, submissions):
        correct = sorted((item for item in submissions if item.grading.is_valid and item.grading.is_correct),
                         key=lambda item: (item.submission_time.effective_at_ms,
                                           item.submission_time.receive_sequence))
        return tuple(RankedSubmission(item, index) for index, item in enumerate(correct, 1))


@dataclass(frozen=True)
class PlayerScoreResult:
    player_id: str
    awarded_score: int
    correct_rank: int | None
    is_correct: bool
    elapsed_ms: int | None
    reason: str


class RoundScoringStrategy(ABC):
    @abstractmethod
    def score_round(self, player_ids: Iterable[str], submissions: Iterable[AnswerSubmission]) -> dict[str, PlayerScoreResult]: ...


class RankedCorrectScoringStrategy(RoundScoringStrategy):
    def __init__(self, rank_scores=(10, 8, 7), fallback_correct_score=5,
                 ranking_policy: RankingPolicy | None = None):
        self.rank_scores = tuple(int(value) for value in rank_scores)
        self.fallback_correct_score = int(fallback_correct_score)
        self.ranking_policy = ranking_policy or EffectiveTimestampRankingPolicy()

    def score_round(self, player_ids, submissions):
        submissions = tuple(submissions)
        by_player = {item.player_id: item for item in submissions}
        ranks = {item.submission.player_id: item.rank
                 for item in self.ranking_policy.rank_correct_submissions(submissions)}
        results = {}
        for player_id in player_ids:
            submission, rank = by_player.get(player_id), ranks.get(player_id)
            if rank is not None:
                score = self.rank_scores[rank - 1] if rank <= len(self.rank_scores) else self.fallback_correct_score
                results[player_id] = PlayerScoreResult(player_id, score, rank, True,
                                                        submission.elapsed_ms, f"第 {rank} 位答对")
            elif submission:
                results[player_id] = PlayerScoreResult(player_id, 0, None, False,
                                                        submission.elapsed_ms, "回答错误")
            else:
                results[player_id] = PlayerScoreResult(player_id, 0, None, False, None, "未作答")
        return results


def question_from_snapshot(data: dict[str, Any]) -> Question:
    question_type = data.get("type", "single_choice")
    if question_type == "single_choice":
        return SingleChoiceQuestion(data)
    if question_type == "text":
        return TextQuestion(data)
    if question_type == "jianying":
        return JianyingQuestion(data)
    if question_type == "multi_hint":
        return MultiHintQuestion(data)
    if question_type == "streaming_text":
        return StreamingTextQuestion(data)
    raise ValueError(f"暂不支持题型: {question_type}")
