import { defineStore } from 'pinia';
import axios from 'axios';
import { useUserStore } from './userStore';
import {
  connectFlip7Socket,
  sendFlip7Message,
  closeFlip7Socket,
} from '../ws/flip7Socket';

const API = import.meta.env.VITE_URL || '';
const emptyGame = () => ({
  state: 'waiting',
  phase: 'waiting',
  players: {},
  scores: {},
  question: null,
  question_index: -1,
  question_count: 0,
  submitted_player_ids: [],
  question_opened_at_ms: 0,
  question_closes_at_ms: 0,
  ranking: [],
  bank_title: '',
});

export const useNewQuizGameStore = defineStore('newQuizGame', {
  state: () => ({
    rooms: [],
    banks: [],
    room_id: null,
    room: {},
    players: {},
    player_id: '',
    player_name: '',
    avatarUrl: '',
    gameState: emptyGame(),
    gameStatus: 'waiting',
    notice: '',
    syncId: null,
    timeOffsetMs: 0,
    latestResult: null,
    answerFeedback: null,
    creatingRoom: false,
  }),
  actions: {
    async initStore() {
      const users = useUserStore();
      if (!users.isLoggedIn || !users.user) await users.checkLoginStatus();
      if (!users.user) throw new Error('请先登录');
      this.player_id = String(users.user.id);
      this.player_name = users.user.username;
      this.avatarUrl = users.user.avatar || '';
    },
    async fetchBanks() {
      await this.initStore();
      const { data } = await axios.get(`${API}/api/new-quiz/banks/available`);
      this.banks = data.banks || [];
    },
    async fetchRooms() {
      await this.initStore();
      const { data } = await axios.get(`${API}/api/room-list/newQuizGame`);
      this.rooms = data.rooms || [];
    },
    async createRoom() {
      this.creatingRoom = true;
      try {
        await this.initStore();
        const { data } = await axios.post(`${API}/api/rooms/newQuizGame`);
        await this.enterRoom(data.room_id);
        return data.room_id;
      } finally {
        this.creatingRoom = false;
      }
    },
    async enterRoom(id) {
      await this.initStore();
      await axios.post(`${API}/api/rooms/newQuizGame/${id}/join`);
      this.room_id = id;
      connectFlip7Socket(
        (data) => this.handleMessage(data),
        id,
        {
          player_id: this.player_id,
          player_name: this.player_name,
          avatarUrl: this.avatarUrl,
        },
        'newQuizGame'
      );
    },
    toggleReady() {
      sendFlip7Message({ type: 'toggle_ready' });
    },
    startGame() {
      sendFlip7Message({ type: 'start_game' });
    },
    updateRules(rules) {
      sendFlip7Message({ type: 'update_settings', settings: { rules } });
    },
    syncTime(attempt = 0) {
      const sent = Date.now();
      const ok = sendFlip7Message({
        type: 'time_sync_request',
        client_request_at_ms: sent,
      });
      if (!ok && attempt < 10)
        setTimeout(() => this.syncTime(attempt + 1), 300);
    },
    submitAnswer(value) {
      if (!this.gameState.question) return;
      const answer = this.gameState.question.type === 'single_choice'
        ? { option_id: value }
        : { text: value };
      sendFlip7Message({
        type: 'action',
        action: 'submit_answer',
        question_id: this.gameState.question.id,
        answer,
        client_submitted_at_ms: Math.round(Date.now() + this.timeOffsetMs),
        sync_id: this.syncId,
      });
    },
    async leaveRoom() {
      const id = this.room_id;
      if (id) {
        try {
          await axios.delete(`${API}/api/rooms/newQuizGame/${id}/membership`);
        } catch (_) {
          /* expired */
        }
      }
      closeFlip7Socket();
      this.room_id = null;
      this.room = {};
      this.players = {};
      this.gameState = emptyGame();
      this.gameStatus = 'waiting';
    },
    handleMessage(data) {
      if (data.type === 'room_state') {
        this.room = data;
        this.players = data.players || {};
        this.gameStatus =
          data.status === 'playing'
            ? 'playing'
            : data.status === 'ended'
              ? 'finished'
              : 'waiting';
        if (data.error || data.extra?.error)
          this.notice = data.error || data.extra.error;
      } else if (data.type === 'game_state') {
        this.gameState = { ...this.gameState, ...data };
        this.players = data.players || this.players;
        this.gameStatus = data.state === 'finished' ? 'finished' : 'playing';
      } else if (data.type === 'time_sync_response') {
        const received = Date.now();
        const average = (Number(data.client_request_at_ms) + received) / 2;
        this.timeOffsetMs = Number(data.server_received_at_ms) - average;
        this.syncId = data.sync_id;
      } else if (data.type === 'question_result') {
        this.latestResult = data;
        this.gameState = {
          ...this.gameState,
          phase: 'result',
          scores: data.scores,
        };
      } else if (data.type === 'answer_feedback') {
        this.answerFeedback = data;
      } else if (data.type === 'answer_received') {
        this.answerFeedback = { ...data, message: data.correct ? '回答正确！' : '答案已提交' };
        this.gameState.submitted_player_ids = [
          ...new Set([
            ...(this.gameState.submitted_player_ids || []),
            this.player_id,
          ]),
        ];
      }
      else if (data.type === 'submission_progress')
        this.gameState = {
          ...this.gameState,
          submitted: data.submitted,
          total: data.total,
        };
      else if (data.type === 'error') this.notice = data.message || data.msg;
    },
  },
});
