from __future__ import annotations

import hashlib
import os
import random
from collections import deque
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PRESET = {"piece_count": 5, "density": "minimum_topology_preserving",
          "visible_ms": 620, "blank_ms": 160, "mode": "baseline"}
SIZES = (14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36)


def _font_path() -> str:
    candidates = [os.getenv("JIANYING_FONT_PATH"), "C:/Windows/Fonts/msyhbd.ttc",
                  "C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file(): return candidate
    raise RuntimeError("未找到鉴影中文字体，请设置 JIANYING_FONT_PATH")


def _rasterize(text: str, size: int, gap: int = 2) -> list[list[bool]]:
    scale = 5
    image = Image.new("L", (len(text) * size * scale, size * scale), 255)
    draw = ImageDraw.Draw(image); font = ImageFont.truetype(_font_path(), int(size * scale * .86))
    for index, character in enumerate(text):
        box = draw.textbbox((0, 0), character, font=font)
        x = index * size * scale + (size * scale - (box[2] - box[0])) / 2 - box[0]
        y = size * scale * .52 - (box[3] - box[1]) / 2 - box[1]
        draw.text((x, y), character, fill=0, font=font)
    columns = len(text) * size + (len(text) - 1) * gap
    grid = [[False] * columns for _ in range(size)]; pixels = image.load()
    for char_index in range(len(text)):
        for y in range(size):
            for x in range(size):
                values = [255 - pixels[char_index * size * scale + x * scale + px, y * scale + py]
                          for py in range(1, scale - 1) for px in range(1, scale - 1)]
                grid[y][char_index * (size + gap) + x] = sum(values) / len(values) > 82
    return grid


def _topology(grid: list[list[bool]]) -> tuple[int, int]:
    def components(value: bool, holes=False) -> int:
        seen, count = set(), 0
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell != value or (x, y) in seen: continue
                queue, touches = deque([(x, y)]), False; seen.add((x, y))
                while queue:
                    cx, cy = queue.popleft(); touches |= cx in (0, len(row)-1) or cy in (0, len(grid)-1)
                    for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0 <= ny < len(grid) and 0 <= nx < len(row) and grid[ny][nx] == value and (nx,ny) not in seen:
                            seen.add((nx,ny)); queue.append((nx,ny))
                if not holes or not touches: count += 1
        return count
    return components(True), components(False, True)


def _minimum_size(answer: str) -> int:
    required = SIZES[0]
    for character in answer:
        reference = _topology(_rasterize(character, 42, 0))
        suitable = next((size for size in SIZES if _topology(_rasterize(character, size, 0)) == reference), SIZES[-1])
        required = max(required, suitable)
    return required


def build_hint_board(answer: str, seed: int) -> dict[str, Any]:
    if not isinstance(answer, str) or not answer.strip(): raise ValueError("鉴影答案不能为空")
    answer = answer.strip(); size = _minimum_size(answer); grid = _rasterize(answer, size)
    cells = [{"x": x, "y": y} for y, row in enumerate(grid) for x, active in enumerate(row) if active]
    randomizer = random.Random(seed); randomizer.shuffle(cells)
    groups = [cells[index::PRESET["piece_count"]] for index in range(PRESET["piece_count"])]
    return {"provider": "jianying", "interface_version": 1, "preset": dict(PRESET),
            "rows": len(grid), "columns": len(grid[0]), "groups": groups,
            "fingerprint": hashlib.sha256(f"{seed}:{answer}".encode()).hexdigest()[:16]}
