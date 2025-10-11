<template>
  <div v-if="store.debugMode && store.debugPanelVisible" class="debug-panel">
    <div class="debug-header">
      <h3>🔧 调试面板</h3>
      <button @click="store.toggleDebugPanel" class="close-btn">×</button>
    </div>
    
    <div class="debug-content">
      <!-- 游戏控制 -->
      <div class="debug-section">
        <h4>游戏控制</h4>
        <div class="debug-buttons">
          <button @click="endGame" class="debug-btn danger">强制结束游戏</button>
          <button @click="resetGame" class="debug-btn warning">重置游戏</button>
          <button @click="getGameState" class="debug-btn info">获取状态</button>
        </div>
      </div>

      <!-- 玩家分数设置 -->
      <div class="debug-section">
        <h4>玩家分数设置</h4>
        <div class="score-controls">
          <div v-for="player in players" :key="player.id" class="player-score-control">
            <label>{{ player.name }} ({{ player.id }})</label>
            <div class="score-input-group">
              <input 
                v-model.number="playerScores[player.id]" 
                type="number" 
                class="score-input"
                min="0"
                max="100"
              />
              <button @click="setPlayerScore(player.id)" class="debug-btn primary">设置</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态显示 -->
      <div class="debug-section" v-if="gameState">
        <h4>游戏状态</h4>
        <pre class="state-display">{{ JSON.stringify(gameState, null, 2) }}</pre>
      </div>

      <!-- 操作结果 -->
      <div class="debug-section" v-if="operationResult">
        <h4>操作结果</h4>
        <div :class="['result-message', operationResult.success ? 'success' : 'error']">
          {{ operationResult.message || (operationResult.success ? '操作成功' : '操作失败') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const store = useSamePatternHuntStore();
const playerScores = ref({});
const gameState = ref(null);
const operationResult = ref(null);

// 计算玩家列表
const players = computed(() => {
  return Object.values(store.players).map(player => ({
    id: player.id,
    name: player.name,
    score: store.gameState?.gameInfo?.[player.id]?.score || 0
  }));
});

// 初始化玩家分数
onMounted(() => {
  players.value.forEach(player => {
    playerScores.value[player.id] = player.score;
  });
});

// 设置玩家分数
const setPlayerScore = async (playerId) => {
  const score = playerScores.value[playerId];
  if (score === undefined || score === null) {
    showResult('请输入有效的分数', false);
    return;
  }

  operationResult.value = null;
  const result = await store.debugSetScore(playerId, score);
  
  if (result.success) {
    showResult(`玩家 ${playerId} 分数已设置为 ${score}`, true);
  } else {
    showResult(`设置分数失败: ${result.error}`, false);
  }
};

// 强制结束游戏
const endGame = async () => {
  operationResult.value = null;
  const result = await store.debugEndGame();
  
  if (result.success) {
    showResult('游戏已强制结束', true);
  } else {
    showResult(`结束游戏失败: ${result.error}`, false);
  }
};

// 重置游戏
const resetGame = async () => {
  operationResult.value = null;
  const result = await store.debugResetGame();
  
  if (result.success) {
    showResult('游戏已重置', true);
    // 刷新页面以重新加载游戏状态
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } else {
    showResult(`重置游戏失败: ${result.error}`, false);
  }
};

// 获取游戏状态
const getGameState = async () => {
  operationResult.value = null;
  const result = await store.debugGetGameState();
  
  if (result.success) {
    gameState.value = result.game_state;
    showResult('游戏状态获取成功', true);
  } else {
    showResult(`获取游戏状态失败: ${result.error}`, false);
  }
};

// 显示操作结果
const showResult = (message, success) => {
  operationResult.value = {
    message,
    success
  };
  
  // 3秒后清除结果
  setTimeout(() => {
    operationResult.value = null;
  }, 3000);
};
</script>

<style scoped>
.debug-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background: white;
  border: 2px solid #3498db;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  z-index: 10000;
  overflow-y: auto;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #3498db;
  color: white;
  border-radius: 10px 10px 0 0;
}

.debug-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.debug-content {
  padding: 20px;
}

.debug-section {
  margin-bottom: 24px;
}

.debug-section h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.debug-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.debug-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.debug-btn.primary {
  background: #3498db;
  color: white;
}

.debug-btn.primary:hover {
  background: #2980b9;
}

.debug-btn.danger {
  background: #e74c3c;
  color: white;
}

.debug-btn.danger:hover {
  background: #c0392b;
}

.debug-btn.warning {
  background: #f39c12;
  color: white;
}

.debug-btn.warning:hover {
  background: #d35400;
}

.debug-btn.info {
  background: #95a5a6;
  color: white;
}

.debug-btn.info:hover {
  background: #7f8c8d;
}

.player-score-control {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.score-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.score-input {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
}

.state-display {
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.result-message {
  padding: 12px;
  border-radius: 6px;
  font-weight: bold;
}

.result-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.result-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@media (max-width: 768px) {
  .debug-panel {
    width: 95%;
    max-height: 90vh;
  }
  
  .debug-buttons {
    flex-direction: column;
  }
  
  .player-score-control {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .score-input-group {
    width: 100%;
    justify-content: space-between;
  }
}
</style>