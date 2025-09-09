# backend/app/games/strategies.py
from abc import ABC, abstractmethod
from typing import Dict

class ScoringStrategy(ABC):
    """计分策略基类"""
    @abstractmethod
    def calculate(self, player_data: Dict, answer: str) -> int:
        pass

class QuizScoringStrategy(ScoringStrategy):
    """答题游戏计分策略（按正确率）"""
    def calculate(self, player_data: Dict, answer: str) -> int:
        return 10 if answer == player_data.get("correct_answer") else 0

class GuessScoringStrategy(ScoringStrategy):
    """猜谜游戏计分策略（按次数）"""
    def calculate(self, player_data: Dict, answer: str) -> int:
        return max(0, 20 - player_data.get("attempts", 0) * 5)