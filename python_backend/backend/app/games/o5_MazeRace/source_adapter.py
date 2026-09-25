"""Adapter for the original HiddenWall/TheMaze Python generator.

The algorithm remains owned by:
minigame/240914QtProject_HiddenWall_TheMaze/python_backend/maze_generator.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import threading
from collections import deque
from pathlib import Path
from types import ModuleType
from typing import List, Sequence


_GENERATOR_LOCK = threading.Lock()
_GENERATOR_MODULE: ModuleType | None = None


def _source_path() -> Path:
    repository_root = Path(__file__).resolve().parents[5]
    return repository_root / "minigame" / "240914QtProject_HiddenWall_TheMaze" / "python_backend" / "maze_generator.py"


def _load_generator() -> ModuleType:
    global _GENERATOR_MODULE
    if _GENERATOR_MODULE is not None:
        return _GENERATOR_MODULE
    path = _source_path()
    if not path.is_file():
        raise RuntimeError(f"TheMaze 原始迷宫算法文件不存在: {path}")
    spec = importlib.util.spec_from_file_location("themaze_original_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 TheMaze 原始迷宫算法: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _GENERATOR_MODULE = module
    return module


EDGE_CORNER_PAIRS = ((0, 7), (7, 63), (56, 63), (0, 56))
MOVES = ((-1, 0, 0), (0, -1, 1), (0, 1, 2), (1, 0, 3))


def shortest_path_distance(walls: Sequence[Sequence[int]], start: int, target: int) -> int:
    """Return the number of legal moves in the shortest route between two cells."""
    distances = {start: 0}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == target:
            return distances[cell]
        row, col = divmod(cell, 8)
        for row_delta, col_delta, wall_index in MOVES:
            next_row, next_col = row + row_delta, col + col_delta
            if not (0 <= next_row < 8 and 0 <= next_col < 8) or walls[cell][wall_index]:
                continue
            neighbor = next_row * 8 + next_col
            if neighbor not in distances:
                distances[neighbor] = distances[cell] + 1
                queue.append(neighbor)
    return 999


def edge_corner_distances(walls: Sequence[Sequence[int]]) -> List[int]:
    """Shortest path lengths between the two endpoints of each map edge."""
    return [shortest_path_distance(walls, start, target) for start, target in EDGE_CORNER_PAIRS]


def has_balanced_edge_distances(walls: Sequence[Sequence[int]], tolerance: int = 8) -> bool:
    distances = edge_corner_distances(walls)
    return 999 not in distances and max(distances) - min(distances) <= tolerance


def generate_from_original(seed: int, max_attempts: int = 200) -> List[List[int]]:
    """Run the original blocked-DFS/cut/check_bfs pipeline and copy its walls."""
    with _GENERATOR_LOCK:
        generator = _load_generator()
        generator.random.seed(seed)
        for _ in range(max_attempts):
            # The source contains optional debug prints; the game server stays quiet.
            with contextlib.redirect_stdout(io.StringIO()):
                generator.init_data()
            first_diagonal = generator.bfs(0, 63, False)
            second_diagonal = generator.bfs(7, 56, False)
            # Mirrors the Qt reset condition's path checks. The source pipeline
            # itself performs its specialized dead-end cleanup in check_bfs().
            if first_diagonal != 999 and second_diagonal != 999 and first_diagonal != 14 and second_diagonal != 14:
                walls = [list(cell[:4]) for cell in generator.wall]
                if has_balanced_edge_distances(walls):
                    return walls
        raise RuntimeError("TheMaze 原始算法未能在限定次数内生成有效迷宫")
