<template>
  <div class="final-state-bg">
    <div class="final-state-container">
      <h2>终局页面 - 所有卡牌图案</h2>
      
      <!-- 游戏信息 -->
      <div class="game-info">
        <div>房间ID: {{ roomId }}</div>
        <div>游戏状态: {{ finalState?.game_state || '加载中...' }}</div>
      </div>

      <!-- 卡牌展示区域 -->
      <div class="cards-grid">
        <div 
          v-for="(card, cardId) in finalState?.cards || {}" 
          :key="cardId"
          class="card-item"
        >
          <div class="card-pattern">
            <img 
              :src="getPatternImage(card.patternId)" 
              :alt="`图案 ${card.patternId}`"
              class="pattern-image"
            />
          </div>
          <div class="card-info">
            <div>卡牌: {{ cardId }}</div>
            <div>图案ID: {{ card.patternId }}</div>
          </div>
        </div>
      </div>

      <!-- 玩家信息 -->
      <div class="players-info" v-if="finalState?.scores">
        <h3>玩家分数</h3>
        <div 
          v-for="(score, playerId) in finalState.scores" 
          :key="playerId"
          class="player-score"
        >
          玩家 {{ playerId }}: {{ score }} 分
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button @click="backToResults" class="action-btn primary">返回结果页面</button>
        <button @click="backToLobby" class="action-btn secondary">返回首页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const route = useRoute();
const router = useRouter();
const store = useSamePatternHuntStore();

const roomId = ref(route.params.roomId);
const finalState = ref(null);
const loading = ref(true);
const error = ref('');

// 获取图案图片URL
const getPatternImage = (patternId) => {
  // 这里需要根据实际的图案资源路径进行调整
  return `/patterns/${patternId}.png`;
};

// 加载终局状态数据
const loadFinalState = async () => {
  try {
    loading.value = true;
    error.value = '';
    
    const response = await fetch(`/api/game-final-state/01-samePatternHunt/${roomId.value}`);
    console.log(response);
    const data = await response.json();
    
    if (data.game_finished && data.final_state) {
      finalState.value = data.final_state;
    } else {
      error.value = data.error || '无法获取终局状态';
    }
  } catch (err) {
    error.value = '加载终局状态失败: ' + err.message;
  } finally {
    console.log("loadFinalState获取结束")
    loading.value = false; 
  }
};

// 返回结果页面
const backToResults = () => {
  router.push({ name: 'SPHResult', params: { roomId: roomId.value } });
};

// 返回首页
const backToLobby = () => {
  router.push({ name: 'SPHLobby' });
};

onMounted(() => {
  console.log("FinalState onMounted trigerred");
  loadFinalState();
});
</script>

<style scoped>
.final-state-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.final-state-container {
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 2rem;
}

.game-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #007bff;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.card-item {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 10px;
  padding: 15px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.card-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  border-color: #007bff;
}

.card-pattern {
  margin-bottom: 10px;
}

.pattern-image {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 5px;
  background: #f8f9fa;
  padding: 5px;
}

.card-info {
  font-size: 0.9rem;
  color: #666;
}

.players-info {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.players-info h3 {
  margin-bottom: 15px;
  color: #333;
}

.player-score {
  padding: 8px 0;
  border-bottom: 1px solid #dee2e6;
}

.player-score:last-child {
  border-bottom: none;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.action-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 150px;
}

.action-btn.primary {
  background: #007bff;
  color: white;
}

.action-btn.primary:hover {
  background: #0056b3;
  transform: translateY(-2px);
}

.action-btn.secondary {
  background: #6c757d;
  color: white;
}

.action-btn.secondary:hover {
  background: #545b62;
  transform: translateY(-2px);
}

/* 加载状态样式 */
.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
  text-align: center;
}
</style>