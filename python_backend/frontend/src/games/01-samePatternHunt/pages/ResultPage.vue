<!-- filepath: e:\Project_storage\blog_updated\QuizArena_latest\python_backend\frontend\src\games\01-samePatternHunt\pages\ResultPage.vue -->
<template>
  <div class="result-bg">
    <h2>游戏结束</h2>
    <div v-if="store.gameResult">
      <div>胜利方：{{ store.gameResult.winner }}</div>
      <div>排名：</div>
      <ul>
        <li v-for="p in store.gameResult.ranking" :key="p.id">
          {{ p.name }} - {{ p.score }}
        </li>
      </ul>
      <div>统计信息：{{ store.gameResult.stats }}</div>
    </div>
    <button @click="restartGame" class="green-btn">再来一局</button>
    <button @click="backToLobby" class="green-btn">返回首页</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
const store = useSamePatternHuntStore();
const router = useRouter();

function restartGame() {
  store.send({ type: 'start_game', roomId: store.room.id });
}
function backToLobby() {
  router.push({ name: 'SPHLobby' });
}
</script>

<style scoped>
.result-bg { background: #e6ffe6; min-height: 100vh; padding: 40px; }
.green-btn { background: #27ae60; color: #fff; border: none; margin: 10px; padding: 10px 20px; border-radius: 8px; box-shadow: 0 0 8px #27ae60; cursor: pointer; }
</style>