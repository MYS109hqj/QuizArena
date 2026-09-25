from .base import BaseGame
from .quiz_game import QuizGame
from app.games.o2_SamePatternHunt.game import o2SPHGame
from app.games.o3_MemorialBanquet.game import o3MBGame
from app.games.o999_Template.game import o999TemplateGame
from app.games.o4_Flip7.game import o4Flip7Game
from app.games.o5_MazeRace.game import MazeRaceGame
from app.games.new_quiz_game.game import NewQuizGame

class GameFactory:
    """游戏工厂，创建不同类型的游戏实例"""
    @staticmethod
    def create_game(game_type: str, room_id: str) -> BaseGame:
        if game_type == "quiz":
            return QuizGame(room_id)
        elif game_type == "o2SPH":
            return o2SPHGame(room_id)
        elif game_type == "o3MB":
            return o3MBGame(room_id)
        elif game_type == "o999Template":
            return o999TemplateGame(room_id)
        elif game_type == "o4Flip7":
            return o4Flip7Game(room_id)
        elif game_type == "o5MazeRace":
            return MazeRaceGame(room_id)
        elif game_type == "newQuizGame":
            return NewQuizGame(room_id)
        else:
            raise ValueError(f"不支持的游戏类型: {game_type}")
