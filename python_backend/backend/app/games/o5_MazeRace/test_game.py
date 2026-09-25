import asyncio
from collections import deque

from app.games.o5_MazeRace.game import MazeRaceGame
from app.games.o5_MazeRace.source_adapter import (
    _source_path,
    edge_corner_distances,
    generate_from_original,
    has_balanced_edge_distances,
)


def reachable(walls, start=0):
    seen = {start}
    queue = deque([start])
    moves = [(-1, 0, 0), (0, -1, 1), (0, 1, 2), (1, 0, 3)]
    while queue:
        cell = queue.popleft()
        row, col = divmod(cell, 8)
        for dr, dc, wall in moves:
            nr, nc = row + dr, col + dc
            nxt = nr * 8 + nc
            if 0 <= nr < 8 and 0 <= nc < 8 and not walls[cell][wall] and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def test_generated_maze_is_connected_and_has_consistent_walls():
    assert _source_path().as_posix().endswith(
        "minigame/240914QtProject_HiddenWall_TheMaze/python_backend/maze_generator.py"
    )
    walls = generate_from_original(12345)
    assert len(walls) == 64
    assert 63 in reachable(walls, 0)
    assert 56 in reachable(walls, 7)
    distances = edge_corner_distances(walls)
    assert max(distances) - min(distances) <= 8
    assert has_balanced_edge_distances(walls)
    for index, cell in enumerate(walls):
        row, col = divmod(index, 8)
        if col < 7:
            assert cell[2] == walls[index + 1][1]
        if row < 7:
            assert cell[3] == walls[index + 8][0]


def test_edge_distance_balance_rejects_an_unbalanced_map():
    # A Hamiltonian snake is connected but gives very different edge-to-edge routes.
    walls = [[1, 1, 1, 1] for _ in range(64)]
    path = []
    for row in range(8):
        cells = list(range(row * 8, row * 8 + 8))
        path.extend(cells if row % 2 == 0 else reversed(cells))
    for first, second in zip(path, path[1:]):
        delta = second - first
        if delta == 1:
            walls[first][2] = 0
            walls[second][1] = 0
        elif delta == -1:
            walls[first][1] = 0
            walls[second][2] = 0
        else:
            walls[first][3] = 0
            walls[second][0] = 0
    distances = edge_corner_distances(walls)
    assert 999 not in distances
    assert max(distances) - min(distances) > 8
    assert not has_balanced_edge_distances(walls)


def test_move_reaches_target_and_finishes_game():
    game = MazeRaceGame("room")
    game.state = "playing"
    game.walls = [[1, 1, 1, 1] for _ in range(64)]
    game.walls[0][2] = 0
    game.walls[1][1] = 0
    game.positions = {"p1": 0, "p2": 63}
    game.targets = {"p1": 1, "p2": 0}
    game.steps = {"p1": 0, "p2": 0}
    game.game_rules["movement_mode"] = "free"
    game.broadcast_game_state = lambda: _noop()
    asyncio.run(game.move("p1", "right"))
    assert game.positions["p1"] == 1
    assert game.steps["p1"] == 1
    assert game.winner == "p1"
    assert game.state == "finished"


def test_repeated_wall_hits_are_private_and_use_one_physical_wall_key():
    game = MazeRaceGame("room")
    game.wall_hit_counts = {"p1": {}, "p2": {}}
    assert game._record_wall_hit("p1", 8, 9) == (1, False)
    # Hitting the same wall from its other side counts toward the same threshold.
    assert game._record_wall_hit("p1", 9, 8) == (2, True)
    assert game._visible_walls_for("p1") == [[8, 2], [9, 1]]
    assert game._visible_walls_for("p2") == []


def test_wall_reveal_can_be_disabled_and_threshold_is_configurable():
    game = MazeRaceGame("room")
    game.wall_hit_counts = {"p1": {}}
    game.game_rules["wall_hit_threshold"] = 3
    game._record_wall_hit("p1", 16, 24)
    game._record_wall_hit("p1", 16, 24)
    assert game._visible_walls_for("p1") == []
    assert game._record_wall_hit("p1", 16, 24) == (3, True)
    assert game._visible_walls_for("p1") == [[16, 3], [24, 0]]
    game.game_rules["reveal_hit_walls"] = False
    assert game._visible_walls_for("p1") == []


def test_turn_changes_after_three_legal_steps():
    game = MazeRaceGame("room")
    game.state = "playing"
    game.player_order = ["p1", "p2"]
    game.current_player = "p1"
    game.positions = {"p1": 8, "p2": 63}
    game.start_positions = {"p1": 56, "p2": 63}
    game.targets = {"p1": 7, "p2": 0}
    game.steps = {"p1": 0, "p2": 0}
    game.walls = [[1, 1, 1, 1] for _ in range(64)]
    for first, second in ((8, 9), (9, 10), (10, 11)):
        game.walls[first][2] = 0
        game.walls[second][1] = 0
    game.broadcast_game_state = lambda: _noop()
    asyncio.run(game.move("p1", "right"))
    asyncio.run(game.move("p1", "right"))
    assert game.current_player == "p1"
    assert game.turn_steps == 2
    asyncio.run(game.move("p1", "right"))
    assert game.current_player == "p2"
    assert game.turn_steps == 0
    assert game.positions["p1"] == 11


def test_wall_hit_returns_to_start_and_ends_turn():
    game = MazeRaceGame("room")
    game.state = "playing"
    game.player_order = ["p1", "p2"]
    game.current_player = "p1"
    game.turn_steps = 1
    game.positions = {"p1": 9, "p2": 63}
    game.start_positions = {"p1": 56, "p2": 63}
    game.targets = {"p1": 7, "p2": 0}
    game.steps = {"p1": 1, "p2": 0}
    game.wall_hit_counts = {"p1": {}, "p2": {}}
    game.walls = [[1, 1, 1, 1] for _ in range(64)]
    game.broadcast_game_state = lambda: _noop()
    game.broadcast_to_player = lambda *_args: _noop()
    asyncio.run(game.move("p1", "right"))
    assert game.positions["p1"] == 56
    assert game.current_player == "p2"
    assert game.turn_steps == 0
    assert game.wall_hit_counts["p1"]["9:10"] == 1


async def _noop():
    return None


def test_orienteering_requires_three_foreign_corners_then_own_start():
    game = MazeRaceGame("room")
    game.game_rules["game_mode"] = "orienteering"
    game.state = "playing"
    game.start_positions = {"p1": 0}
    game.home_positions = {"p1": 0}
    game.positions = {"p1": 7}
    game.visited_checkpoints = {"p1": []}
    for position in (7, 63, 56):
        game.positions["p1"] = position
        game._update_orienteering_progress("p1")
        assert game.state == "playing"
        assert game.start_positions["p1"] == position
    game.positions["p1"] = 0
    game._update_orienteering_progress("p1")
    assert game.winner == "p1"
    assert game.finish_reason == "orienteering_complete"


def test_orienteering_does_not_finish_when_a_corner_is_missing():
    game = MazeRaceGame("room")
    game.game_rules["game_mode"] = "orienteering"
    game.state = "playing"
    game.start_positions = {"p1": 0}
    game.home_positions = {"p1": 0}
    game.positions = {"p1": 0}
    game.visited_checkpoints = {"p1": [7, 63]}
    game._update_orienteering_progress("p1")
    assert game.state == "playing"
    assert game.winner is None


def test_orienteering_wall_hit_respawns_at_latest_checkpoint():
    game = MazeRaceGame("room")
    game.game_rules.update({"game_mode": "orienteering", "movement_mode": "free"})
    game.state = "playing"
    game.start_positions = {"p1": 0}
    game.home_positions = {"p1": 0}
    game.positions = {"p1": 7}
    game.visited_checkpoints = {"p1": []}
    game.wall_hit_counts = {"p1": {}}
    game.steps = {"p1": 1}
    game.walls = [[1, 1, 1, 1] for _ in range(64)]
    game._update_orienteering_progress("p1")
    assert game.start_positions["p1"] == 7
    game.positions["p1"] = 8
    game.broadcast_game_state = lambda: _noop()
    game.broadcast_to_player = lambda *_args: _noop()
    asyncio.run(game.move("p1", "right"))
    assert game.positions["p1"] == 7
