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
  remaining_cards: 94, discard_count: 0, rules: defaultRules(), probabilities: {} });

function userData() {
  const users = useUserStore();
  if (users.isLoggedIn && users.user) return {
    player_id: String(users.user.id), player_name: users.user.username || '玩家',
    avatarUrl: users.user.avatar || ''
  };
  let id = localStorage.getItem('flip7_guest_id');
  if (!id) { id = `guest-${crypto.randomUUID()}`; localStorage.setItem('flip7_guest_id', id); }
  return { player_id: id, player_name: '游客', avatarUrl: '' };
}

export const useFlip7Store = defineStore('flip7', {
  state: () => ({
    rooms: [], creatingRoom: false, connected: false,
    player_id: '', player_name: '', avatarUrl: '', room_id: null,
    room: {}, players: {}, gameStatus: 'waiting', gameState: defaultGameState(),
    roundHistory: [], lastCard: null,
  }),
  actions: {
    initStore() { Object.assign(this, userData()); },
    async createRoom() {
      this.creatingRoom = true;
      try {
        this.initStore();
        const { data } = await axios.get(`${import.meta.env.VITE_URL}/api/new-room-id-short/o4Flip7`);
        this.enterRoom(data.room_id);
        return data.room_id;
      } finally { this.creatingRoom = false; }
    },
    enterRoom(roomId) {
      this.initStore(); this.room_id = roomId;
      connectFlip7Socket(data => this.handleMessage(data), roomId, {
        player_id: this.player_id, player_name: this.player_name, avatarUrl: this.avatarUrl
      });
    },
    async fetchRooms() {
      const { data } = await axios.get(`${import.meta.env.VITE_URL}/api/room-list/o4Flip7`);
      this.rooms = data.rooms || [];
    },
    leaveRoom() {
      closeFlip7Socket(); this.room_id = null; this.room = {}; this.players = {};
      this.gameStatus = 'waiting'; this.gameState = defaultGameState();
      this.roundHistory = []; this.lastCard = null;
    },
    startGame() { sendFlip7Message({ type: 'start_game' }); },
    toggleReady() { sendFlip7Message({ type: 'toggle_ready' }); },
    drawCard() { sendFlip7Message({ type: 'action', action: 'draw' }); },
    stopTurn() { sendFlip7Message({ type: 'action', action: 'stop' }); },
    selectTarget(targetId, cardId = null, ownCardId = null, secondTargetId = null, secondCardId = null) {
      sendFlip7Message({ type: 'action', action: 'select_target', data: {
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
        this.players = data.players || {};
        if (data.rules) this.gameState.rules = data.rules;
        this.gameStatus = data.status === 'playing' ? 'playing' : 'waiting';
      } else if (data.type === 'player_list') {
        this.players = Object.fromEntries((data.players || []).map(p => [p.id, p]));
      } else if (data.type === 'game_state') {
        const oldRound = this.gameState.round;
        this.gameState = { ...defaultGameState(), ...data };
        if (data.players) this.players = data.players;
        this.gameStatus = data.state === 'finished' ? 'finished' : 'playing';
        if (data.round > oldRound) this.roundHistory = [];
      } else if (data.type === 'card_drawn') {
        this.lastCard = data; this.roundHistory.push(data);
      } else if (data.type === 'pending_action') {
        this.gameState.pending_action = data.action;
      } else if (data.type === 'probability_state') {
        this.gameState.probabilities = { ...this.gameState.probabilities, ...(data.probabilities || {}) };
      } else if (data.type === 'rules_updated' || data.type === 'settings_updated') {
        if (data.rules) this.gameState.rules = data.rules;
      } else if (data.type === 'game_finished') {
        this.gameState.state = 'finished'; this.gameStatus = 'finished';
      } else if (data.type === 'error' || data.type === 'rules_error') {
        console.error(data.message || data.msg);
      }
    },
    getPlayerName(id) { return this.players[id]?.name || id; },
    resetStore() { this.leaveRoom(); this.rooms = []; },
  }
});
