<template>
  <div :class="['players-status', orientation]">
    <PlayerCard
      v-for="player in store.players"
      :key="player.id"
      :player="player"
    />
  </div>
</template>

<script setup>
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import PlayerCard from './PlayerCard.vue';

const store = useSamePatternHuntStore();

defineProps({
  orientation: {
    type: String,
    default: 'horizontal',
    validator: (value) => ['horizontal', 'vertical'].includes(value)
  }
});
</script>
<style scoped>
.players-status {
  display: flex;
  gap: 15px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.players-status.horizontal {
  flex-direction: row;
  overflow-x: auto;
  margin-bottom: 20px;
}

.players-status.vertical {
  flex-direction: column;
  overflow-y: auto;
  max-height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .players-status.horizontal {
    gap: 10px;
    padding: 8px;
  }
  
  .players-status.vertical {
    max-height: 300px;
  }
}

/* 滚动条样式 */
.players-status::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.players-status::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.players-status::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
}

.players-status::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.5);
}
</style>