<template>
  <div class="room-bg">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>正在加载房间信息...</p>
      <p class="loading-details">{{ loadingDetails }}</p>
    </div>
    
    <h2>房间：{{ store.room?.name || store.room?.room_id || '未知' }}</h2>
    <div>房主：{{ store.room?.owner?.name || '未知' }}</div>
    <div>最大人数：{{ store.room?.config?.max_players || '未知' }}</div>
    <div>最小人数：{{ store.room?.config?.min_players || '未知' }}</div>
    <div>当前人数：{{ Object.keys(store.players).length || 0 }}</div>
    <div class="players">
      <div v-for="(p, key) in store.players" :key="key" class="player-card">
        <img :src="p.avatar" class="avatar" :alt="p.name" />
        <span>{{ p.name }}</span>
        <span v-if="key === store.room?.owner?.id">房主</span>
        <span v-else>玩家</span>
        <span class="status-tag" :class="p.ready ? 'ready' : 'not-ready'">
          {{ p.ready ? '已准备' : '未准备' }}
        </span>
        
        <!-- 游戏进行中时，隐藏所有准备按钮 -->
        <button 
          v-if="!isPlaying && key === store.player_id && key === store.room?.owner?.id" 
          @click="toggleReady"
        >
          取消准备
        </button>
        <button 
          v-if="!isPlaying && key === store.player_id && key !== store.room?.owner?.id" 
          @click="toggleReady"
        >
          {{ p.ready ? '取消准备' : '准备' }}
        </button>
      </div>
    </div>
    
    <!-- 游戏进行中时，显示提示和跳转按钮 -->
    <div v-if="isPlaying" class="game-started提示">
      <p>⚠️ 游戏已开始！请前往游戏页面。</p>
      <button @click="goToGamePage" class="green-btn">进入游戏</button>
    </div>
    
    <!-- 游戏未开始时，显示房主按钮和返回大厅按钮 -->
    <div v-else>
      <!-- 房主的特殊按钮 -->
      <div v-if="isOwner">
        <button @click="startGame" class="green-btn" :disabled="!allPlayersReady">
          开始游戏
        </button>
        <button @click="showSettingsDialog = true" class="green-btn">修改设置</button>
      </div>
      
      <button @click="leaveRoom" class="green-btn">返回大厅</button>
    </div>

    <!-- 设置对话框 -->
    <div v-if="showSettingsDialog" class="settings-dialog-overlay" @click.self="showSettingsDialog = false">
      <div class="settings-dialog">
        <h3>房间设置</h3>
        <div class="setting-item">
          <label>最小人数：</label>
          <input 
            type="number" 
            v-model.number="settingsForm.minPlayers" 
            min="1" 
            max="10"
            class="setting-input"
          >
        </div>
        <div class="setting-item">
          <label>最大人数：</label>
          <input 
            type="number" 
            v-model.number="settingsForm.maxPlayers" 
            min="1" 
            max="10"
            class="setting-input"
          >
        </div>
        <div class="dialog-buttons">
          <button @click="saveSettings" class="green-btn">保存</button>
          <button @click="showSettingsDialog = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import { setRouteChanging } from '@/ws/samePatternSocket';

const store = useSamePatternHuntStore();
const router = useRouter();
const route = useRoute();

// 加载状态管理
const isLoading = ref(true);
const loadingDetails = ref('正在建立连接...');
const performanceMetrics = ref({
  connectionStart: null,
  roomInfoReceived: null,
  totalTime: null
});

const isPlaying = ref(false);

// 设置对话框相关
const showSettingsDialog = ref(false);
const settingsForm = ref({
  minPlayers: store.room?.config?.min_players || 2,
  maxPlayers: store.room?.config?.max_players || 2
});

// 监听房间状态变化
watch(
  () => store.gameStatus,
  (newStatus) => {
    if (newStatus === 'playing') {
      isPlaying.value = newStatus === 'playing';
      // 设置路由切换标记，避免触发重连
      setRouteChanging(true);
      sessionStorage.setItem('SPH_ROUTE_CHANGING', 'true');
      
      router.replace({ 
        name: 'SPHGame', 
        params: { roomId: store.room.room_id } 
      });
    }
  },
  { immediate: true }
);

// 监听房间信息加载完成和更新
watch(
  () => store.room,
  (newRoom, oldRoom) => {
    if (newRoom && newRoom.room_id) {
      // 记录房间信息接收时间
      performanceMetrics.value.roomInfoReceived = Date.now();
      
      if (performanceMetrics.value.connectionStart) {
        performanceMetrics.value.totalTime = 
          performanceMetrics.value.roomInfoReceived - performanceMetrics.value.connectionStart;
        
        // 输出性能指标
        console.log(`🎯 房间加载性能指标:
- 连接建立耗时: ${performanceMetrics.value.roomInfoReceived - performanceMetrics.value.connectionStart}ms
- 总加载时间: ${performanceMetrics.value.totalTime}ms`);
        
        loadingDetails.value = `加载完成！总耗时: ${performanceMetrics.value.totalTime}ms`;
        
        // 延迟隐藏加载状态，让用户看到完成信息
        setTimeout(() => {
          isLoading.value = false;
        }, 500);
      }
      
      // 更新设置表单
      if (newRoom.config) {
        const oldMinPlayers = oldRoom?.config?.min_players || 2;
        const oldMaxPlayers = oldRoom?.config?.max_players || 2;
        const newMinPlayers = newRoom.config.min_players || 2;
        const newMaxPlayers = newRoom.config.max_players || 2;
        
        settingsForm.value.minPlayers = newMinPlayers;
        settingsForm.value.maxPlayers = newMaxPlayers;
        console.log(`🔄 设置表单已同步: min=${newMinPlayers}, max=${newMaxPlayers}`);
        
        // 如果设置发生了变化且设置对话框是打开的，自动关闭对话框
        if (showSettingsDialog.value && 
            (oldMinPlayers !== newMinPlayers || oldMaxPlayers !== newMaxPlayers)) {
          console.log('✅ 设置已更新，自动关闭设置对话框');
          showSettingsDialog.value = false;
        }
      }
    }
  },
  { immediate: true, deep: true }
);

// 确保在组件加载时尝试加入房间
onMounted(() => {
  // 记录连接开始时间
  performanceMetrics.value.connectionStart = Date.now();
  loadingDetails.value = '正在连接服务器...';
  
  if (!store.room || store.room.room_id !== route.params.roomId) {
    console.log(`🚀 开始加入房间: ${route.params.roomId}`);
    loadingDetails.value = '正在发送加入房间请求...';
    
    store.send({ type: 'join_room', roomId: route.params.roomId });
    
    // 设置超时检查
    setTimeout(() => {
      if (isLoading.value && !store.room?.room_id) {
        loadingDetails.value = '连接超时，正在重试...';
        console.warn('房间连接超时，尝试重新连接');
        store.send({ type: 'join_room', roomId: route.params.roomId });
      }
    }, 5000);
  } else {
    // 如果已经有房间信息，直接完成加载
    isLoading.value = false;
    performanceMetrics.value.totalTime = 0;
  }
});

// 计算属性，判断当前用户是否为房主
const isOwner = computed(() => store.player_id === store.room?.owner?.id);

// 计算属性，判断是否所有玩家都已准备
const allPlayersReady = computed(() => {
  if (!store.players || Object.keys(store.players).length === 0) return false;
  
  // 检查所有玩家是否都已准备
  return Object.values(store.players).every(player => player.ready);
});

function toggleReady() {
  // 实现准备/取消准备逻辑
  console.log(`⏱️ 准备状态切换请求发送时间: ${Date.now()}`);
  store.send({ type: 'toggle_ready', roomId: store.room.room_id });
}

function startGame() {
  // 开始游戏逻辑
  console.log(`⏱️ 开始游戏请求发送时间: ${Date.now()}`);
  store.send({ type: 'start_game', roomId: store.room.room_id });
}

function saveSettings() {
  // 验证设置
  if (settingsForm.value.minPlayers > settingsForm.value.maxPlayers) {
    alert('最小人数不能大于最大人数');
    return;
  }
  
  if (settingsForm.value.minPlayers < 1) {
    alert('最小人数不能小于1');
    return;
  }
  
  if (settingsForm.value.maxPlayers < 1) {
    alert('最大人数不能小于1');
    return;
  }
  
  // 发送设置更新请求
  console.log(`⏱️ 更新设置请求发送时间: ${Date.now()}`);
  store.send({ 
    type: 'update_settings', 
    roomId: store.room.room_id,
    settings: {
      min_players: settingsForm.value.minPlayers,
      max_players: settingsForm.value.maxPlayers
    }
  });
  
  // 不立即关闭对话框，等待后端响应
  // 后端会在更新成功后广播room_state消息，前端会自动更新并关闭对话框
  console.log('⏳ 等待后端设置更新响应...');
}

function leaveRoom() {
  // 离开房间逻辑
  router.push({ name: 'SPHLobby' });
}

function goToGamePage() {
  // 设置路由切换标记，避免触发重连
  setRouteChanging(true);
  sessionStorage.setItem('SPH_ROUTE_CHANGING', 'true');
  
  router.replace({ 
    name: 'SPHGame', 
    params: { roomId: store.room?.room_id } 
  });
}

// 监听页面可见性变化（刷新/关闭）
const handlePageUnload = () => {
  // store.disconnect();
};

onUnmounted(() => {
  window.removeEventListener('beforeunload', handlePageUnload);
});

// 监听路由离开（点击后退或其他导航）,store的重置完全交由该方法处理
onBeforeRouteLeave((to, from, next) => {
  // 定义允许直接跳转的目标路由（游戏页面）
  const allowedTargets = ['SPHGame'];
  console.log(to,to.name);
  if (allowedTargets.includes(to.name)) {
    next();
  } else {
    // 其他情况（返回大厅、浏览器回退等）显示确认弹窗
    const confirmLeave = window.confirm('你确定要离开房间吗？这将断开连接。');
    if (confirmLeave) {
      next();
      console.log("通过RoomPage的onBeforeRouteLeave断开了websocket连接")
      store.disconnect(); 
    } else {
      next(false);
    }
  }
});
</script>

<style scoped>
.room-bg { 
  background: #e6ffe6; 
  min-height: 100vh; 
  padding: 40px; 
  position: relative;
}

/* 加载状态样式 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(230, 255, 230, 0.95);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #b2f7b2;
  border-top: 4px solid #27ae60;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: #2c3e50;
  font-size: 1.2em;
  margin: 5px 0;
}

.loading-details {
  font-size: 0.9em;
  color: #7f8c8d;
  font-style: italic;
}

.players { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 20px; }
.player-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px #b2f7b2; display: flex; align-items: center; gap: 8px; }
.avatar { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #27ae60; }
.status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.online { background: #27ae60; }
.offline { background: #bbb; }
.green-btn { background: #27ae60; color: #fff; border: none; margin: 10px; padding: 10px 20px; border-radius: 8px; box-shadow: 0 0 8px #27ae60; cursor: pointer; }
.green-btn:disabled { background: #95d6a5; cursor: not-allowed; }
.status-tag { padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
.ready { background-color: #d4edda; color: #155724; }
.not-ready { background-color: #f8d7da; color: #721c24; }
.game-started提示 {
  margin: 20px 0;
  padding: 16px;
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  text-align: center;
}
.game-started提示 p {
  color: #856404;
  font-size: 1.1em;
  margin-bottom: 12px;
}

/* 设置对话框样式 */
.settings-dialog-overlay {
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

.settings-dialog-overlay > * {
  cursor: default;
}

.settings-dialog {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 300px;
  max-width: 400px;
}

.settings-dialog h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  text-align: center;
}

.setting-item {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.setting-item label {
  font-weight: 500;
  color: #2c3e50;
  min-width: 80px;
}

.setting-input {
  width: 80px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
}

.setting-input:focus {
  outline: none;
  border-color: #27ae60;
}

.dialog-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #7f8c8d;
}
</style>