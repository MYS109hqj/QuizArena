import { defineStore } from 'pinia';
import { connectSPHSocket, sendSPHMessage, closeSPHSocket } from '../ws/samePatternSocket';
import { useUserStore } from './userStore';
import axios from 'axios';
import { inject } from 'vue';

// 从userStore获取用户信息
function getUserData() {
  const userStore = useUserStore();
  if (userStore.isLoggedIn && userStore.user) {
    return {
      player_id: userStore.user.id || `user-${Date.now()}`,
      player_name: userStore.user.username || '用户',
      avatarUrl: userStore.user.avatar || "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format"
    };
  }
  
  // 如果用户未登录，返回默认数据
  return {
    player_id: `guest-${Date.now()}`,
    player_name: '游客',
    avatarUrl: "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format"
  };
}

const initializeCards = () => {
  const letters = 'ABCDEFGHIJKLMNOP'.split('');
  return letters.map((letter, index) => ({
    cardId: `A${index+1}`,
    letter,        // 正面字母
    patternId: null // 背面图案，初始为空，点击后由后端返回
  }));
};

// Mock 房间数据
const createMockRooms = () => [
  {
    id: 'room-001',
    owner: 'Alice',
    players: ['Alice'],
    maxPlayers: 6,
    status: 'waiting',
  },
  {
    id: 'room-002',
    owner: 'Bob',
    players: ['Bob', 'Charlie'],
    maxPlayers: 4,
    status: 'playing',
  },
];

export const useSamePatternHuntStore = defineStore('samePatternHunt', {
  state: () => {
    // 初始化时使用临时默认值，避免依赖userStore立即加载完成
    return {
      rooms: [],
      connected: false,
      creatingRoom: false,
      mockEnabled: import.meta.env.VITE_USE_MOCK === 'true',

      // 临时默认值，将在初始化后通过syncUserData更新
      player_id: `temp-${Date.now()}`,
      player_name: '加载中...',
      avatarUrl: "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format",

      // 其他状态
      room_id: null,
      room: {},
      players: {},
      
      // 房间缓存，用于预加载优化
      roomCache: {},
      
      gameStatus: 'waiting',
      gameState: {
        state: "StoreIniting", 
        current_player: "StoreIniting",
        gameInfo: {},
        round: 999,
      },
      cards: initializeCards(),
      flippedCards: [],     // 当前已翻面的卡片 ID
      matchedCards: [],     // 已匹配成功的卡片 ID
      unmatchedCards: [],   // 临时不匹配的卡片 ID（用于动画）
      
      // 规则配置
      gameRules: {
        // 现有特殊规则（保持原样）
        allowSimultaneousActions: true,
        
        // 新增规则选项
        flipRestrictions: {
          preventFlipDuringAnimation: false, // 牌未翻回限制
          waitForOthersToFlipBack: false,    // 等待他人翻回限制
          actionLockEnabled: true            // 行动锁定限制（现有）
        },
        
        // 规则参数配置
        animationDuration: 5000,      // 翻牌动画时长
        maxConcurrentFlips: 1,        // 最大同时翻牌数
        turnTransitionDelay: 1000     // 回合转换延迟
      },
      
      // 终局状态数据
      finalState: null,
      
      // 调试模式状态
      debugMode: import.meta.env.VITE_DEBUG_MODE === 'true' || false,
      debugPanelVisible: false,
      
      // 成就系统相关状态
      achievements: [], // 所有已解锁的成就
      recentAchievements: [] // 最近解锁的成就，用于显示通知
    };
  },

  actions: {
      // 同步用户数据从userStore
      syncUserData() {
        try {
          // 不需要传入userStore参数，getUserData内部会自己获取
          const playerData = getUserData();
          
          // 只有当用户数据有变化时才更新
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
          // 保持现有数据
        }
      },
      
      // 初始化store，包括用户数据同步
      initStore() {
        // 同步用户数据
        this.syncUserData();
      
      // 设置监听，在userStore数据变化时自动同步
      const userStore = useUserStore();
      if (userStore && userStore.$subscribe) {
        userStore.$subscribe(() => {
          this.syncUserData();
        });
      }
      
      // 初始化调试模式
      this.initDebugMode();
    },
    
    // 初始化调试模式
    initDebugMode() {
      // 检查URL参数和localStorage中的调试模式设置
      const urlParams = new URLSearchParams(window.location.search);
      const debugFromURL = urlParams.get('debug') === 'true';
      const debugFromStorage = localStorage.getItem('DEBUG_MODE') === 'true';
      
      this.debugMode = debugFromURL || debugFromStorage;
      
      if (this.debugMode) {
        console.log('🔧 调试模式已启用');
        this.addDebugLog('调试模式已启用');
      }
    },
    
    // 从userStore同步用户信息
    syncUserData() {
      const userStore = useUserStore();
      if (userStore.isLoggedIn && userStore.user) {
        this.player_id = userStore.user.id || this.player_id;
        this.player_name = userStore.user.username || this.player_name;
        this.avatarUrl = userStore.user.avatar || this.avatarUrl;
      }
    },
    
    // 设置玩家信息（现在直接使用userStore的数据）
    setPlayerProfile(name, avatar) {
      const userStore = useUserStore();
      if (userStore.isLoggedIn) {
        // 更新userStore中的用户信息
        userStore.updateProfile({ username: name, avatar: avatar });
        // 同步到当前store
        this.syncUserData();
      } else {
        // 如果用户未登录，只更新本地状态
        this.player_name = name || this.player_name;
        this.avatarUrl = avatar || this.avatarUrl;
      }
    },
    async joinRoom(roomId) {
      if (!roomId) return;

      console.log(`🚀 开始加入房间流程: ${roomId}`);
      const joinStartTime = Date.now();

      this.room_id = null; // 重置当前房间
      this.room = {};
      this.players = [];
      this.gameStatus = 'waiting';

      // 检查是否有缓存数据，如果有则先显示缓存信息
      if (this.roomCache && this.roomCache[roomId]) {
        console.log(`📦 使用缓存房间信息: ${roomId}`);
        const cachedRoom = this.roomCache[roomId];
        this.room = {
          room_id: cachedRoom.room_id,
          name: cachedRoom.name,
          owner: { name: cachedRoom.owner },
          config: { max_players: cachedRoom.max_players }
        };
        console.log(`✅ 缓存信息加载完成`);
      }

      if (this.mockEnabled) {
        // 模拟加入房间
        const mockRooms = createMockRooms();
        const targetRoom = mockRooms.find(r => r.id === roomId);
        if (targetRoom) {
          this.room_id = roomId;
          this.room = { ...targetRoom };
          this.players = [...targetRoom.players];
          this.gameStatus = targetRoom.status;
          console.log(`✅ 模拟加入房间完成，耗时: ${Date.now() - joinStartTime}ms`);
        }
      } else {
        try {
          // 获取玩家信息
          const player_info = {
            type: 'player_info',
            id: this.player_id,
            name: this.player_name,
            avatar: this.avatarUrl
          };

          console.log(`⏱️ 开始建立WebSocket连接...`);
          const connectStartTime = Date.now();

          // 检查是否有保存的连接信息（可能是刷新页面后留下的）
          const savedConnection = localStorage.getItem('SPH_LAST_CONNECTION');
          if (savedConnection) {
            try {
              const connectionInfo = JSON.parse(savedConnection);
              // 只有当保存的连接信息匹配当前房间时才使用它
              if (connectionInfo.roomId === roomId) {
                console.log('🔄 发现匹配的保存连接，尝试直接恢复');
              }
            } catch (e) {
              console.warn('Failed to parse saved connection:', e);
              localStorage.removeItem('SPH_LAST_CONNECTION');
            }
          }

          // 建立该房间的 WebSocket 连接，并传入回调处理消息
          connectSPHSocket((data) => {
            this.handleMessage(data); // 所有消息统一由 store 处理
          }, roomId, player_info);

          this.room_id = roomId; // 设置 room_id，触发 watch 跳转
          console.log(`✅ WebSocket连接建立完成，耗时: ${Date.now() - connectStartTime}ms`);
          console.log(`✅ 加入房间流程完成，总耗时: ${Date.now() - joinStartTime}ms`);
        } catch (error) {
          console.error('❌ 加入房间失败:', error);
          console.error(`⏱️ 加入房间失败，总耗时: ${Date.now() - joinStartTime}ms`);
          // 可以添加错误提示
          alert(`加入房间失败: ${error.message}`);
        }
      }
    },

    connect(userData) {
      console.log('连接中...', userData);
      this.connected = true;

      if (this.mockEnabled) {
        // 模拟延迟加载房间列表
        setTimeout(() => {
          this.rooms = createMockRooms();
        }, 800);
      } else {
        // TODO: 真实 WebSocket 连接逻辑
        this.connectSPHSocket(userData);
      }
    },

    async send(message) {
        if (this.mockEnabled) {
            if (message.type === 'get_room_list') {
            this.rooms = createMockRooms(); // 重新加载
            }
            if (message.type === 'create_room') {
            // 从后端获取房间 ID
                const gameType = 'o2SPH';
                axios.get(`${import.meta.env.VITE_URL}/api/new-room-id-short/${gameType}`)
                .then(response => {
                    const newRoom = {
                    id: response.data.room_id,
                    owner: 'You',
                    players: ['You'],

                    status: 'waiting',
                    };
                    this.rooms.unshift(newRoom); // 添加到顶部
                });
              }
        }
          else {
                // 发送到真实 WebSocket
                if (message.type === 'create_room') {
                    this.creatingRoom = true; 
                    try {
                        // 从后端获取房间 ID
                        const gameType = 'o2SPH';
                        const response = await axios.get(`${import.meta.env.VITE_URL}/api/new-room-id-short/${gameType}`);
                        this.room_id = response.data.room_id;
                        const player_info = {"type": "player_info", "id": this.player_id, "name": this.player_name, "avatar": this.avatarUrl}
                        connectSPHSocket((data) => {
                            this.handleMessage(data);
                        }, this.room_id, player_info);

                    }catch (error) {
                        console.error('创建房间失败:', error);
                    } finally {
                        this.creatingRoom = false;  
                    }
                }
                else if (message.type === 'get_room_list') {
                  try {
                    const response = await axios.get(`${import.meta.env.VITE_URL}/api/room-list/o2SPH`);
                    this.rooms = response.data.rooms;
                  }catch (error) {
                        console.error('获取房间列表失败:', error);
                  }
                }else{
                  console.log("尝试发送消息：",message)
                  sendSPHMessage(message);
                  console.log("发送成功")
                }
            
        }
    },
    handleMessage(data) {
        console.log('📨 收到消息:', data);
        const receiveTime = Date.now();
        
        switch (data.type) {
        case 'room_state':
          console.log(`⏱️ 房间状态消息处理开始: ${receiveTime}`);
          this.room = {
            "room_id": data.room_id, 
            "owner": data.owner, 
            "config": {
              "max_players": data.max_players, 
              "min_players": data.min_players
            }
          };
          this.players = data.players || [];
          this.gameStatus = data.status || 'waiting';
          if (data.room_id) {
            this.room_id = data.room_id;
          }
          console.log(`✅ 房间状态更新完成，耗时: ${Date.now() - receiveTime}ms`);
          console.log(`📊 房间配置更新: min_players=${data.min_players}, max_players=${data.max_players}`);
          break;
        case 'game_state':
          this.gameState = {
            state: data.state, 
            current_player: data.current_player,
            gameInfo: data.gameInfo ,
            round: data.round
          };

          // // 🔔 可选：触发一些副作用（比如声音提示）
          // if (data.current_player === this.player_id) {
          //   console.log("轮到你了！");
          //   // 可播放音效或 UI 动画
          // }

          break;
        case 'card_flipped':
          this.handleCardFlipped(data.result);
        break;
        case 'target_sequence':
          // 预留逻辑
          break;
        case 'rules_updated':
          this.handleRulesUpdate(data.rules);
          break;
        case 'cards_sync':
          this.handleCardsSync(data.cards);
          break;
        case 'flip_status_sync':
          this.handleFlipStatusSync(data.flip_status);
          break;
        case 'player_sync':
          this.handlePlayerSync(data);
          break;
        case 'final_state':
          console.log('📥 收到final_state消息:', data);
          this.handleFinalState(data);
          break;
        case 'achievement_unlocked':
          console.log('🏆 收到成就解锁消息:', data);
          this.handleAchievementUnlocked(data.achievement);
          break;
        default:
          console.warn('Unknown message type:', data.type);
        }
    },
    handleCardFlipped(result) {
      const { cardId, matched, patternId, flipBack = 1500 } = result;

      // cards 现在是数组格式，直接通过索引查找
      const cardIndex = this.cards.findIndex(c => c.cardId === cardId);
      if (cardIndex === -1) {console.warn(`Card with id ${cardId} not found`);return;}

      this.cards[cardIndex].patternId = patternId;
      // 翻面卡牌
      if (!this.flippedCards.includes(cardId)) {
        this.flippedCards.push(cardId);
      }
      // 确定要触发的样式
      if (matched) {
        if (!this.matchedCards.includes(cardId)) {
          this.matchedCards.push(cardId);
        }
      } else {
        if (!this.unmatchedCards.includes(cardId)) {
          this.unmatchedCards.push(cardId);
        }
      }
      // 延迟将牌翻回+清除样式
      setTimeout(() => {
        this.flippedCards = this.flippedCards.filter(id => id !== cardId);
        this.matchedCards = this.matchedCards.filter(id => id !== cardId);
        this.unmatchedCards = this.unmatchedCards.filter(id => id !== cardId);

        const cardIndex = this.cards.findIndex(c => c.cardId === cardId);
        if (cardIndex !== -1) {
          this.cards[cardIndex].patternId = null;
        }
      }, flipBack);
    },
    // 处理成就解锁消息
    handleAchievementUnlocked(achievementData) {
      // 确保成就数据格式正确
      const achievement = {
        id: achievementData.id || `achievement-${Date.now()}`,
        name: achievementData.name || '未知成就',
        description: achievementData.description || '',
        icon: achievementData.icon || '🏆'
      };
      
      // 检查是否已经有这个成就
      const existingIndex = this.achievements.findIndex(a => a.id === achievement.id);
      
      // 如果没有，则添加到总成就列表
      if (existingIndex === -1) {
        this.achievements.push(achievement);
        console.log('✅ 新成就添加到总列表:', achievement.name);
      }
      
      // 检查是否已经在最近成就列表中
      const recentIndex = this.recentAchievements.findIndex(a => a.id === achievement.id);
      
      // 如果不在最近成就列表中，则添加
      if (recentIndex === -1) {
        this.recentAchievements.push(achievement);
        console.log('✨ 显示成就解锁通知:', achievement.name);
        
        // 可选：播放成就解锁音效
        // this.playAchievementSound();
        
        // 30秒后自动清除此成就通知
        setTimeout(() => {
          this.dismissAchievement(achievement.id);
        }, 120000);
      }
    },
    
    // 关闭单个成就通知
    dismissAchievement(achievementId) {
      const index = this.recentAchievements.findIndex(a => a.id === achievementId);
      if (index !== -1) {
        this.recentAchievements.splice(index, 1);
        console.log(`📌 成就通知已关闭: ${achievementId}`);
      }
    },
    
    // 清除所有最近的成就通知
    clearRecentAchievements() {
      this.recentAchievements = [];
      console.log('🧹 所有成就通知已清除');
    },
    
    // 可选：播放成就解锁音效
    playAchievementSound() {
      try {
        // 这里可以实现音效播放逻辑
        // const audio = new Audio('/sounds/achievement-unlock.mp3');
        // audio.play();
      } catch (error) {
        console.warn('🔊 无法播放成就音效:', error);
      }
    },
    
    disconnect() {
      closeSPHSocket();
      this.$reset();
      this.syncUserData(); // 重新从userStore同步数据
    },

    // 更新规则配置
    updateGameRules(newRules) {
      this.gameRules = { ...this.gameRules, ...newRules };
      
      // 发送规则更新到后端
      if (!this.mockEnabled) {
        sendSPHMessage({
          type: 'update_rules',
          rules: this.gameRules
        });
      }
    },

    // 处理从后端接收的规则更新
    handleRulesUpdate(rules) {
      this.gameRules = { ...this.gameRules, ...rules };
    },

    // 处理卡牌状态同步（重连时）
    handleCardsSync(cards) {
      // 将对象格式的cards转换为数组格式
      this.cards = Object.values(cards);
      console.log('Cards state synchronized:', this.cards.length, 'cards');
    },

    // 处理翻转状态同步（重连时）
    handleFlipStatusSync(flipStatus) {
      // 清空当前翻转状态
      this.flippedCards = [];
      this.matchedCards = [];
      this.unmatchedCards = [];

      // 根据同步的状态重新设置卡牌状态
      for (const [cardId, status] of Object.entries(flipStatus)) {
        if (status.flipping) {
          // 卡牌正在翻转中，重新创建翻转动画
          this.flippedCards.push(cardId);
          
          // 如果剩余时间大于0，设置定时器自动翻回
          if (status.remaining_time > 0) {
            setTimeout(() => {
              this.flippedCards = this.flippedCards.filter(id => id !== cardId);
            }, status.remaining_time);
          }
        }
      }
      console.log('Flip status synchronized:', Object.keys(flipStatus).length, 'cards');
    },

    // 处理玩家状态同步（重连时）
    handlePlayerSync(playerData) {
      if (playerData.targets) {
        this.targetSequence = playerData.targets;
      }
      if (playerData.current_index !== undefined) {
        this.currentTargetIndex = playerData.current_index;
      }
      if (playerData.score !== undefined) {
        this.score = playerData.score;
      }
      console.log('Player state synchronized:', playerData);
    },

    // 处理终局状态数据
    handleFinalState(data) {
      console.log('📊 收到终局状态数据:', data);
      this.finalState = data;
      
      // 更新卡牌状态为终局状态（显示图案面）
      if (data.cards) {
        this.cards = Object.values(data.cards).map(card => ({
          cardId: card.cardId,
          letter: card.cardId.replace('A', ''), // 从cardId提取字母
          patternId: card.patternId,
          isFinalState: true // 标记为终局状态
        }));
        console.log('🃏 更新后的cards:', this.cards);
      }
      
      // 触发终局页面显示 - 通过更新finalState触发watch监听
      console.log('🚀 终局状态已更新，等待GamePage监听');
    },

    // 调试相关方法
    toggleDebugPanel() {
      if (this.debugMode) {
        this.debugPanelVisible = !this.debugPanelVisible;
        console.log(`🔧 调试面板 ${this.debugPanelVisible ? '显示' : '隐藏'}`);
      }
    },

    async debugSetScore(playerId, score) {
      if (!this.debugMode) {
        console.warn('调试模式未启用，无法设置分数');
        return { success: false, error: '调试模式未启用' };
      }

      try {
        const response = await axios.post(`${import.meta.env.VITE_URL}/api/debug/set-score/o2SPH/${this.room_id}`, {
          player_id: playerId,
          score: parseInt(score)
        });
        console.log('🔧 调试设置分数成功:', response.data);
        return response.data;
      } catch (error) {
        console.error('🔧 调试设置分数失败:', error);
        return { success: false, error: error.message };
      }
    },

    async debugEndGame() {
      if (!this.debugMode) {
        console.warn('调试模式未启用，无法结束游戏');
        return { success: false, error: '调试模式未启用' };
      }

      try {
        const response = await axios.post(`${import.meta.env.VITE_URL}/api/debug/end-game/o2SPH/${this.room_id}`);
        console.log('🔧 调试结束游戏成功:', response.data);
        return response.data;
      } catch (error) {
        console.error('🔧 调试结束游戏失败:', error);
        return { success: false, error: error.message };
      }
    },

    async debugResetGame() {
      if (!this.debugMode) {
        console.warn('调试模式未启用，无法重置游戏');
        return { success: false, error: '调试模式未启用' };
      }

      try {
        const response = await axios.post(`${import.meta.env.VITE_URL}/api/debug/reset-game/o2SPH/${this.room_id}`);
        console.log('🔧 调试重置游戏成功:', response.data);
        return response.data;
      } catch (error) {
        console.error('🔧 调试重置游戏失败:', error);
        return { success: false, error: error.message };
      }
    },

    async debugGetGameState() {
      if (!this.debugMode) {
        console.warn('调试模式未启用，无法获取游戏状态');
        return { success: false, error: '调试模式未启用' };
      }

      try {
        const response = await axios.get(`${import.meta.env.VITE_URL}/api/debug/game-state/o2SPH/${this.room_id}`);
        console.log('🔧 调试获取游戏状态成功:', response.data);
        return response.data;
      } catch (error) {
        console.error('🔧 调试获取游戏状态失败:', error);
        return { success: false, error: error.message };
      }
    }


  },
});