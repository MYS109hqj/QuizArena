<!-- filepath: e:\Project_storage\blog_updated\QuizArena_latest\python_backend\frontend\src\games\03-memorialBanquet\pages\GameLobby.vue -->
<template>
  <div class="lobby-bg">
    <!-- 游戏规则模态框 -->
    <div v-if="showRules" class="rules-dialog-overlay" @click.self="showRules = false">
      <div class="rules-dialog">
        <h2>游戏规则</h2>
        <div class="rules-content">
          <p>记忆宴会(MemorialBanquet)是一款记忆类游戏。</p>
          <p>游戏开始时，所有卡牌的数字会展示30秒供玩家记忆。之后，玩家需要翻开两张卡牌，如果数字相同则匹配成功。</p>
          <ul>
            <li>游戏开始前30秒，所有卡牌的数字都会展示，玩家需要记住每张卡牌的位置和数字；</li>
            <li>每次翻开两张卡牌，如果数字相同则匹配成功，该玩家分数加一且必须选择其中一张卡牌的数字+1；</li>
            <li>如果数字不同，卡牌会翻回，分数扣一。多人游戏下玩家轮流行动；</li>
            <li>当一位玩家的分数达到0分，或者累计错误次数到达阈值，游戏结束，根据玩家的得分和卡牌升级次数结算名次；</li>
          </ul>
        </div>
        <div class="dialog-buttons">
          <button @click="showRules = false" class="action-btn close">关闭</button>
        </div>
      </div>
    </div>
    <!-- Header导航栏 -->
    <header class="lobby-header">
      <!-- 左侧返回主页按钮 -->
      <button @click="navigateToHome" class="back-home-btn">
        ← 返回主页
      </button>

      <!-- 右侧用户信息 -->
      <div class="user-info" @click="navigateToSettings">
        <div class="avatar-container">
          <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" alt="用户头像" class="user-avatar" />
          <div v-else class="avatar-placeholder">{{ userStore.user?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
        </div>
        <span class="username">{{ userStore.user?.username || '用户' }}</span>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="lobby-content">
      <h1 class="main-title">记忆宴会<br>MemorialBanquet——在线游戏大厅</h1>
      <div class="button-group">
        <button @click="debouncedCreate" class="action-btn create">创建新房间</button>
        <button @click="debouncedRefresh" class="action-btn refresh">刷新房间列表</button>
        <button @click="showRules = true" class="action-btn rules">查看规则</button>
      </div>

      <!-- 加载状态 -->
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
          <!-- 预加载状态指示 -->
          <div v-if="preloadingRooms[room.id]" class="preload-status">
            <span class="preload-dot"></span>
            预加载中...
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useMemorialBanquetStore } from '@/stores/memorialBanquetStore';
import { useUserStore } from '@/stores/userStore';
import { debounce } from '@/utils/debounce';
import axios from 'axios';

const store = useMemorialBanquetStore();
const userStore = useUserStore();
const router = useRouter();

const isLoading = ref(false);
const preloadingRooms = reactive({});
const showRules = ref(false);

watch(
  () => store.room_id,
  (newRoomId) => {
    if (newRoomId) {
      console.log(`🚀 检测到房间ID变化，跳转到房间: ${newRoomId}`);
      router.push({ name: 'MBRoom', params: { roomId: newRoomId } });
    }
  },
  { immediate: false }
);

// 监听房间列表变化，触发预加载
watch(
  () => store.rooms,
  (newRooms) => {
    if (newRooms && newRooms.length > 0) {
      console.log(`📊 房间列表更新，开始预加载房间信息...`);
      preloadRoomDetails(newRooms);
    }
  },
  { immediate: true, deep: true }
);

function createRoom() {
  console.log(`⏱️ 创建房间请求发送时间: ${Date.now()}`);
  store.send({ type: 'create_room', settings: { rules: 'classic' } });
}

function refreshRooms() {
  console.log(`⏱️ 刷新房间列表请求发送时间: ${Date.now()}`);
  isLoading.value = true;
  store.send({ type: 'get_room_list' });

  // 设置加载超时
  setTimeout(() => {
    if (isLoading.value) {
      isLoading.value = false;
      console.warn('房间列表加载超时');
    }
  }, 8000);
}

function enterRoom(roomId) {
  console.log(`🎯 用户点击进入房间: ${roomId}`);
  console.log(`⏱️ 进入房间请求发送时间: ${Date.now()}`);
  store.joinRoom(roomId);
}

// 预加载房间详细信息
async function preloadRoomDetails(rooms) {
  if (store.mockEnabled) return; // 模拟模式下不预加载

  for (const room of rooms) {
    if (!preloadingRooms[room.id]) {
      preloadingRooms[room.id] = true;

      try {
        // 预加载房间基本信息（不建立WebSocket连接）
        console.log(`🔍 预加载房间信息: ${room.id}`);
        const preloadStartTime = Date.now();
        const response = await axios.get(`${import.meta.env.VITE_URL}/api/room-info/${room.id}`);

        if (response.data && response.data.exists) {
          const preloadTime = Date.now() - preloadStartTime;
          console.log(`✅ 房间 ${room.id} 预加载完成，耗时: ${preloadTime}ms`);
          console.log(`📊 房间信息:`, response.data);

          // 缓存房间信息到store，减少进入房间时的加载时间
          if (!store.roomCache) {
            store.roomCache = {};
          }
          store.roomCache[room.id] = response.data;
        } else {
          console.warn(`⚠️ 房间 ${room.id} 不存在或预加载失败`);
        }
      } catch (error) {
        console.warn(`⚠️ 房间 ${room.id} 预加载失败:`, error.message);
      } finally {
        // 预加载完成后移除状态
        setTimeout(() => {
          delete preloadingRooms[room.id];
        }, 1000);
      }
    }
  }
}

// 防抖函数
const debouncedRefresh = debounce(refreshRooms, 300, { immediate: true });
const debouncedCreate = debounce(createRoom, 300, { immediate: true });

// 返回主页
function navigateToHome() {
  router.push('/');
}

// 跳转到用户设置页面
function navigateToSettings() {
  router.push('/settings');
}

onMounted(() => {
  // 初始化store，确保用户数据正确同步
  if (typeof store.initStore === 'function') {
    store.initStore();
  }

  // 检查登录状态
  checkLoginStatus();
});

// 检查用户登录状态
function checkLoginStatus() {
  // 确保用户数据已加载
  if (!userStore.isLoggedIn && !userStore.user?.username) {
    console.log('👤 等待用户数据加载...');
    // 短暂延迟后再检查，给userStore加载时间
    setTimeout(() => {
      if (!userStore.isLoggedIn) {
        console.log('🔐 用户未登录，重定向到登录页面');
        router.push('/login');
      } else {
        console.log('✅ 用户已登录，可以加入游戏大厅');
        // 同步用户数据
        if (typeof store.syncUserData === 'function') {
          store.syncUserData();
        }
        console.log('🏠 游戏大厅组件挂载，开始加载房间列表');
        refreshRooms();
      }
    }, 300);
  } else if (!userStore.isLoggedIn) {
    console.log('🔐 用户未登录，重定向到登录页面');
    router.push('/login');
  } else {
    console.log('✅ 用户已登录，可以加入游戏大厅');
    console.log('🏠 游戏大厅组件挂载，开始加载房间列表');
    refreshRooms();
  }
}



</script>

<style scoped>
.lobby-bg {
  min-height: 100vh;
  background:
    linear-gradient(70deg,
      transparent 60%,
      rgba(255, 255, 255, 0.15) 68%,
      transparent 75%),
    url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2000') center top / cover no-repeat,
    linear-gradient(135deg, #e6ffe6 0%, #b2f7b2 70%, #f8fbf8 100%);
  padding: 60px 40px 40px;
  position: relative;
  overflow: hidden;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.lobby-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 55%;
  background: radial-gradient(ellipse at 25% 45%,
      rgba(255, 255, 255, 0.25) 1%,
      transparent 60%);
  pointer-events: none;
  z-index: 1;
}

/* Header导航栏样式 */
.lobby-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  z-index: 1000;
}

/* 返回主页按钮样式 */
.back-home-btn {
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(5px);
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  color: #333;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-home-btn:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(224, 224, 224, 0.3);
}

/* 用户信息样式 */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(5px);
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  padding: 8px 15px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(224, 224, 224, 0.3);
}

.avatar-container {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: 2px solid rgba(76, 175, 80, 0.3);
}

.avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(76, 175, 80, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
  border: 2px solid rgba(76, 175, 80, 0.3);
}

.username {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

/* 主内容区域样式 */
.lobby-content {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(15px);
  border-radius: 20px;
  padding: 40px;
  margin: 100px auto 40px;
  /* 使用auto居中，确保左右边距一致 */
  max-width: 1200px;
  width: calc(100% - 80px);
  /* 确保左右各40px边距 */
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  z-index: 2;
  box-sizing: border-box;
  /* 确保padding和border包含在宽度内 */
}

.main-title {
  text-align: center;
  color: #2c3e50;
  font-size: 28px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 30px;
  text-shadow: 0 1px 3px rgba(255, 255, 255, 0.7);
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 10px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 140px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.action-btn.create {
  background: #3a9d6a;
  color: #fff;
}

.action-btn.refresh {
  background: #5ca97a;
  color: #fff;
}

.action-btn.rules {
  background: #7eb88e;
  color: #fff;
}

.action-btn.close {
  background: #95a5a6;
  color: #fff;
  margin: 0 auto;
  display: block;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:active {
  transform: translateY(0);
}

.room-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
}

.room-card {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  padding: 20px;
  cursor: pointer;
  min-width: 240px;
  max-width: 300px;
  transition: all 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.room-card:hover {
  box-shadow: 0 6px 16px rgba(58, 157, 106, 0.25);
  transform: translateY(-2px);
}

.room-card div {
  margin: 6px 0;
  color: #2c3e50;
  font-size: 15px;
}

/* 表单组 */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  color: #2c3e50;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ccc;
  font-size: 14px;
  outline: none;
}

.form-input:focus {
  border-color: #3a9d6a;
  box-shadow: 0 0 0 2px rgba(58, 157, 106, 0.2);
}

/* 头像预览 */
.avatar-preview {
  text-align: center;
  margin: 20px 0;
}

.avatar-preview img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #3a9d6a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}


/* 加载状态样式 */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  margin: 20px auto;
  max-width: 300px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #b2f7b2;
  border-top: 3px solid #27ae60;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.loading-indicator span {
  color: #2c3e50;
  font-weight: 600;
}

/* 预加载状态样式 */
.preload-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 0.8em;
  color: #7f8c8d;
}

.preload-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #27ae60;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

/* 规则模态框样式 */
.rules-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  cursor: pointer;
}

.rules-dialog-overlay>* {
  cursor: default;
}

.rules-dialog {
  background: white;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
  min-width: 400px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.rules-dialog h2 {
  text-align: center;
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: bold;
}

.rules-content {
  color: #34495e;
  line-height: 1.6;
}

.rules-content p {
  margin-bottom: 16px;
  text-indent: 2em;
}

.rules-content ul {
  margin-bottom: 20px;
}

.rules-content li {
  margin-bottom: 12px;
  padding-left: 8px;
}

.dialog-buttons {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 移除旧样式 */
.lobby-bg::before {
  display: none;
}

/* 调整背景样式 - 背景图片覆盖整个页面 */
.lobby-bg {
  min-height: 100vh;
  background:
    linear-gradient(70deg,
      transparent 60%,
      rgba(255, 255, 255, 0.15) 68%,
      transparent 75%),
    url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2000') center top / cover no-repeat,
    linear-gradient(135deg, #e6ffe6 0%, #b2f7b2 70%, #f8fbf8 100%);
  padding: 0;
  position: relative;
  overflow: hidden;
  font-family: 'Segoe UI', system-ui, sans-serif;
  z-index: 1;
}

/* 为header添加背景图片覆盖 */
.lobby-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(70deg,
      transparent 60%,
      rgba(255, 255, 255, 0.15) 68%,
      transparent 75%),
    url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2000') center top / cover no-repeat,
    linear-gradient(135deg, #e6ffe6 0%, #b2f7b2 70%, #f8fbf8 100%);
  z-index: -1;
  opacity: 0.3;
  /* 降低背景图片在header中的透明度 */
}
</style>