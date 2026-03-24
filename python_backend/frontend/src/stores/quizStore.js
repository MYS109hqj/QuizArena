import { defineStore } from 'pinia';
import { connectQuizSocket, sendQuizMessage, closeQuizSocket } from '../ws/quizSocket';

export const useQuizStore = defineStore('quiz', {
  state: () => ({
    roomId: null,
    playerInfo: {},
    question: null,
    answers: [],
    onlinePlayers: [],
    currentMode: 'none',
    currentRound: 1,
    totalRounds: 1,
    exposeAnswer: false,
    finalResults: null,
    isConnected: false,
    // 其它状态...
  }),
  actions: {
    init(roomId, playerInfo) {
      this.roomId = roomId;
      this.playerInfo = playerInfo;
      connectQuizSocket(roomId, this.handleSocketMessage);
    },
    handleSocketMessage(data) {
      // 公共消息处理
      if (data.type === 'question') {
        this.question = data.content;
      } else if (data.type === 'answer') {
        this.answers.push(data);
      } else if (data.type === 'player_list') {
        this.onlinePlayers = data.players;
      } else if (data.type === 'mode_change') {
        this.currentMode = data.currentMode;
      } else if (data.type === 'round') {
        this.currentRound = data.currentRound;
        this.totalRounds = data.totalRounds;
      } else if (data.type === 'congratulations_complete') {
        this.finalResults = data.results;
      }
      // ...其它类型
    },
    sendMessage(msg) {
      sendQuizMessage(msg);
    },
    close() {
      closeQuizSocket();
      this.$reset();
    }
  }
});