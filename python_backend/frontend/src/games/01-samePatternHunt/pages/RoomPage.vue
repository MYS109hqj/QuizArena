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
        
        <!-- 房主的准备按钮逻辑 -->
        <button v-if="key === store.player_id && key === store.room?.owner?.id" @click="toggleReady">
          取消准备
        </button>
        
        <!-- 普通玩家的准备按钮逻辑 -->
        <button v-if="key === store.player_id && key !== store.room?.owner?.id" @click="toggleReady">
          {{ p.ready ? '取消准备' : '准备' }}
        </button>
      </div>
    </div>
    
    <!-- 房主的特殊按钮 -->
    <div v-if="isOwner">
      <button @click="startGame" class="green-btn" :disabled="!allPlayersReady">
        开始游戏
      </button>
      <button @click="modifySettings" class="green-btn">修改设置</button>
    </div>
    
    <button @click="leaveRoom" class="green-btn">返回大厅</button>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const store = useSamePatternHuntStore();
const router = useRouter();
const route = useRoute();

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
  store.disconnect();
  router.push({ name: 'SPHLobby' });
}

// 监听页面可见性变化（刷新/关闭）
const handlePageUnload = () => {
  store.disconnect();
};

onMounted(() => {
  window.addEventListener('beforeunload', handlePageUnload);
});

onUnmounted(() => {
  window.removeEventListener('beforeunload', handlePageUnload);
});

// 监听路由离开（点击后退或其他导航）
onBeforeRouteLeave((to, from, next) => {
  const confirmLeave = window.confirm('你确定要离开房间吗？这将断开连接。');
  if (confirmLeave) {
    store.disconnect(); // 断开连接
    next(); // 允许跳转
  } else {
    next(false); // 阻止跳转
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
</style>
