<!-- filepath: e:\Project_storage\blog_updated\QuizArena_latest\python_backend\frontend\src\games\01-samePatternHunt\pages\GameLobby.vue -->
<template>
  <div class="lobby-bg">
    <h1 class="main-title">寻找目标图案<br>SamePatternHunt——在线游戏大厅</h1>
    <div class="button-group">
      <button @click="debouncedCreate" class="action-btn create">创建新房间</button>
      <button @click="debouncedRefresh" class="action-btn refresh">刷新房间列表</button>
      <button @click="openProfileDialog" class="action-btn profile">设置个人信息</button>
    </div>
    <PlayerProfileDialog :show="showProfile" @close="showProfile = false" />
    
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
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import { debounce } from '@/utils/debounce';
import PlayerProfileDialog from '@/modules/PlayerProfileDialog.vue';
import axios from 'axios';

const store = useSamePatternHuntStore();
const router = useRouter();

// 状态管理
const isLoading = ref(false);
const preloadingRooms = reactive({}); // 记录正在预加载的房间

// 监听store.room_id变化，自动跳转到房间页面
watch(
  () => store.room_id,
  (newRoomId) => {
    if (newRoomId) {
      console.log(`🚀 检测到房间ID变化，跳转到房间: ${newRoomId}`);
      router.push({ name: 'SPHRoom', params: { roomId: newRoomId } });
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

onMounted(() => {
  console.log('🏠 游戏大厅组件挂载，开始加载房间列表');
  refreshRooms();
});

// 设置个人信息
const showProfile = ref(false);
function openProfileDialog(){
  showProfile.value = true;
}

</script>

<style scoped>
.lobby-bg {
  min-height: 100vh;
  background: 
    linear-gradient(
      70deg,
      transparent 60%,
      rgba(255, 255, 255, 0.15) 68%,
      transparent 75%
    ),
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
  background: radial-gradient(
    ellipse at 25% 45%,
    rgba(255, 255, 255, 0.25) 1%,
    transparent 60%
  );
  pointer-events: none;
  z-index: 1;
}

.main-title {
  text-align: center;
  color: #2c3e50;
  font-size: 28px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 30px;
  text-shadow: 0 1px 3px rgba(255, 255, 255, 0.7);
  z-index: 2;
  position: relative;
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
  z-index: 2;
  position: relative;
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
  z-index: 2;
  position: relative;
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
  box-shadow: 0 0 0 2px rgba(58,157,106,0.2);
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}


/* 加载状态样式 */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
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
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>