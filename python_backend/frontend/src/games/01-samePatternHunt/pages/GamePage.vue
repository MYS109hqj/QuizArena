<template>
  <div class="game-bg">
    <GameHeader />
    <PlayerStatus />
    <TargetDisplay />
    <CardsGrid
      :cards="store.cards"
      :flipped-cards="store.flippedCards"
      :matched-cards="store.matchedCards"
      :unmatched-cards="store.unmatchedCards"
      :is-locked="isLocked"
    />
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
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}
</style>