<!-- components/PlayerCard.vue -->
<template>
  <div class="player-card" :class="{ 'current-turn': isCurrentTurn, 'me': isMe }">
    <!-- 头像 -->
    <img :src="player.avatar" :alt="player.name" class="avatar" />

    <!-- 信息区 -->
    <div class="player-info">
      <span class="name">{{ player.name }}</span>
      <span class="score">分数：{{ score }}</span>

      <!-- 进度条 -->
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
      </div>
      <span class="progress-text">进度：{{ targetIndex }}/48</span>
    </div>

    <!-- 当前操作标记 -->
    <div v-if="isCurrentTurn" class="current-turn-marker">正在操作</div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

// 接收原始 player 对象（或仅 id）
const props = defineProps({
  player: {
    type: Object,
    required: true
  }
});

const store = useSamePatternHuntStore();

// 从 store 中根据 playerId 获取游戏数据
const playerGameData = computed(() => {
  const gameId = props.player.id;
  return store.gameState?.gameInfo?.[gameId] || {};
});

// 本地计算状态
const score = computed(() => playerGameData.value.score || 0);
const targetIndex = computed(() => playerGameData.value.target_index || 0);
const progress = computed(() => Math.min((targetIndex.value / 48) * 100, 100));
const isCurrentTurn = computed(() => store.gameState?.current_player === props.player.id);
const isMe = computed(() => props.player.id === store.player_id);
</script>

<style scoped>
/* 添加了me和current-turn样式类，未实现 */
.player-card {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 250px;
  padding: 10px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.player-info {
  flex: 1;
}

.name {
  font-weight: bold;
  display: block;
  margin-bottom: 5px;
}

.score {
  font-size: 0.9em;
  color: #666;
}

.progress-container {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  margin: 5px 0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #27ae60;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8em;
  color: #888;
}

.current-turn-marker {
  background: #27ae60;
  color: white;
  font-size: 0.8em;
  padding: 2px 8px;
  border-radius: 4px;
}
</style>