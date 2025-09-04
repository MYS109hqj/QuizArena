from .base import BaseGame
from .quiz_game import QuizGame

class GameFactory:
    """游戏工厂，创建不同类型的游戏实例"""
    @staticmethod
    def create_game(game_type: str, room_id: str) -> BaseGame:
        if game_type == "quiz":
            return QuizGame(room_id)
        # 未来可添加其他游戏类型
        # elif game_type == "guess":
        #     return GuessGame(room_id)
        else:
            raise ValueError(f"不支持的游戏类型: {game_type}")