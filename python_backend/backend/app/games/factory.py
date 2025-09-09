from .base import BaseGame
from .quiz_game import QuizGame
from app.games.o2_SamePatternHunt.game import o2SPHGame

class GameFactory:
    """游戏工厂，创建不同类型的游戏实例"""
    @staticmethod
    def create_game(game_type: str, room_id: str) -> BaseGame:
        if game_type == "quiz":
            return QuizGame(room_id)
        elif game_type == "o2SPH":
            return o2SPHGame(room_id)
        else:
            raise ValueError(f"不支持的游戏类型: {game_type}")