<template>
  <div class="game-bg">
    <div v-if="isReconnecting" class="reconnect-overlay">
      <div class="reconnect-modal">
        <div class="reconnect-spinner"></div>
        <p>{{ reconnectStatus }}</p>
      </div>
    </div>

    <div v-if="showFinalState" class="final-state-overlay">
      <div class="final-state-modal">
        <div class="final-state-header">
          <h2>游戏结束！</h2>
          <button class="close-btn" @click="closeFinalState">×</button>
        </div>
        <div class="final-state-content">
          <div class="final-scores">
            <h3 class="section-title">最终得分</h3>
            <div class="score-list">
              <div v-for="player in rankedPlayers" :key="player.id" class="score-item"
                :class="{ 'winner': player.isWinner }">
                <span class="player-name">{{ player.name }}</span>
                <span class="player-score">{{ player.score }}分</span>
                <span v-if="player.isWinner" class="winner-badge">🏆 获胜</span>
              </div>
            </div>
          </div>
          <div class="final-total">
            <h3 class="section-title">总分达到: {{ store.gameState.total_score }}</h3>
          </div>
        </div>
        <div class="final-state-actions">
          <button @click="playAgain" class="green-btn">再来一局</button>
          <button @click="leaveGame" class="green-btn">返回大厅</button>
        </div>
      </div>
    </div>

    <header class="game-header">
      <button @click="handleExit" class="exit-btn">退出游戏</button>
      <h1>回合制模板游戏</h1>
      <div class="status-indicator">
        {{ isCurrentPlayer ? '轮到你了' : '等待其他玩家' }}
      </div>
    </header>

    <div class="game-main">
      <div class="score-display">
        <div class="total-score">
          <span class="score-label">总分</span>
          <span class="score-value">{{ store.gameState.total_score }}</span>
          <span class="score-target">/ {{ store.gameState.target_score }}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
      </div>

      <div class="player-scores">
        <h3>玩家得分</h3>
        <div v-for="(score, playerId) in store.gameState.player_scores" :key="playerId" 
             class="player-score-item" :class="{ 'current-player': playerId === store.gameState.current_player }">
          <span class="player-id">{{ getPlayerName(playerId) }}</span>
          <span class="player-points">{{ score }}</span>
        </div>
      </div>

      <div class="action-area">
        <button @click="handleIncrement" 
                :disabled="!isCurrentPlayer || store.gameState.state !== 'player_turn'"
                class="increment-btn">
          +1
        </button>
      </div>

      <div class="game-status">
        <p>当前回合: {{ store.gameState.round }}</p>
        <p>当前状态: {{ getStateText(store.gameState.state) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useTemplateStore } from '@/stores/templateStore';

const store = useTemplateStore();
const router = useRouter();
const route = useRoute();

const isReconnecting = ref(false);
const reconnectStatus = ref('');
const showFinalState = ref(false);

const isCurrentPlayer = computed(() => {
  return store.gameState.current_player === store.player_id;
});

const progressPercentage = computed(() => {
  const target = store.gameState.target_score || 100;
  const current = store.gameState.total_score || 0;
  return Math.min((current / target) * 100, 100);
});

const rankedPlayers = computed(() => {
  const scores = store.gameState.player_scores;
  const players = [];
  for (const [id, score] of Object.entries(scores)) {
    players.push({
      id,
      name: getPlayerName(id),
      score
    });
  }
  players.sort((a, b) => b.score - a.score);
  if (players.length > 0) {
    players[0].isWinner = true;
  }
  return players;
});

function getPlayerName(playerId) {
  return store.players[playerId]?.name || playerId;
}

function getStateText(state) {
  const stateMap = {
    'init': '初始化',
    'player_turn': '玩家回合',
    'checking_end': '检查结束条件',
    'finished': '游戏结束'
  };
  return stateMap[state] || state;
}

watch(
  () => store.gameState.state,
  (state) => {
    if (state === 'finished') {
      showFinalState.value = true;
    }
  }
);

onMounted(() => {
  store.initStore();
});

onUnmounted(() => {
});

function handleIncrement() {
  if (isCurrentPlayer.value && store.gameState.state === 'player_turn') {
    store.incrementScore();
  }
}

function handleExit() {
  store.leaveRoom();
  router.push({ name: 'TemplateLobby' });
}

function closeFinalState() {
  showFinalState.value = false;
}

async function playAgain() {
  showFinalState.value = false;
  await store.startGame();
}

function leaveGame() {
  store.leaveRoom();
  router.push({ name: 'TemplateLobby' });
}
</script>

<style scoped>
.game-bg {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  color: white;
}

.exit-btn {
  padding: 10px 20px;
  background: #f44336;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.status-indicator {
  padding: 10px 20px;
  background: rgba(76, 175, 80, 0.3);
  border-radius: 20px;
  color: #4CAF50;
  font-weight: bold;
}

.game-main {
  max-width: 600px;
  margin: 0 auto;
}

.score-display {
  text-align: center;
  margin-bottom: 30px;
}

.total-score {
  color: white;
  font-size: 48px;
  font-weight: bold;
}

.score-label {
  font-size: 24px;
  margin-right: 10px;
}

.score-value {
  color: #FFD700;
}

.score-target {
  font-size: 24px;
  color: #aaa;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: rgba(255,255,255,0.2);
  border-radius: 10px;
  margin-top: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #FFD700);
  transition: width 0.3s;
}

.player-scores {
  background: rgba(255,255,255,0.1);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.player-scores h3 {
  color: white;
  margin-bottom: 15px;
}

.player-score-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  color: white;
}

.player-score-item.current-player {
  background: rgba(76, 175, 80, 0.2);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 5px;
}

.action-area {
  text-align: center;
  margin-bottom: 30px;
}

.increment-btn {
  width: 200px;
  height: 200px;
  font-size: 64px;
  font-weight: bold;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
  box-shadow: 0 10px 30px rgba(76, 175, 80, 0.4);
}

.increment-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 15px 40px rgba(76, 175, 80, 0.5);
}

.increment-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.increment-btn:disabled {
  background: #666;
  cursor: not-allowed;
  box-shadow: none;
}

.game-status {
  text-align: center;
  color: #aaa;
}

.reconnect-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.reconnect-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-top: 5px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.final-state-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.final-state-modal {
  background: white;
  padding: 30px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
}

.final-state-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.close-btn {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
}

.section-title {
  margin-bottom: 15px;
}

.score-list {
  margin-bottom: 20px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.score-item.winner {
  background: #FFF8E1;
}

.winner-badge {
  color: #FFD700;
}

.final-state-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.green-btn {
  padding: 12px 24px;
  background: #4CAF50;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}
</style>
