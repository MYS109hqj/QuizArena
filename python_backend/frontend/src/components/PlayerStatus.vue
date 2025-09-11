<template>
  <div class="players-status">
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
</script>
<style scoped>
.players-status {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding: 10px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
}
</style>