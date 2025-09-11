<template>
  <div class="game-header">
    <span>房间ID：{{ store.room_id }}</span>
    <span>当前轮次：{{ store.gameState?.round }}</span>
    <span v-if="isMyTurn" class="turn-indicator">轮到你了！</span>
    <span v-else-if="store?.gameState?.current_player" class="turn-indicator">
        {{ currentPlayerName }}的回合
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
const store = useSamePatternHuntStore();
const isMyTurn = computed(() => store.gameState.current_player === store.player_id);
const currentPlayerName = computed(() => {
  const playerId = store.gameState?.current_player;
  return store.players[playerId]?.name || '未知玩家';
});
</script>

<style scoped>
.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 10px;
}
.turn-indicator {
  color: #27ae60;
  font-weight: bold;
  margin-left: 15px;
  padding: 3px 8px;
  background: rgba(39, 174, 96, 0.1);
  border-radius: 4px;
}
</style>