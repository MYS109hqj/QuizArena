<template>
  <div class="room-bg">
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>正在加载房间信息...</p>
    </div>

    <h2>房间：{{ store.room?.name || store.room?.room_id || '未知' }}</h2>
    <div>房主：{{ store.room?.owner?.name || '未知' }}</div>
    <div>最大人数：{{ store.room?.config?.max_players || '未知' }}</div>
    <div>最小人数：{{ store.room?.config?.min_players || '未知' }}</div>
    <div>当前人数：{{ Object.keys(store.players).length || 0 }}</div>

    <div class="players">
      <div v-for="(p, key) in store.players" :key="key" class="player-card">
        <div class="avatar-container">
          <img v-if="p.avatar" :src="p.avatar" class="avatar-image" :alt="p.name" />
          <div v-else class="avatar-placeholder">{{ p.name?.charAt(0)?.toUpperCase() || 'P' }}</div>
        </div>
        <span>{{ p.name }}</span>
        <span v-if="key === store.room?.owner?.id">房主</span>
        <span v-else>玩家</span>
        <span class="status-tag" :class="p.ready ? 'ready' : 'not-ready'">
          {{ p.ready ? '已准备' : '未准备' }}
        </span>

        <button
          v-if="!isPlaying && String(key) === String(store.player_id) && String(key) === String(store.room?.owner?.id)"
          @click="toggleReady">
          取消准备
        </button>
        <button
          v-if="!isPlaying && String(key) === String(store.player_id) && String(key) !== String(store.room?.owner?.id)"
          @click="toggleReady">
          {{ p.ready ? '取消准备' : '准备' }}
        </button>
      </div>
    </div>

    <div v-if="isPlaying" class="game-started提示">
      <p>⚠️ 游戏已开始！请前往游戏页面。</p>
      <button @click="goToGamePage" class="green-btn">进入游戏</button>
    </div>

    <div v-else>
      <div v-if="isOwner">
        <button @click="startGame" class="green-btn" :disabled="!allPlayersReady">
          开始游戏
        </button>
      </div>

      <button @click="showRules = true" class="green-btn">查看规则</button>
      <button @click="leaveRoom" class="green-btn">返回大厅</button>
    </div>

    <div v-if="showRules" class="rules-dialog-overlay" @click.self="showRules = false">
      <div class="rules-dialog">
        <h2>游戏规则</h2>
        <div class="rules-content">
          <p>回合制模板游戏 - 简单的按按钮+1游戏</p>
          <ul>
            <li>玩家轮流按按钮，每次按按钮让总分+1</li>
            <li>总分达到100时游戏结束</li>
            <li>每个玩家按按钮时自己的分数也会+1</li>
          </ul>
        </div>
        <div class="dialog-buttons">
          <button @click="showRules = false" class="green-btn">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useTemplateStore } from '@/stores/templateStore';
import { isWebSocketActive } from '@/ws/templateSocket';

const store = useTemplateStore();
const router = useRouter();
const route = useRoute();

const isLoading = ref(true);
const showRules = ref(false);

const isOwner = computed(() => {
  const ownerId = store.room?.owner?.id;
  const playerId = store.player_id;
  return ownerId !== undefined && String(ownerId) === String(playerId);
});

const isPlaying = computed(() => {
  return store.gameStatus === 'playing';
});

const allPlayersReady = computed(() => {
  const playerList = Object.values(store.players);
  if (playerList.length === 0) return false;
  return playerList.every(p => p.ready);
});

watch(
  () => store.gameStatus,
  (status) => {
    if (status === 'playing') {
      goToGamePage();
    }
  }
);

onMounted(() => {
  store.initStore();
  if (!isWebSocketActive()) {
    store.enterRoom(route.params.roomId);
  }
  setTimeout(() => {
    isLoading.value = false;
  }, 500);
});

async function toggleReady() {
  await store.toggleReady();
}

async function startGame() {
  await store.startGame();
}

function goToGamePage() {
  router.push({ name: 'TemplateGame', params: { roomId: route.params.roomId } });
}

async function leaveRoom() {
  await store.leaveRoom();
  router.push({ name: 'TemplateLobby' });
}
</script>

<style scoped>
.room-bg {
  min-height: 100vh;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-top: 5px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.players {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin: 30px 0;
}

.player-card {
  background: rgba(255, 255, 255, 0.2);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  min-width: 150px;
}

.avatar-container {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin: 0 auto 10px;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.status-tag {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  margin-top: 10px;
}

.status-tag.ready {
  background: #4CAF50;
}

.status-tag.not-ready {
  background: #f44336;
}

.green-btn {
  padding: 15px 30px;
  background: #4CAF50;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 18px;
  cursor: pointer;
  margin-right: 10px;
  margin-bottom: 10px;
}

.green-btn:hover:not(:disabled) {
  background: #45a049;
}

.green-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.rules-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.rules-dialog {
  background: white;
  padding: 30px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  color: #333;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
