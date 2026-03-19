<!-- components/PlayerCard.vue -->
<template>
  <div class="player-card" :class="{ 'current-turn': isCurrentTurn, 'me': isMe }">
    <img :src="player.avatar" :alt="player.name" class="avatar" />

    <div class="player-info">
      <span class="name">{{ player.name }}</span>
      <span class="score">分数：{{ score }}</span>
      <span class="error-count">错误：{{ errorCount }}</span>
    </div>

    <div v-if="isCurrentTurn" class="current-turn-marker">正在操作</div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';
import { useMemorialBanquetStore } from '@/stores/memorialBanquetStore';

const props = defineProps({
  player: {
    type: Object,
    required: true
  }
});

const store = useMemorialBanquetStore();

const playerGameData = computed(() => {
  const gameId = props.player.id;
  return store.gameState?.gameInfo?.[gameId] || {};
});

const score = computed(() => playerGameData.value.score || 0);
const errorCount = computed(() => playerGameData.value.errorCount || 0);
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
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.player-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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

.error-count {
  font-size: 0.9em;
  color: #e74c3c;
}

.current-turn-marker {
  background: #27ae60;
  color: white;
  font-size: 0.8em;
  padding: 2px 8px;
  border-radius: 4px;
}
</style>