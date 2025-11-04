<template>
  <div class="game-bg">
    <!-- 重连状态提示 -->
    <div v-if="isReconnecting" class="reconnect-overlay">
      <div class="reconnect-modal">
        <div class="reconnect-spinner"></div>
        <p>{{ reconnectStatus }}</p>
      </div>
    </div>

    <!-- 规则设置模态框 -->
    <div v-if="showRulesModal" class="modal-overlay" @click.self="showRulesModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>游戏规则设置</h3>
          <button class="close-btn" @click="showRulesModal = false">×</button>
        </div>
        <RulesSettings />
      </div>
    </div>

    <!-- 终局页面 -->
    <div v-if="showFinalState" class="final-state-overlay">
      <div class="final-state-modal">
        <div class="final-state-header">
          <h2>终局页面</h2>
          <button class="close-btn" @click="closeFinalState">×</button>
        </div>
        <div class="final-state-content">
          <div class="final-patterns-section">
            <h3 class="section-title">终局图案</h3>
            <div class="final-cards-grid">
              <div v-for="card in finalCards" :key="card.cardId" class="final-card">
                <img 
                  :src="getPatternImage(card.patternId)" 
                  :alt="'图案 ' + card.patternId" 
                  class="pattern-img"
                />
              </div>
            </div>
          </div>
          <div class="final-scores">
            <h3 class="section-title">最终得分</h3>
            <div class="score-list">
              <div v-for="player in rankedPlayers" :key="player.id" class="score-item">
                <span class="player-name">{{ player.name }}</span>
                <span class="player-score">{{ player.score }}分</span>
              </div>
            </div>
          </div>
        </div>
        <div class="final-state-actions">
          <button @click="closeFinalState" class="green-btn">关闭</button>
        </div>
      </div>
    </div>

    <GameHeader class="game-header" @exit="handleExit" @showRules="showRulesModal = true" />

    <!-- 桌面宽屏时的侧边栏 -->
    <div class="player-sidebar">
      <div class="sidebar-header">
        <h3>玩家状态</h3>
      </div>
      <PlayerStatus orientation="vertical" />
    </div>

    <!-- 主内容区 -->
    <div class="game-main">
      <!-- 移动端时的顶部状态栏 -->
      <div class="player-status-container">
        <PlayerStatus orientation="horizontal" />
      </div>

      <TargetDisplay />
      <CardsGrid :cards="store.cards" :flipped-cards="store.flippedCards" :matched-cards="store.matchedCards"
        :unmatched-cards="store.unmatchedCards" :is-locked="isLocked" />
    </div>

    <!-- 目标栏侧边栏 - 宽屏时显示 -->
    <div class="target-sidebar">
      <TargetDisplay />
    </div>

    <GameOverModal :show="isGameFinished" :ranked-players="rankedPlayers" @leave="leaveGame" @playAgain="playAgain" @viewFinalState="showFinalState = true" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import { hasPendingConnection, restoreConnection, connectSPHSocket, isWebSocketActive, setRouteChanging } from '@/ws/samePatternSocket';
import axios from 'axios';
import GameHeader from '@/components/GameHeader.vue';
import PlayerStatus from '@/components/PlayerStatus.vue';
import TargetDisplay from '@/components/TargetDisplay.vue';
import CardsGrid from '@/components/CardsGrid.vue';
import GameOverModal from '@/components/GameOverModal.vue';
import RulesSettings from '@/components/RulesSettings.vue';

// 图片路径工具
const getPatternImage = (patternId) => {
  if (!patternId) {
    return new URL('/assets/placeholder.svg', import.meta.url).href;
  }
  return new URL(`/assets/patterns/${patternId}.svg`, import.meta.url).href;
};

const store = useSamePatternHuntStore();
const router = useRouter();
const route = useRoute();

// 重连状态
const isReconnecting = ref(false);
const reconnectStatus = ref('');

// 规则设置模态框状态
const showRulesModal = ref(false);

// 终局页面状态
const showFinalState = ref(false);
const finalCards = ref([]);

// 本地状态（仅保留 UI 控制）
const isLocked = computed(() => {
  // 如果你后端没有 locked 字段，可以基于 gameState.state 判断
  return store.gameState?.state === 'locked' || false;
});

// 计算属性
const isGameFinished = computed(() => store.gameState?.state === 'finished');

const rankedPlayers = computed(() => {
  if (!store.gameState?.gameInfo) return [];

  return Object.entries(store.gameState.gameInfo)
    .map(([id, info]) => ({
      id,
      name: store.players[id]?.name || '未知',
      score: info.score
    }))
    .sort((a, b) => b.score - a.score);
});

// 方法
const leaveGame = () => {
  store.send({ type: 'leave_room', roomId: store.room?.room_id });
  router.push({ name: 'SPHLobby' });
};

const playAgain = async () => {
  try {
    // 发送重置游戏请求，将房间状态转为waiting
    store.send({ type: 'reset_game', roomId: store.room?.room_id });

    // 等待游戏重置完成
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 跳转到房间页面
    router.push({
      name: 'SPHRoom',
      params: { roomId: store.room?.room_id }
    });
  } catch (error) {
    console.error('再来一局失败:', error);
    alert('再来一局失败，请返回大厅重新创建房间');
    router.push({ name: 'SPHLobby' });
  }
};

const handleExit = () => {
  router.push({ name: 'SPHLobby' });
};

const closeFinalState = () => {
  showFinalState.value = false;
};




// 检查并处理重连
onMounted(async () => {
  const roomId = route.params.roomId;

  // 清除路由切换标记（页面加载完成）
  setTimeout(() => {
    setRouteChanging(false);
    sessionStorage.removeItem('SPH_ROUTE_CHANGING');
  }, 1000);

  // 监听终局状态事件
  const handleFinalState = (data) => {
    console.log('🎯 收到终局状态事件:', data);
    console.log('store.cards:', store.cards);
    
    // 确保使用store中已经更新好的cards数据
    if (store.cards && store.cards.length > 0) {
      finalCards.value = store.cards.map(card => ({
        cardId: card.cardId,
        patternId: card.patternId
      }));
      console.log('终局卡牌数据:', finalCards.value);
      showFinalState.value = true;
    } else {
      console.error('store.cards为空或未定义');
    }
  };

  // 监听store的finalState变化
  watch(() => store.finalState, (newValue) => {
    if (newValue && newValue.cards) {
      console.log('🔍 检测到finalState变化:', newValue);
      handleFinalState(newValue);
    }
  }, { deep: true });

  // 检查连接状态
  if (isWebSocketActive()) {
    // 连接活跃，直接使用现有连接
    console.log('使用现有WebSocket连接，不触发重连');
    // 获取当前游戏状态
    setTimeout(() => {
      store.send({ type: 'get_game_state' });
    }, 500);
  } else if (hasPendingConnection()) {
    // 异常断开，需要重连
    isReconnecting.value = true;
    reconnectStatus.value = '正在尝试重新连接...';

    try {
      // 先检查房间状态
      const roomExists = await checkRoomExists(roomId);

      if (roomExists) {
        // 房间存在，尝试恢复连接
        const success = await new Promise((resolve) => {
          setTimeout(() => {
            const restored = restoreConnection(store.handleMessage);
            resolve(restored);
          }, 1000);
        });

        if (success) {
          reconnectStatus.value = '连接恢复成功！';
          setTimeout(() => {
            isReconnecting.value = false;
            reconnectStatus.value = '';
            // 获取游戏状态
            store.send({ type: 'get_game_state' });
          }, 2000);
        } else {
          reconnectStatus.value = '重连失败，正在加入新会话...';
          await joinNewSession(roomId);
        }
      } else {
        // 房间已被销毁，创建新房间
        reconnectStatus.value = '原房间已不存在，正在创建新房间...';
        await createNewRoom();
      }
    } catch (error) {
      console.error('重连过程中出错:', error);
      reconnectStatus.value = '重连失败，正在创建新房间...';
      await createNewRoom();
    }
  } else {
    // 全新连接或路由切换后的正常连接
    console.log('建立新连接或路由切换后的连接');
    await joinNewSession(roomId);
  }
});

// 检查房间是否存在
const checkRoomExists = async (roomId) => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_URL}/api/room-exists/o2SPH/${roomId}`);
    return response.data.exists;
  } catch (error) {
    console.error('检查房间状态失败:', error);
    return false;
  }
};

// 创建新房间
const createNewRoom = async () => {
  try {
    // 从后端获取新的房间ID
    const response = await axios.get(`${import.meta.env.VITE_URL}/api/new-room-id-short/o2SPH`);
    const newRoomId = response.data.room_id;

    // 重定向到新房间
    router.replace({ name: 'SPHGame', params: { roomId: newRoomId } });

    // 加入新房间
    await joinNewSession(newRoomId);

    reconnectStatus.value = '已创建新房间';
    setTimeout(() => {
      isReconnecting.value = false;
      reconnectStatus.value = '';
    }, 2000);
  } catch (error) {
    console.error('创建新房间失败:', error);
    reconnectStatus.value = '创建房间失败，请返回大厅重试';
  }
};

// 加入新会话
const joinNewSession = async (roomId) => {
  try {
    const player_info = {
      type: 'player_info',
      id: store.player_id,
      name: store.player_name,
      avatar: store.avatarUrl
    };

    // 清除旧的连接信息
    localStorage.removeItem('SPH_LAST_CONNECTION');

    // 建立新的WebSocket连接
    connectSPHSocket(store.handleMessage, roomId, player_info);

    setTimeout(() => {
      isReconnecting.value = false;
      reconnectStatus.value = '';
    }, 1000);
  } catch (error) {
    console.error('加入新会话失败:', error);
    reconnectStatus.value = '加入房间失败';
    localStorage.removeItem('SPH_LAST_CONNECTION');
  }
};

onUnmounted(() => {
  console.log("GamePage的onUnmounted激活，断开websocket连接")
  store.disconnect();
});
</script>
<style scoped>
.game-bg {
  background: #e6ffe6;
  height: 100vh;
  padding: 12px;
  box-sizing: border-box;
  display: grid;
  grid-template-rows: auto 1fr;
  grid-template-columns: 1fr;
  gap: 12px;
  overflow: hidden;
}

.game-header {
  grid-column: 1 / -1;
}

.player-sidebar {
  display: none;
  position: fixed;
  right: 20px;
  top: 100px;
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  z-index: 1001;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
}

.sidebar-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e1e5e9;
}

.sidebar-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.game-main {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  /* 允许垂直滚动 */
  justify-content: flex-start;
  /* 从顶部开始排列 */
  align-items: center;
  /* 水平居中内容 */
  padding: 20px 0;
  /* 添加上下内边距 */
}

.player-status-container {
  display: none;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

.target-sidebar {
  display: none;
}

/* 终局页面样式 */
.final-state-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1003;
  padding: 20px;
}

.final-state-modal {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.final-state-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.final-state-header h2 {
  margin: 0;
  color: #2c3e50;
}

.final-state-content {
  padding: 20px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
}

.final-patterns-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.section-title {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
}

.final-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(4, 1fr);
  gap: 8px;
  width: 100%;
  height: 400px;
  max-height: 400px;
}

.final-card {
  background: white;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 4px;
  text-align: center;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.final-card:hover {
  border-color: #3498db;
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.2);
  transform: translateY(-2px);
}

.pattern-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.final-scores {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.final-scores h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.player-name {
  font-weight: 600;
  color: #2c3e50;
}

.player-score {
  color: #27ae60;
  font-weight: bold;
}

.final-state-actions {
  padding: 20px;
  border-top: 1px solid #eee;
  text-align: center;
}

/* 宽屏布局 - 宽高比大于1.5且宽度大于1024px时显示侧边栏和目标栏 */
@media (min-aspect-ratio: 3/2) and (min-width: 1024px) {
  .game-bg {
    grid-template-columns: 280px 1fr 280px;
    gap: 12px;
  }

  .player-sidebar {
    display: block;
    position: static;
    grid-column: 3;
    grid-row: 2;
    width: 100%;
    max-height: none;
  }

  .target-sidebar {
    display: flex;
    align-items: center;
    justify-content: center;
    position: static;
    grid-column: 1;
    grid-row: 2;
    width: 240px;
    /* 缩小宽度 */
    max-height: none;
    padding: 0;
  }

  .target-sidebar .target-display {
    margin: 0;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 16px;
    width: 100%;
  }

  .target-sidebar .target-display h3 {
    color: #2c3e50;
    font-size: 16px;
    margin-bottom: 12px;
    text-align: center;
  }

  .target-sidebar .target-pattern {
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }

  .target-sidebar .target-img {
    width: 60px;
    height: 60px;
    border-color: #27ae60;
  }

  .target-sidebar .target-id {
    font-size: 14px;
    color: #2c3e50;
    text-align: center;
  }

  .game-main {
    grid-column: 2;
    grid-row: 2;
    width: 100%;
    max-width: none;
  }

  .player-status-container {
    display: none;
  }

  .game-main .target-display {
    display: none;
  }
}

/* 窄屏布局 - 宽高比小于1.5或宽度小于1024px时显示顶部状态栏 */
@media (max-aspect-ratio: 3/2),
(max-width: 1023px) {
  .player-status-container {
    display: block;
    margin-bottom: 20px;
  }

  .player-sidebar {
    display: none;
  }

  .target-sidebar {
    display: none;
  }

  .target-display {
    display: block;
  }

  .game-main {
    /* 移除padding-top设置，保持默认间距 */
  }

  /* 移动端终局页面适配 - 保持4×4布局 */
  .final-state-content {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .final-patterns-section {
    order: 2;
  }

  .final-scores {
    order: 1;
  }

  .final-cards-grid {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 1fr);
    height: 350px;
    max-height: 350px;
    gap: 6px;
  }
}

/* 超小屏幕优化 */
@media (max-width: 768px) {
  .game-bg {
    padding: 12px;
  }

  .player-status-container {
    padding: 12px;
  }

  .game-main {
    gap: 16px;
  }

  .final-cards-grid {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 1fr);
    height: 300px;
    max-height: 300px;
    gap: 4px;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1600px) {
  .game-main {
    max-width: 1400px;
  }
}

/* 规则设置模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1002;
  overflow: hidden;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  margin: 0 auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  transform: none;
  top: auto;
  left: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

/* 重连状态样式 */
.reconnect-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.reconnect-modal {
  background: white;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  min-width: 300px;
}

.reconnect-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.reconnect-modal p {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}
</style>