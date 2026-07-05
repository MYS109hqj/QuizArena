import { defineStore } from 'pinia';
import { connectTemplateSocket, sendTemplateMessage, closeTemplateSocket } from '../ws/templateSocket';
import { useUserStore } from './userStore';
import axios from 'axios';

function getUserData() {
  const userStore = useUserStore();
  if (userStore.isLoggedIn && userStore.user) {
    return {
      player_id: userStore.user.id || `user-${Date.now()}`,
      player_name: userStore.user.username || '用户',
      avatarUrl: userStore.user.avatar || "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format"
    };
  }
  return {
    player_id: `guest-${Date.now()}`,
    player_name: '游客',
    avatarUrl: "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format"
  };
}

export const useTemplateStore = defineStore('template', {
  state: () => ({
    rooms: [],
    connected: false,
    creatingRoom: false,
    mockEnabled: import.meta.env.VITE_USE_MOCK === 'true',

    player_id: `temp-${Date.now()}`,
    player_name: '加载中...',
    avatarUrl: "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format",

    room_id: null,
    room: {},
    players: {},

    roomCache: {},

    gameStatus: 'waiting',
    gameState: {
      state: "StoreIniting",
      current_player: "StoreIniting",
      round: 999,
      total_rounds: 1,
      total_score: 0,
      target_score: 100,
      player_scores: {}
    },

    debugMode: import.meta.env.VITE_DEBUG_MODE === 'true' || false,
    debugPanelVisible: false,

    achievements: [],
    recentAchievements: []
  }),

  actions: {
    syncUserData() {
      try {
        const playerData = getUserData();
        if (playerData.player_id !== this.player_id ||
          playerData.player_name !== this.player_name ||
          playerData.avatarUrl !== this.avatarUrl) {
          this.player_id = playerData.player_id;
          this.player_name = playerData.player_name;
          this.avatarUrl = playerData.avatarUrl;
          console.log('👤 用户数据已同步:', {
            player_id: this.player_id,
            player_name: this.player_name
          });
        }
      } catch (error) {
        console.error('❌ 同步用户数据失败:', error);
      }
    },

    initStore() {
      this.syncUserData();
    },

    async createRoom() {
      if (this.creatingRoom) return;
      this.creatingRoom = true;

      try {
        this.syncUserData();
        const playerData = getUserData();
        const gameType = 'o999Template';
        
        const response = await axios.get(`${import.meta.env.VITE_URL}/api/new-room-id-short/${gameType}`);
        const roomId = response.data.room_id;
        console.log('🏠 创建房间成功:', roomId);

        connectTemplateSocket((data) => {
          this.handleMessage(data);
        }, roomId, playerData, gameType);

        this.room_id = roomId;
      } catch (error) {
        console.error('❌ 创建房间失败:', error);
      } finally {
        this.creatingRoom = false;
      }
    },

    async enterRoom(roomId) {
      try {
        this.syncUserData();
        const playerData = getUserData();
        const gameType = 'o999Template';

        connectTemplateSocket((data) => {
          this.handleMessage(data);
        }, roomId, playerData, gameType);

        this.room_id = roomId;
      } catch (error) {
        console.error('❌ 加入房间失败:', error);
      }
    },

    async fetchRooms() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_URL}/api/room-list/o999Template`);
        this.rooms = response.data.rooms || [];
      } catch (error) {
        console.error('❌ 获取房间列表失败:', error);
      }
    },

    async leaveRoom() {
      try {
        closeTemplateSocket();
        this.room_id = null;
        this.room = {};
        this.players = {};
        this.gameStatus = 'waiting';
      } catch (error) {
        console.error('❌ 离开房间失败:', error);
      }
    },
    // 注：再来一局不能用startGame，理论上是重新创建房间
    async startGame() {
      try {
        sendTemplateMessage({
          type: 'start_game'
        });
      } catch (error) {
        console.error('❌ 开始游戏失败:', error);
      }
    },

    async toggleReady() {
      try {
        sendTemplateMessage({
          type: 'toggle_ready'
        });
      } catch (error) {
        console.error('❌ 准备状态切换失败:', error);
      }
    },

    incrementScore() {
      if (this.gameState.state !== 'player_turn' ||
        this.gameState.current_player !== this.player_id) {
        return;
      }

      sendTemplateMessage({
        type: 'action',
        action: 'increment'
      });
    },

    handleMessage(data) {
      switch (data.type) {
        case 'game_state':
          this.handleGameState(data);
          break;
        case 'room_state':
          this.handleRoomState(data);
          break;
        case 'player_list':
          this.handlePlayerList(data);
          break;
        case 'error':
          console.error('❌ 游戏错误:', data.msg);
          break;
        default:
          console.log('📩 未知消息类型:', data);
      }
    },

    handleRoomState(data) {
      this.room = {
        room_id: data.room_id,
        name: data.name,
        owner: data.owner,
        status: data.status,
        config: {
          max_players: data.max_players || 2,
          min_players: data.min_players || 1
        },
        player_count: data.player_count || 0
      };
      this.players = data.players || {};
      this.gameStatus = data.status === 'playing' ? 'playing' : 'waiting';
      console.log('🏠 房间状态更新:', this.room);
    },

    handleGameState(data) {
      this.gameState = {
        state: data.state,
        current_player: data.current_player,
        round: data.round,
        total_rounds: data.total_rounds,
        total_score: data.total_score || 0,
        target_score: data.target_score || 100,
        player_scores: data.player_scores || {}
      };

      if (data.state === 'playing' || data.state === 'player_turn') {
        this.gameStatus = 'playing';
      } else if (data.state === 'finished') {
        this.gameStatus = 'finished';
      }

      console.log('🎮 游戏状态更新:', this.gameState);
    },

    handlePlayerList(data) {
      const players = {};
      data.players.forEach(p => {
        players[p.id] = p;
      });
      this.players = players;
      console.log('👥 玩家列表更新:', this.players);
    },

    resetStore() {
      this.rooms = [];
      this.connected = false;
      this.room_id = null;
      this.room = {};
      this.players = {};
      this.gameStatus = 'waiting';
      this.gameState = {
        state: "StoreIniting",
        current_player: "StoreIniting",
        round: 999,
        total_rounds: 1,
        total_score: 0,
        target_score: 100,
        player_scores: {}
      };
    }
  }
});
