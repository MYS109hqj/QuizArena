import { defineStore } from 'pinia';
import axios from 'axios';
import { useUserStore } from './userStore';
import { connectFlip7Socket, sendFlip7Message, closeFlip7Socket } from '../ws/flip7Socket';

const emptyGame = () => ({ state: 'waiting', rows: 8, cols: 8, walls: [], positions: {},
  targets: {}, start_positions: {}, home_positions: {}, checkpoints: [], visited_checkpoints: {}, steps: {}, players: {}, visible_walls: [], winner: null,
  current_player: null, turn_steps: 0, turn_number: 1,
  rules: { game_mode: 'classic', reveal_hit_walls: true, wall_hit_threshold: 2, movement_mode: 'turns', steps_per_turn: 3 } });

export const useMazeRaceStore = defineStore('mazeRace', {
  state: () => ({ rooms: [], room_id: null, room: {}, players: {}, player_id: '', player_name: '',
    avatarUrl: '', gameStatus: 'waiting', gameState: emptyGame(), creatingRoom: false,
    notice: null, rejectedMove: null }),
  actions: {
    async initStore() {
      const users = useUserStore();
      if (!users.isLoggedIn || !users.user) await users.checkLoginStatus();
      if (!users.isLoggedIn || !users.user) throw new Error('请先登录后再游戏');
      this.player_id = String(users.user.id);
      this.player_name = users.user.username || '玩家';
      this.avatarUrl = users.user.avatar || '';
    },
    async createRoom() {
      this.creatingRoom = true;
      try {
        await this.initStore();
        const { data } = await axios.post(`${import.meta.env.VITE_URL}/api/rooms/o5MazeRace`, {}, { withCredentials: true });
        await this.enterRoom(data.room_id);
        return data.room_id;
      } finally { this.creatingRoom = false; }
    },
    async enterRoom(roomId) {
      await this.initStore();
      await axios.post(`${import.meta.env.VITE_URL}/api/rooms/o5MazeRace/${roomId}/join`, {}, { withCredentials: true });
      this.room_id = roomId;
      connectFlip7Socket(data => this.handleMessage(data), roomId, {
        player_id: this.player_id, player_name: this.player_name, avatarUrl: this.avatarUrl,
      }, 'o5MazeRace');
    },
    async fetchRooms() {
      await this.initStore();
      const { data } = await axios.get(`${import.meta.env.VITE_URL}/api/room-list/o5MazeRace`, { withCredentials: true });
      this.rooms = data.rooms || [];
    },
    toggleReady() { sendFlip7Message({ type: 'toggle_ready' }); },
    startGame() { sendFlip7Message({ type: 'start_game' }); },
    updateRules(rules) { sendFlip7Message({ type: 'update_settings', settings: { rules } }); },
    move(direction) {
      if (this.gameState.state === 'playing') sendFlip7Message({ type: 'action', action: 'move', direction });
    },
    async leaveRoom(notifyServer = true) {
      const id = this.room_id;
      if (notifyServer && id) {
        try { await axios.delete(`${import.meta.env.VITE_URL}/api/rooms/o5MazeRace/${id}/membership`, { withCredentials: true }); }
        catch (_) { /* room may already have expired */ }
      }
      closeFlip7Socket();
      this.room_id = null; this.room = {}; this.players = {}; this.gameStatus = 'waiting';
      this.gameState = emptyGame(); this.rejectedMove = null;
    },
    handleMessage(data) {
      if (data.type === 'room_state') {
        this.room = data; this.players = data.players || {};
        this.gameStatus = data.status === 'playing' ? 'playing' : data.status === 'ended' ? 'finished' : 'waiting';
        if (data.extra?.error) this.notice = data.extra.error;
      } else if (data.type === 'game_state') {
        this.gameState = { ...emptyGame(), ...data };
        this.players = data.players || this.players;
        this.gameStatus = data.state === 'finished' ? 'finished' : 'playing';
      } else if (data.type === 'move_rejected') {
        this.rejectedMove = { ...data, token: Date.now() };
      } else if (data.type === 'error') this.notice = data.message || data.msg;
    },
  },
});
