import asyncio
import json

from app.rooms import Room
from app.games.factory import GameFactory
from app.models.player import Player


class FakeWS:
    def __init__(self, name):
        self.name = name
        self.sent = []

    async def send_json(self, data):
        self.sent.append(data)

    async def send_text(self, text):
        self.sent.append(json.loads(text))


async def main():
    game = GameFactory.create_game('o5MazeRace', 'r1')
    room = Room('r1', game, owner_info={'id': '1', 'name': 'A', 'avatar': ''}, gameType='o5MazeRace')
    p1, p2 = Player('1', 'A', ''), Player('2', 'B', '')
    room.players['1'] = p1
    room.players['2'] = p2
    ws1, ws2 = FakeWS('ws1'), FakeWS('ws2')
    await room.connect(ws1, p1)
    await room.connect(ws2, p2)

    # B 准备
    await room.handle_event(ws2, {'type': 'toggle_ready'})

    # 房主切换定向越野
    await room.handle_event(ws1, {'type': 'update_settings', 'settings': {
        'rules': {'game_mode': 'orienteering', 'movement_mode': 'turns',
                  'reveal_hit_walls': True, 'wall_hit_threshold': 2}}})
    print('rules:', game.game_rules)
    print('config:', game.config)

    # 房主开始游戏
    await room.handle_event(ws1, {'type': 'start_game'})
    print('room.status:', room.status, '| game.state:', game.state)
    print('player_order:', game.player_order, '| current_player:', game.current_player)
    print('positions:', game.positions, '| targets:', game.targets)

    # 房主走 3 步
    for i in range(3):
        await room.handle_event(ws1, {'type': 'action', 'action': 'move', 'direction': 'right'})
        print(f'A move{i + 1}: turn_steps={game.turn_steps} current={game.current_player} pos1={game.positions["1"]}')

    # B 走 3 步
    for i in range(3):
        await room.handle_event(ws2, {'type': 'action', 'action': 'move', 'direction': 'left'})
        print(f'B move{i + 1}: turn_steps={game.turn_steps} current={game.current_player} pos2={game.positions["2"]}')

    gs = [m for m in ws2.sent if m.get('type') == 'game_state']
    if gs:
        last = gs[-1]
        print('game_state.players keys:', list(last['players'].keys()))
        print('current_player in players?', last['current_player'] in last['players'])
        print('rules sent:', last['rules'])
    else:
        print('!!! ws2 never received any game_state')

    errors = [m for m in ws1.sent + ws2.sent if m.get('type') == 'error']
    print('errors seen:', errors)


asyncio.run(main())
