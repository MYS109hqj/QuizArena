<template>
  <div class="lobby-bg">
    <div v-if="showRules" class="rules-dialog-overlay" @click.self="showRules = false">
      <div class="rules-dialog">
        <h2>Flip 7 游戏规则</h2>
        <div class="rules-content">
          <h3>基础规则</h3>
          <ul>
            <li>玩家轮流抽牌，目标是收集不重复的数字牌</li>
            <li>翻到重复数字牌则爆牌，本轮得分为0</li>
            <li>可以随时选择停牌，保留当前分数</li>
            <li>连翻7张不同数字牌可获得七连翻奖励</li>
            <li>先达到目标分数(默认200分)的玩家获胜</li>
          </ul>
          <h3>功能牌</h3>
          <ul>
            <li><strong>Flip 3</strong>: 指定一名玩家立即连抽3张牌</li>
            <li><strong>Freeze</strong>: 冻结一名玩家，使其跳过后续回合</li>
            <li><strong>Second Chance</strong>: 获得一次避免爆牌的机会</li>
          </ul>
          <h3>特殊牌</h3>
          <ul>
            <li><strong>+2/+4/+6/+8/+10</strong>: 直接加分</li>
            <li><strong>×2</strong>: 本轮数字分数翻倍</li>
          </ul>
          <h3>复仇版(可选)</h3>
          <ul>
            <li><strong>÷2/-2/-4/-6/-8/-10</strong>: 选择目标玩家扣分</li>
            <li><strong>残酷模式</strong>: 修改牌可作用于已停止/爆牌的玩家</li>
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
      <h1 class="main-title">🎮 Flip 7</h1>
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
import { useFlip7Store } from '@/stores/flip7Store';
import { useUserStore } from '@/stores/userStore';

const store = useFlip7Store();
const userStore = useUserStore();
const router = useRouter();

const isLoading = ref(false);
const showRules = ref(false);

watch(
  () => store.room_id,
  (newRoomId) => {
    if (newRoomId) {
      router.push({ name: 'Flip7Room', params: { roomId: newRoomId } });
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
  font-size: 48px;
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
  z-index: 1000;
}

.rules-dialog {
  background: white;
  padding: 30px;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.rules-dialog h2 {
  margin-bottom: 20px;
  color: #333;
}

.rules-dialog h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #667eea;
}

.rules-dialog ul {
  margin: 0 0 10px 20px;
  color: #666;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>