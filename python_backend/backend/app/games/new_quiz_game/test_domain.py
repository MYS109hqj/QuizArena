from app.games.new_quiz_game.domain import (
    AnswerSubmission, EffectiveTimestampRankingPolicy, RankedCorrectScoringStrategy,
    SingleChoiceQuestion, SubmissionTime, TextQuestion, JianyingQuestion, TimeSyncRecord,
    ValidatedSynchronizedTimestampPolicy,
)


def make_question():
    return SingleChoiceQuestion({"id": "q1", "prompt": "2 + 2 = ?",
        "options": [{"id": "A", "text": "3"}, {"id": "B", "text": "4"}],
        "correct_option_id": "B", "explanation": "基础算术"})


def submission(player_id, effective, sequence, correct=True):
    question = make_question()
    answer = question.parse_answer("B" if correct else "A")
    timing = SubmissionTime(effective, effective + 20, sequence, effective, "synced_client", "sync")
    return AnswerSubmission(player_id, "q1", answer, question.grade(answer), timing, effective - 1000)


def test_single_choice_question_hides_answer_until_result():
    question = make_question()
    assert "correct_option_id" not in question.public_view()
    assert question.result_view()["correct_option_id"] == "B"
    assert question.grade(question.parse_answer({"option_id": "B"})).is_correct


def test_timestamp_policy_accepts_recent_synced_time_and_falls_back_for_forgery():
    policy = ValidatedSynchronizedTimestampPolicy()
    sync = TimeSyncRecord("s1", "p1", 900, 950, 951, 950)
    accepted = policy.resolve(player_id="p1", client_submitted_at_ms=1500,
        server_received_at_ms=1600, question_opened_at_ms=1000,
        question_closes_at_ms=5000, sync_record=sync, receive_sequence=1)
    assert accepted.effective_at_ms == 1500
    assert accepted.source == "synced_client"
    fallback = policy.resolve(player_id="p1", client_submitted_at_ms=-10000,
        server_received_at_ms=1600, question_opened_at_ms=1000,
        question_closes_at_ms=5000, sync_record=sync, receive_sequence=2)
    assert fallback.effective_at_ms == 1600
    assert fallback.source == "server_fallback"


def test_ranked_scoring_uses_effective_time_then_server_sequence():
    items = [submission("p2", 1200, 2), submission("p1", 1200, 1),
             submission("p3", 1300, 3), submission("p4", 1400, 4, False)]
    ranks = EffectiveTimestampRankingPolicy().rank_correct_submissions(items)
    assert [item.submission.player_id for item in ranks] == ["p1", "p2", "p3"]
    results = RankedCorrectScoringStrategy((10, 8, 7)).score_round(
        ("p1", "p2", "p3", "p4", "p5"), items)
    assert [results[pid].awarded_score for pid in ("p1", "p2", "p3", "p4", "p5")] == [10, 8, 7, 0, 0]


def test_text_and_jianying_questions_normalize_answers_and_hide_them():
    text = TextQuestion({"id": "t", "prompt": "回答", "accepted_answers": ["北京"]})
    assert text.grade(text.parse_answer(" 北 京！ ")).is_correct
    assert "accepted_answers" not in text.public_view()
    board = {"provider": "jianying", "groups": [[], [], [], [], []]}
    jianying = JianyingQuestion({"id": "j", "prompt": "猜词", "accepted_answers": ["画龙点睛"],
                                 "hint_board": board})
    assert jianying.allows_retry
    assert jianying.public_view()["hint_board"] == board
    assert "accepted_answers" not in jianying.public_view()
