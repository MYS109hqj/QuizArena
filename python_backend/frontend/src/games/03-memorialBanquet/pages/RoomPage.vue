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

        <!-- 游戏进行中时，隐藏所有准备按钮 -->
        <button v-if="!isPlaying && key === store.player_id && key === store.room?.owner?.id" @click="toggleReady">
          取消准备
        </button>
        <button v-if="!isPlaying && key === store.player_id && key !== store.room?.owner?.id" @click="toggleReady">
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

      <button @click="showRules = true" class="green-btn">查看规则</button>
      <button @click="leaveRoom" class="green-btn">返回大厅</button>
    </div>

    <!-- 设置对话框 -->
    <div v-if="showSettingsDialog" class="settings-dialog-overlay" @click.self="showSettingsDialog = false">
      <div class="settings-dialog">
        <h3>房间设置</h3>
        <div class="setting-item">
          <label>最小人数：</label>
          <input type="number" v-model.number="settingsForm.minPlayers" min="1" max="10" class="setting-input">
        </div>
        <div class="setting-item">
          <label>最大人数：</label>
          <input type="number" v-model.number="settingsForm.maxPlayers" min="1" max="10" class="setting-input">
        </div>
        <div class="setting-item">
          <label>游戏难度：</label>
          <select v-model="settingsForm.difficulty" class="setting-input">
            <option value="normal">普通（12张卡牌）</option>
            <option value="hard">困难（18张卡牌）</option>
            <option value="extreme">极难（24张卡牌）</option>
          </select>
        </div>
        <div class="dialog-buttons">
          <button @click="saveSettings" class="green-btn">保存</button>
          <button @click="showSettingsDialog = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

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
          <button @click="showRules = false" class="green-btn">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router';
import { useMemorialBanquetStore } from '@/stores/memorialBanquetStore';
import { useUserStore } from '@/stores/userStore';
import { setRouteChanging, restoreConnection } from '@/ws/samePatternSocket';

const store = useMemorialBanquetStore();
const userStore = useUserStore();
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
const showRules = ref(false); // 控制规则模态框显示
const settingsForm = ref({
  minPlayers: store.room?.config?.min_players || 2,
  maxPlayers: store.room?.config?.max_players || 2,
  difficulty: store.room?.config?.difficulty || 'normal'
});

// 监听房间状态变化
watch(
  () => store.gameStatus,
  (newStatus) => {
    if (newStatus === 'playing') {
      isPlaying.value = newStatus === 'playing';
      setRouteChanging(true);
      sessionStorage.setItem('MB_ROUTE_CHANGING', 'true');

      router.replace({
        name: 'MBGame',
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
        const oldDifficulty = oldRoom?.config?.difficulty || 'normal';
        const newMinPlayers = newRoom.config.min_players || 2;
        const newMaxPlayers = newRoom.config.max_players || 2;
        const newDifficulty = newRoom.config.difficulty || 'normal';

        settingsForm.value.minPlayers = newMinPlayers;
        settingsForm.value.maxPlayers = newMaxPlayers;
        settingsForm.value.difficulty = newDifficulty;
        console.log(`🔄 设置表单已同步: min=${newMinPlayers}, max=${newMaxPlayers}, difficulty=${newDifficulty}`);

        // 如果设置发生了变化且设置对话框是打开的，自动关闭对话框
        if (showSettingsDialog.value &&
          (oldMinPlayers !== newMinPlayers || oldMaxPlayers !== newMaxPlayers || oldDifficulty !== newDifficulty)) {
          console.log('✅ 设置已更新，自动关闭设置对话框');
          showSettingsDialog.value = false;
        }
      }
    }
  },
  { immediate: true, deep: true }
);

// 确保在组件加载时尝试加入房间
onMounted(async () => {
  try {
    store.initStore();

    // 2. 检查userStore是否已加载，如果未加载则等待
    if (!userStore.isLoggedIn && !userStore.user?.id) {
      console.log('👤 等待用户数据加载...');
      await new Promise(resolve => {
        const checkInterval = setInterval(() => {
          if (userStore.user?.id) {
            clearInterval(checkInterval);
            resolve();
          }
        }, 100);
        // 设置超时，避免无限等待
        setTimeout(() => {
          clearInterval(checkInterval);
          resolve();
        }, 3000);
      });
    }

    // 3. 再次同步用户数据，确保最新
    store.syncUserData();

    // 检查登录状态
    if (!userStore.isLoggedIn) {
      console.log('🔐 用户未登录，重定向到登录页面');
      router.push('/login');
      return;
    }

    // 记录连接开始时间
    performanceMetrics.value.connectionStart = Date.now();
    loadingDetails.value = '正在连接服务器...';

    // 检查是否存在待恢复的连接
    const hasPendingConnection = localStorage.getItem('o3MB_LAST_CONNECTION') !== null;

    if (hasPendingConnection) {
      console.log('🔄 检测到待恢复的连接，尝试恢复...');
      loadingDetails.value = '正在恢复连接...';

      // 直接调用restoreConnection尝试恢复连接
      const connectionRestored = restoreConnection((data) => {
        store.handleMessage(data);
      });

      // 设置超时检查，如果连接未能及时恢复，则尝试重新加入房间
      setTimeout(() => {
        if (isLoading.value && !store.room?.room_id) {
          console.warn('连接恢复失败，尝试重新加入房间');
          loadingDetails.value = '连接恢复失败，正在尝试重新连接...';
          store.joinRoom(route.params.roomId);
        }
      }, 3000);
    } else if (!store.room || store.room.room_id !== route.params.roomId) {
      console.log(`🚀 开始加入房间: ${route.params.roomId}`);
      loadingDetails.value = '正在发送加入房间请求...';

      store.joinRoom(route.params.roomId);

      // 设置超时检查
      setTimeout(() => {
        if (isLoading.value && !store.room?.room_id) {
          loadingDetails.value = '连接超时，正在重试...';
          console.warn('房间连接超时，尝试重新连接');
          store.joinRoom(route.params.roomId);
        }
      }, 5000);
    } else {
      // 如果已经有房间信息，直接完成加载
      isLoading.value = false;
      performanceMetrics.value.totalTime = 0;
    }
  } catch (error) {
    console.error('❌ 房间加载失败:', error);
    router.push({ name: 'MBLobby' });
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
      max_players: settingsForm.value.maxPlayers,
      difficulty: settingsForm.value.difficulty
    }
  });

  // 不立即关闭对话框，等待后端响应
  // 后端会在更新成功后广播room_state消息，前端会自动更新并关闭对话框
  console.log('⏳ 等待后端设置更新响应...');
}

function leaveRoom() {
  router.push({ name: 'MBLobby' });
}

function goToGamePage() {
  setRouteChanging(true);
  sessionStorage.setItem('MB_ROUTE_CHANGING', 'true');

  router.replace({
    name: 'MBGame',
    params: { roomId: store.room?.room_id }
  });
}

// 监听页面可见性变化（刷新/关闭）
const handlePageUnload = () => {
  // 在页面刷新/关闭前保存连接信息
  if (store.room && store.room.room_id && !isRouteChange) {
    const connectionInfo = {
      roomId: store.room.room_id,
      player_info: {
        id: store.player_id,
        name: store.player_name,
        avatar: store.avatarUrl
      },
      gameType: 'o3MB'
    };
    localStorage.setItem('o3MB_LAST_CONNECTION', JSON.stringify(connectionInfo));
  }
};

onUnmounted(() => {
  window.removeEventListener('beforeunload', handlePageUnload);
});

onBeforeRouteLeave((to, from, next) => {
  const allowedTargets = ['MBGame'];
  console.log(to, to.name);
  if (allowedTargets.includes(to.name)) {
    next();
  } else {
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
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
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

.players {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 20px;
}

.player-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px #b2f7b2;
  display: flex;
  align-items: center;
  gap: 8px;
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

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: 2px solid #27ae60;
}

.avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #27ae60;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: white;
  border: 2px solid #27ae60;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.online {
  background: #27ae60;
}

.offline {
  background: #bbb;
}

.green-btn {
  background: #27ae60;
  color: #fff;
  border: none;
  margin: 10px;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 0 8px #27ae60;
  cursor: pointer;
}

.green-btn:disabled {
  background: #95d6a5;
  cursor: not-allowed;
}

.status-tag {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8em;
}

.ready {
  background-color: #d4edda;
  color: #155724;
}

.not-ready {
  background-color: #f8d7da;
  color: #721c24;
}

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

/* 设置对话框和规则模态框通用样式 */
.settings-dialog-overlay,
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

.settings-dialog-overlay>*,
.rules-dialog-overlay>* {
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

/* 规则模态框样式 */
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