<template>
  <div class="game-bg">
    <GameHeader/>

    <PlayerStatus/>

    <!-- <div class="target-display">
      <h3>当前目标</h3>
      <div class="target-pattern">
        <img 
          :src="getPatternImage(currentTargetPattern)" 
          :alt="currentTargetPattern" 
          class="target-img"
        />
        <span class="target-id">{{ currentTargetPattern || '等待游戏开始' }}</span>
      </div>
    </div>

    <div class="cards-container" :class="{ locked: isLocked }">
      <div 
        v-for="card in cards" 
        :key="card.cardId" 
        class="card"
        :class="{ 
          flipped: flippedCards.includes(card.cardId),
          matched: isCardMatched(card.cardId),
          unmatched: isCardUnmatched(card.cardId)
        }"
        @click="handleCardClick(card)"
      >
        <div class="card-inner">
         <div class="card-front">
            <img :src="getLetterImage(cardIndex)" alt="Letter" />
          </div>
          <div class="card-back">
            <img 
              :src="getPatternImage(card.patternId)" 
              :alt="card.patternId" 
              class="card-img"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-if="isGameFinished" class="game-over-modal">
      <div class="modal-content">
        <h2>游戏结束！</h2>
        <div class="ranking-list">
          <div class="rank-item" v-for="(p, index) in rankedPlayers" :key="p.id">
            <span class="rank">{{ index + 1 }}.</span>
            <span class="player-name">{{ p.name }}</span>
            <span class="player-score">分数：{{ p.score }}</span>
          </div>
        </div>
        <button @click="leaveGame" class="green-btn">返回大厅</button>
      </div>
    </div> -->
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import GameHeader from '../components/GameHeader.vue';
import PlayerStatus from '../components/PlayerStatus.vue';

const store = useSamePatternHuntStore();
const router = useRouter();

// 在组件的script部分添加字母顺序配置
const letterOrder = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'];
// 假设字母图片命名为 letter-A.png, letter-B.png... 放在 /assets/letters/ 目录下
const getLetterImage = (index) => {
  const letter = letterOrder[index];
  return require(`@/assets/letters/${letter}.png`); // 确保图片路径正确
};

// 本地状态管理
const cards = ref([]);
const flippedCards = ref([]);
const matchedCards = ref([]);
const unmatchedCards = ref([]);
const flipBackTimer = ref(null);
const isLocked = ref(false);

// 计算属性
const currentTargetPattern = computed(() => {
  const myInfo = store.gameState?.gameInfo?.[store.player_id];
  return myInfo?.next_pattern;
});


const isGameFinished = computed(() => {
  return store.gameState?.state === 'finished';
});

const rankedPlayers = computed(() => {
  if (!store.gameState?.gameInfo) return [];
  
  return Object.entries(store.gameState.gameInfo)
    .map(([id, info]) => ({
      id,
      name: store.players.find(p => p.id === id)?.name || '未知',
      score: info.score
    }))
    .sort((a, b) => b.score - a.score);
});

// 方法
const getPlayerScore = (playerId) => {
  return store.gameState?.gameInfo?.[playerId]?.score || 0;
};

const getPlayerTargetIndex = (playerId) => {
  return store.gameState?.gameInfo?.[playerId]?.target_index || 0;
};

const getPlayerProgress = (playerId) => {
  const index = getPlayerTargetIndex(playerId);
  return Math.min((index / 48) * 100, 100);
};

const getPatternImage = (patternId) => {
  // 实际项目中替换为真实图片路径
  if (!patternId) return '@assets/placeholder.svg';
  return `@assets/patterns/${patternId}.svg`;
};

const isCardMatched = (cardId) => {
  return matchedCards.value.includes(cardId);
};

const isCardUnmatched = (cardId) => {
  return unmatchedCards.value.includes(cardId);
};

const handleCardClick = (card) => {
  // 不是自己的回合或游戏锁定时不能操作
  if (!isMyTurn.value || isLocked.value || flippedCards.value.includes(card.cardId)) {
    return;
  }

  // 发送翻牌动作
  store.send({
    type: 'action',
    action: {
      type: 'flip',
      cardId: card.cardId
    }
  });
};

const leaveGame = () => {
  if (confirm('确定要退出游戏吗？')) {
    store.send({ type: 'leave_room', roomId: store.room?.id });
    router.push({ name: 'SPHLobby' });
  }
};

// 监听游戏状态更新
const handleGameStateUpdate = (gameState) => {
  // 更新锁定状态
  isLocked.value = gameState.locked || false;
  
  // 首次加载时初始化卡牌
  if (gameState.state === 'playing' && cards.value.length === 0) {
    // 从后端获取卡牌数据（实际项目中可能需要调整获取方式）
    // 这里假设通过某种方式获取了完整的cards数据
    // 实际实现中可能需要在store中存储cards信息
  }
};

// 监听翻牌结果
const handleCardFlipped = (result) => {
  // 显示翻牌结果
  flippedCards.value.push(result.cardId);
  
  // 记录匹配状态
  if (result.matched) {
    matchedCards.value.push(result.cardId);
  } else {
    unmatchedCards.value.push(result.cardId);
  }
  
  // 设置自动翻回定时器
  clearTimeout(flipBackTimer.value);
  flipBackTimer.value = setTimeout(() => {
    flippedCards.value = flippedCards.value.filter(id => id !== result.cardId);
    unmatchedCards.value = unmatchedCards.value.filter(id => id !== result.cardId);
  }, result.flipBack);
};

// 初始化消息监听
onMounted(() => {
  // 注册消息处理函数到store
  const originalHandleMessage = store.handleMessage;
  store.handleMessage = (data) => {
    originalHandleMessage(data);
    
    switch (data.type) {
      case 'game_state':
        handleGameStateUpdate(data);
        break;
      case 'card_flipped':
        handleCardFlipped(data.result);
        break;
      case 'target_sequence':
        // 存储自己的目标序列（如果需要）
        break;
      case 'error':
        alert(data.message || data.msg);
        break;
    }
  };

  // 初始化时请求当前游戏状态
  store.send({ type: 'get_game_state' });
});

// 清理函数
onUnmounted(() => {
  clearTimeout(flipBackTimer.value);
  store.disconnect();
});

// 监听玩家目标序列更新
watch(
  () => store.gameState?.gameInfo?.[store.player_id]?.next_pattern,
  (newTarget) => {
    // 目标更新时可以添加提示动画
    if (newTarget) {
      const targetEl = document.querySelector('.target-pattern');
      if (targetEl) {
        targetEl.classList.add('pulse');
        setTimeout(() => targetEl.classList.remove('pulse'), 1000);
      }
    }
  }
);

// 监听游戏结束状态
watch(
  isGameFinished,
  (finished) => {
    if (finished) {
      clearTimeout(flipBackTimer.value);
    }
  }
);
</script>

<style scoped>
.game-bg {
  background: #e6ffe6;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 10px;
}

.current-round {
  margin: 0 15px;
  color: #333;
}

.turn-indicator {
  color: #27ae60;
  font-weight: bold;
  margin-left: 15px;
  padding: 3px 8px;
  background: rgba(39, 174, 96, 0.1);
  border-radius: 4px;
}


.target-display {
  text-align: center;
  margin: 20px 0;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.target-pattern {
  display: inline-flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
}

.target-img {
  width: 60px;
  height: 60px;
  object-fit: contain;
  border: 2px solid #27ae60;
  border-radius: 4px;
  padding: 5px;
}

.target-id {
  font-size: 1.2em;
  font-weight: bold;
  color: #333;
}

.pulse {
  animation: pulse 1s ease-in-out;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  perspective: 1000px;
}

.cards-container.locked {
  pointer-events: none;
  opacity: 0.8;
}

.card {
  height: 150px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.6s;
  cursor: pointer;
}

.card.flipped {
  transform: rotateY(180deg);
}

.card.matched .card-back {
  border-color: #27ae60;
  box-shadow: 0 0 15px rgba(39, 174, 96, 0.5);
}

.card.unmatched .card-back {
  border-color: #e74c3c;
  box-shadow: 0 0 15px rgba(231, 76, 60, 0.5);
}

.card-inner {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 8px;
  overflow: hidden;
}

.card-front, .card-back {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-back {
  transform: rotateY(180deg);
  position: absolute;
  top: 0;
  left: 0;
  border: 2px solid #ccc;
}

.card-img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.game-over-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  min-width: 300px;
}

.ranking-list {
  margin: 20px 0;
  text-align: left;
}

.rank-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.rank {
  font-weight: bold;
  color: #27ae60;
  width: 30px;
}

.green-btn {
  background: #27ae60;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 0 8px rgba(39, 174, 96, 0.5);
  cursor: pointer;
  font-size: 1em;
  transition: background 0.3s;
}

.green-btn:hover {
  background: #219653;
}

@media (max-width: 768px) {
  .cards-container {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .card {
    height: 120px;
  }
}

@media (max-width: 480px) {
  .cards-container {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .card {
    height: 100px;
  }
}
</style>