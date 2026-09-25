from __future__ import annotations

import time
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    raise ValueError(f"暂不支持题型: {question_type}")
