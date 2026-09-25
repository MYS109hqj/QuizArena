import { defineStore } from 'pinia';
import axios from 'axios';
import { useUserStore } from './userStore';
import { connectFlip7Socket, sendFlip7Message, closeFlip7Socket } from '../ws/flip7Socket';

const defaultDeckSpec = () => ({ preset: 'base', name: '官方基础版', number_max: 12,
  special_numbers: { zero: false, unlucky_7: false, lucky_13: false },
  actions: { flip_3: 3, freeze: 3, second_chance: 3 },
  modifiers: { times_2: 1, plus_2: 1, plus_4: 1, plus_6: 1, plus_8: 1, plus_10: 1 } });
const defaultRules = () => ({ deck_preset: 'base', deck_spec: defaultDeckSpec(),
  vengeance_mode: false, brutal_mode: false, win_score: 200, flip7_bonus: 15,
  probability_enabled: false, probability_visibility: 'all', random_seed: null });
const defaultGameState = () => ({ state: 'waiting', current_player: null, round: 1,
  player_states: {}, pending_action: null, flip3_state: { active: false },
  remaining_cards: 94, discard_count: 0, rules: defaultRules(), probabilities: {},
  autoplay_states: {} });

function userData() {
  const users = useUserStore();
  if (users.isLoggedIn && users.user) return {
    player_id: String(users.user.id), player_name: users.user.username || '玩家',
    avatarUrl: users.user.avatar || ''
  };
  return null;
}

export const useFlip7Store = defineStore('flip7', {
  state: () => ({
    rooms: [], creatingRoom: false, connected: false, initializing: false,
    player_id: '', player_name: '', avatarUrl: '', room_id: null,
    playerDirectory: {},
    room: {}, players: {}, gameStatus: 'waiting', gameState: defaultGameState(),
    roundHistory: [], lastCard: null, notice: null,
  }),
  actions: {
    async initStore() {
      const users = useUserStore();
      if (!users.isLoggedIn || !users.user) await users.checkLoginStatus();
      const identity = userData();
      if (!identity) throw new Error('请先登录后再游玩');
      Object.assign(this, identity);
      return true;
    },
    async createRoom() {
      this.creatingRoom = true;
      try {
        await this.initStore();
        const { data } = await axios.post(`${import.meta.env.VITE_URL}/api/rooms/o4Flip7`, {}, { withCredentials: true });
        await this.enterRoom(data.room_id);
        return data.room_id;
      } finally { this.creatingRoom = false; }
    },
    async enterRoom(roomId) {
      this.initializing = true;
      try {
        await this.initStore();
        await axios.post(`${import.meta.env.VITE_URL}/api/rooms/o4Flip7/${roomId}/join`, {}, { withCredentials: true });
      } catch (error) {
        this.showNotice(error.response?.data?.detail || error.message || '无法加入房间', 'error');
        throw error;
      } finally { this.initializing = false; }
      this.room_id = roomId;
      connectFlip7Socket(data => this.handleMessage(data), roomId, {
        player_id: this.player_id, player_name: this.player_name, avatarUrl: this.avatarUrl
      });
    },
    async fetchRooms() {
      const { data } = await axios.get(`${import.meta.env.VITE_URL}/api/room-list/o4Flip7`);
      this.rooms = data.rooms || [];
    },
    async leaveRoom(notifyServer = true) {
      const roomId = this.room_id;
      if (notifyServer && roomId) {
        try { await axios.delete(`${import.meta.env.VITE_URL}/api/rooms/o4Flip7/${roomId}/membership`, { withCredentials: true }); }
        catch (error) { console.error('退出房间失败', error); }
      }
      closeFlip7Socket(); this.room_id = null; this.room = {}; this.players = {};
      this.gameStatus = 'waiting'; this.gameState = defaultGameState();
      this.roundHistory = []; this.lastCard = null;
    },
    startGame() { sendFlip7Message({ type: 'start_game' }); },
    toggleReady() { sendFlip7Message({ type: 'toggle_ready' }); },
    drawCard() { sendFlip7Message({ type: 'action', action: 'draw', decision_id: this.gameState.decision?.id }); },
    stopTurn() { sendFlip7Message({ type: 'action', action: 'stop', decision_id: this.gameState.decision?.id }); },
    savePlayerStrategy(strategy) {
      sendFlip7Message({ type: 'save_player_strategy', strategy });
    },
    setStrategyAutoplay(enabled) {
      sendFlip7Message({ type: 'set_strategy_autoplay', enabled });
    },
    cancelSystemManaged() { sendFlip7Message({ type: 'cancel_system_managed' }); },
    addBot(config) { sendFlip7Message({ type: 'add_bot', config }); },
    removeBot(botId) { sendFlip7Message({ type: 'remove_bot', bot_id: botId }); },
    async kickMember(playerId) {
      await axios.delete(`${import.meta.env.VITE_URL}/api/rooms/o4Flip7/${this.room_id}/members/${playerId}`, { withCredentials: true });
    },
    selectTarget(targetId, cardId = null, ownCardId = null, secondTargetId = null, secondCardId = null) {
      sendFlip7Message({ type: 'action', action: 'select_target', decision_id: this.gameState.decision?.id, data: {
        target_id: targetId, card_id: cardId, own_card_id: ownCardId,
        second_target_id: secondTargetId, second_card_id: secondCardId } });
    },
    updateRules(rules) {
      const normalized = { ...rules,
        vengeance_mode: rules.deck_preset === 'vengeance',
        brutal_mode: ['vengeance', 'custom'].includes(rules.deck_preset) && rules.brutal_mode };
      sendFlip7Message({ type: 'update_settings', settings: { rules: normalized } });
    },
    handleMessage(data) {
      if (data.type === 'room_state') {
        this.room = data;
        this.playerDirectory = { ...this.playerDirectory, ...(data.players || {}) };
        this.players = data.players || {};
        if (data.rules) this.gameState.rules = data.rules;
        if (data.error) this.showNotice(data.error, 'error');
        this.gameStatus = data.status === 'playing' ? 'playing' : 'waiting';
      } else if (data.type === 'player_list') {
        this.players = Object.fromEntries((data.players || []).map(p => [p.id, p]));
        this.playerDirectory = { ...this.playerDirectory, ...this.players };
      } else if (data.type === 'game_state') {
        const oldRound = this.gameState.round;
        this.gameState = { ...defaultGameState(), ...data };
        if (data.players) {
          this.players = data.players;
          this.playerDirectory = { ...this.playerDirectory, ...data.players };
        }
        this.gameStatus = data.state === 'finished' ? 'finished' : 'playing';
        if (data.round > oldRound) this.roundHistory = [];
      } else if (data.type === 'card_drawn') {
        this.lastCard = data; this.roundHistory.push(data);
      } else if (data.type === 'pending_action') {
        this.gameState.pending_action = data.action;
      } else if (data.type === 'probability_state') {
        this.gameState.probabilities = { ...this.gameState.probabilities, ...(data.probabilities || {}) };
      } else if (data.type === 'player_strategy_saved') {
        const previous = this.gameState.autoplay_states?.[this.player_id] || {};
        this.gameState.autoplay_states = {
          ...this.gameState.autoplay_states,
          [this.player_id]: { ...previous, strategy: data.strategy },
        };
        this.showNotice('策略已保存');
      } else if (data.type === 'rules_updated' || data.type === 'settings_updated') {
        if (data.rules) this.gameState.rules = data.rules;
      } else if (data.type === 'game_finished') {
        this.gameState.state = 'finished'; this.gameStatus = 'finished';
      } else if (data.type === 'removed_from_room') {
        this.showNotice(data.reason === 'kicked' ? '你已被房主移出房间' : '已退出房间', 'error');
        this.leaveRoom(false);
      } else if (data.type === 'error' || data.type === 'rules_error') {
        this.showNotice(data.message || data.msg || '操作失败', 'error');
      }
    },
    showNotice(message, kind = 'info') {
      const token = Date.now();
      this.notice = { message, kind, token };
      setTimeout(() => { if (this.notice?.token === token) this.notice = null; }, 3500);
    },
    getPlayerName(id) {
      const player = this.players[id] || this.playerDirectory[id];
      if (!player) return id;
      if (!player.is_bot) return player.name;
      const threshold = Number(player.strategy_threshold);
      const suffix = player.strategy === 'score_threshold'
        ? `分数阈值 ${threshold}分`
        : player.strategy === 'risk_threshold'
          ? `概率阈值 ${(threshold * 100).toFixed(0)}%`
          : '随机策略';
      return `${player.name}（${suffix}）`;
    },
    resetStore() { this.leaveRoom(); this.rooms = []; },
  }
});
