<template>
  <div class="game-header">
    <span>房间ID：{{ store.room_id }}</span>
    <span>当前轮次：{{ store.gameState?.round }}</span>
    <span v-if="isMyTurn" class="turn-indicator">轮到你了！</span>
    <span v-else-if="store?.gameState?.current_player" class="turn-indicator">
        {{ currentPlayerName }}的回合
    </span>
    
    <button class="rules-btn" @click="showRulesModal = true">
      ⚙️ 规则设置
    </button>

    <div v-if="showRulesModal" class="modal-overlay" @click.self="showRulesModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>游戏规则设置</h3>
          <button class="close-btn" @click="showRulesModal = false">×</button>
        </div>
        <RulesSettings />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';
import RulesSettings from './RulesSettings.vue';

const store = useSamePatternHuntStore();
const showRulesModal = ref(false);

const isMyTurn = computed(() => store.gameState.current_player === store.player_id);
const currentPlayerName = computed(() => {
  const playerId = store.gameState?.current_player;
  return store.players[playerId]?.name || '未知玩家';
});
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

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}
</style>