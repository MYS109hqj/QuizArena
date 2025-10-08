<template>
  <div class="room-bg">
    <h2>房间：{{ store.room?.name || store.room?.room_id || '未知' }}</h2>
    <div>房主：{{ store.room?.owner?.name || '未知' }}</div>
    <div>最大人数：{{ store.room?.config?.max_players || '未知' }}</div>
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
        <button @click="modifySettings" class="green-btn">修改设置</button>
      </div>
      
      <button @click="leaveRoom" class="green-btn">返回大厅</button>
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

const isPlaying = ref(false);
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

// 确保在组件加载时尝试加入房间
if (!store.room || store.room.room_id !== route.params.roomId) {
  store.send({ type: 'join_room', roomId: route.params.roomId });
}

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
  store.send({ type: 'toggle_ready', roomId: store.room.room_id });
}

function startGame() {
  // 开始游戏逻辑
  store.send({ type: 'start_game', roomId: store.room.room_id });
}

function modifySettings() {
  // 修改设置逻辑
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

onMounted(() => {
  window.addEventListener('beforeunload', handlePageUnload);
});

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
.room-bg { background: #e6ffe6; min-height: 100vh; padding: 40px; }
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
</style>
