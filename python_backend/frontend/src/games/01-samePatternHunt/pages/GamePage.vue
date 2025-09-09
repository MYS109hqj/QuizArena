<!-- filepath: e:\Project_storage\blog_updated\QuizArena_latest\python_backend\frontend\src\games\01-samePatternHunt\pages\GamePage.vue -->
<template>
  <div class="game-bg">
    <div class="game-header">
      <span>房间ID：{{ store.room?.id }}</span>
      <button @click="leaveGame" class="green-btn">退出</button>
    </div>
    <div class="players-list">
      <div v-for="p in store.players" :key="p.id" class="player-status">
        <img :src="p.avatar" class="avatar" />
        <span>{{ p.name }}</span>
        <span v-if="p.status === 'alive'" class="alive">存活</span>
        <span v-else class="eliminated">淘汰</span>
      </div>
    </div>
    <div class="game-main">
      <!-- 游戏主逻辑组件，可根据规则扩展 -->
      <div v-if="store.gameState">
        <pre>{{ store.gameState }}</pre>
      </div>
    </div>
    <div class="chat-area">
      <!-- 聊天区可选实现 -->
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
const store = useSamePatternHuntStore();
const router = useRouter();

function leaveGame() {
  store.send({ type: 'leave_room', roomId: store.room.id });
  router.push({ name: 'SPHLobby' });
}
</script>

<style scoped>
.game-bg { background: #e6ffe6; min-height: 100vh; padding: 40px; }
.game-header { display: flex; justify-content: space-between; align-items: center; }
.players-list { display: flex; gap: 16px; margin-top: 20px; }
.player-status { background: #fff; border-radius: 12px; padding: 12px; box-shadow: 0 2px 8px #b2f7b2; display: flex; align-items: center; gap: 8px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; border: 2px solid #27ae60; }
.alive { color: #27ae60; font-weight: bold; }
.eliminated { color: #bbb; }
.green-btn { background: #27ae60; color: #fff; border: none; margin: 10px; padding: 10px 20px; border-radius: 8px; box-shadow: 0 0 8px #27ae60; cursor: pointer; }
</style>