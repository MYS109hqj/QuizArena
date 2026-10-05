import asyncio
from types import SimpleNamespace

from app.games.new_quiz_game.game import NewQuizGame
from app.models.player import Player


def test_one_question_game_runs_from_start_to_ranked_finish():
    game = NewQuizGame("room")
    players = {"p1": Player("p1", "一号", ""), "p2": Player("p2", "二号", "")}
    room = SimpleNamespace(players=players, owner={"id": "p1"}, status="waiting")
    game.set_room_reference(room)
    game.persistent_players.update(players)
    game.game_rules.update({"question_count": 1, "time_limit_seconds": 100, "result_seconds": 0})
    game._load_snapshot = lambda: {"questions": [{"id": "q1", "type": "single_choice",
        "prompt": "答案选 B", "options": [{"id": "A", "text": "A"}, {"id": "B", "text": "B"}],
        "correct_option_id": "B", "explanation": "测试"}]}

    async def run():
        await game.start_game()
        await game._submit_answer("p1", {"question_id": "q1", "answer": {"option_id": "B"}})
        await game._submit_answer("p2", {"question_id": "q1", "answer": {"option_id": "B"}})

    asyncio.run(run())
    assert game.state == "finished"
    assert game.scores == {"p1": 10, "p2": 8}
    assert room.status == "ended"


def test_jianying_wrong_answer_can_retry_until_first_correct_answer():
    game = NewQuizGame("room")
    player = Player("p1", "一号", "")
    room = SimpleNamespace(players={"p1": player}, owner={"id": "p1"}, status="waiting")
    game.set_room_reference(room); game.persistent_players["p1"] = player
    game.game_rules.update({"time_limit_seconds": 100, "result_seconds": 0})
    game._load_snapshot = lambda: {"questions": [{"id": "j1", "type": "jianying",
        "prompt": "猜词", "accepted_answers": ["画龙点睛"],
        "hint_board": {"provider": "jianying", "groups": [[], [], [], [], []]}}]}

    async def run():
        await game.start_game()
        await game._submit_answer("p1", {"question_id": "j1", "answer": {"text": "错误"}})
        assert "p1" not in game.submissions
        await game._submit_answer("p1", {"question_id": "j1", "answer": {"text": "画龙点睛"}})

    asyncio.run(run())
    assert game.scores == {"p1": 10}
    assert game.attempt_counts == {"p1": 2}


def test_multi_hint_wrong_answer_uses_next_allowed_stage_and_resets_per_question():
    game = NewQuizGame("room")
    player = Player("p1", "一号", "")
    room = SimpleNamespace(players={"p1": player}, owner={"id": "p1"}, status="waiting")
    game.set_room_reference(room); game.persistent_players["p1"] = player
    game.game_rules.update({"result_seconds": 0})
    game._load_snapshot = lambda: {"questions": [{"id": "h1", "type": "multi_hint",
        "prompt": "猜事物", "accepted_answers": ["缓存"],
        "content": {"hints": [f"提示{i}" for i in range(1, 7)],
                    "hint_interval_seconds": 20}}]}

    async def run():
        await game.start_game()
        await game._submit_answer("p1", {"question_id": "h1", "answer": {"text": "内存"}})
        assert "p1" not in game.submissions
        assert game.flow_runtime.player_states["p1"].next_allowed_stage == 3
        await game._submit_answer("p1", {"question_id": "h1", "answer": {"text": "缓存"}})
        assert "p1" not in game.submissions
        game.flow_runtime.opened_at_ms -= 40_000
        game.flow_runtime.closes_at_ms -= 40_000
        game.question_opened_at_ms -= 40_000
        game.question_closes_at_ms -= 40_000
        await game._submit_answer("p1", {"question_id": "h1", "answer": {"text": "缓存"}})

    asyncio.run(run())
    assert game.scores == {"p1": 10}
