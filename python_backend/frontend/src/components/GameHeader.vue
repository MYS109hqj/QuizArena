<template>
  <div class="game-header">
    <button class="exit-btn" @click="exitRoom" title="返回">
      ◀️
    </button>
    
    <span>房间ID：{{ store.room_id }}</span>
    <span>当前轮次：{{ store.gameState?.round }}</span>
    <span v-if="isMyTurn" class="turn-indicator">轮到你了！</span>
    <span v-else-if="store?.gameState?.current_player" class="turn-indicator">
        {{ currentPlayerName }}的回合
    </span>
    
    <button class="rules-btn" @click="$emit('showRules')">
      ⚙️ 规则设置
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const store = useSamePatternHuntStore();

const isMyTurn = computed(() => store.gameState.current_player === store.player_id);
const currentPlayerName = computed(() => {
  const playerId = store.gameState?.current_player;
  return store.players[playerId]?.name || '未知玩家';
});

const emit = defineEmits(['exit', 'showRules']);

const exitRoom = () => {
  if (confirm('确定要返回吗？')) {
    store.send({ type: 'leave_room', roomId: store.room?.room_id });
    emit('exit');
  }
};
</script>

<style scoped>
.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 20px;
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}
.turn-indicator {
  color: #2e7d32;
  font-weight: 600;
  margin-left: 15px;
  padding: 6px 12px;
  background: rgba(46, 125, 50, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(46, 125, 50, 0.2);
}

.rules-btn {
  padding: 8px 16px;
  background: #3a9d6a;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(58, 157, 106, 0.3);
}

.rules-btn:hover {
  background: #2e7d32;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(46, 125, 50, 0.4);
}

.exit-btn {
  padding: 8px 12px;
  background: rgba(46, 125, 50, 0.1); /* 用户指定的半透明绿色 */
  color: #2e7d32; /* 文字颜色改为绿色 */
  border: 1px solid rgba(46, 125, 50, 0.3); /* 添加边框 */
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(46, 125, 50, 0.1);
}

.exit-btn:hover {
  background: rgba(46, 125, 50, 0.2); /* 悬停时增加透明度 */
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(46, 125, 50, 0.2);
}


</style>