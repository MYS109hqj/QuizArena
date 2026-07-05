<template>
  <div class="lobby-bg">
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

    <header class="lobby-header">
      <button @click="navigateToHome" class="back-home-btn">
        ← 返回主页
      </button>
      <div class="user-info" @click="navigateToSettings">
        <div class="avatar-container">
          <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" alt="用户头像" class="user-avatar" />
          <div v-else class="avatar-placeholder">{{ userStore.user?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
        </div>
        <span class="username">{{ userStore.user?.username || '用户' }}</span>
      </div>
    </header>

    <main class="lobby-content">
      <h1 class="main-title">回合制模板<br>Template Game</h1>
      <div class="button-group">
        <button @click="createRoom" class="green-btn" :disabled="store.creatingRoom">
          {{ store.creatingRoom ? '创建中...' : '创建新房间' }}
        </button>
        <button @click="fetchRooms" class="green-btn">刷新房间列表</button>
        <button @click="showRules = true" class="green-btn">查看规则</button>
      </div>

      <div v-if="isLoading" class="loading-indicator">
        <div class="loading-spinner"></div>
        <span>正在加载房间列表...</span>
      </div>

      <div class="room-list">
        <div v-for="room in store.rooms" :key="room.id" class="room-card" @click="enterRoom(room.id)">
          <div>房间ID: {{ room.id }}</div>
          <div>房主: {{ room.owner }}</div>
          <div>人数: {{ room.players.length }}/{{ room.maxPlayers }}</div>
          <div>状态: {{ room.status }}</div>
        </div>
        <div v-if="store.rooms.length === 0 && !isLoading" class="empty-room-list">
          暂无房间，快来创建一个吧！
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useTemplateStore } from '@/stores/templateStore';
import { useUserStore } from '@/stores/userStore';

const store = useTemplateStore();
const userStore = useUserStore();
const router = useRouter();

const isLoading = ref(false);
const showRules = ref(false);

watch(
  () => store.room_id,
  (newRoomId) => {
    if (newRoomId) {
      router.push({ name: 'TemplateRoom', params: { roomId: newRoomId } });
    }
  }
);

onMounted(() => {
  store.initStore();
  fetchRooms();
});

async function createRoom() {
  await store.createRoom();
}

async function fetchRooms() {
  isLoading.value = true;
  await store.fetchRooms();
  isLoading.value = false;
}

function enterRoom(roomId) {
  store.enterRoom(roomId);
}

function navigateToHome() {
  router.push('/');
}

function navigateToSettings() {
  router.push('/settings');
}
</script>

<style scoped>
.lobby-bg {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.lobby-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.back-home-btn {
  padding: 10px 20px;
  background: rgba(255,255,255,0.2);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.avatar-container {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.username {
  color: white;
  font-size: 16px;
}

.lobby-content {
  max-width: 800px;
  margin: 0 auto;
}

.main-title {
  text-align: center;
  color: white;
  font-size: 36px;
  margin-bottom: 30px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.button-group {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.green-btn {
  padding: 15px 30px;
  background: #4CAF50;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.3s;
}

.green-btn:hover:not(:disabled) {
  background: #45a049;
}

.green-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.loading-indicator {
  text-align: center;
  color: white;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255,255,255,0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.room-list {
  display: grid;
  gap: 20px;
}

.room-card {
  background: rgba(255,255,255,0.9);
  padding: 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.3s;
}

.room-card:hover {
  transform: translateY(-5px);
}

.empty-room-list {
  text-align: center;
  color: white;
  font-size: 18px;
  padding: 40px;
}

.rules-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
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
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
