<template>
  <div class="game-bg">
    <GameHeader class="game-header" />
    
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
      <CardsGrid
        :cards="store.cards"
        :flipped-cards="store.flippedCards"
        :matched-cards="store.matchedCards"
        :unmatched-cards="store.unmatchedCards"
        :is-locked="isLocked"
      />
    </div>
    
    <!-- 目标栏侧边栏 - 宽屏时显示 -->
    <div class="target-sidebar">
      <TargetDisplay />
    </div>
    
    <GameOverModal
      :show="isGameFinished"
      :ranked-players="rankedPlayers"
      @leave="leaveGame"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import GameHeader from '@/components/GameHeader.vue';
import PlayerStatus from '@/components/PlayerStatus.vue';
import TargetDisplay from '@/components/TargetDisplay.vue';
import CardsGrid from '@/components/CardsGrid.vue';
import GameOverModal from '@/components/GameOverModal.vue';

const store = useSamePatternHuntStore();
const router = useRouter();

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

// 消息处理器：已全部移入 store，无需再覆盖
onMounted(() => {
  // 不再覆盖 store.handleMessage
  // 只需发送请求获取状态
  store.send({ type: 'get_game_state' });
});

onUnmounted(() => {
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
  z-index: 100;
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
  overflow-y: auto; /* 允许垂直滚动 */
  justify-content: flex-start; /* 从顶部开始排列 */
  align-items: center; /* 水平居中内容 */
  padding: 20px 0; /* 添加上下内边距 */
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
    width: 240px; /* 缩小宽度 */
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
@media (max-aspect-ratio: 3/2), (max-width: 1023px) {
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
}

/* 超大屏幕优化 */
@media (min-width: 1600px) {
  .game-main {
    max-width: 1400px;
  }
}


</style>