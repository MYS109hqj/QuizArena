class Player:
    """玩家模型"""
    def __init__(self, id: str, name: str, avatar: str):
        self.id = id
        self.name = name
        self.avatar = avatar
        self.submitted_answer: str = ""
        self.timestamp: str = ""
        # 初始化游戏数据
        self.content = {
            "scoring": {"score": 0, "round_score": 0},
            "survival": {"lives": 3, "lost_lives_this_round": 0},
            "judgement_correct": False
        }