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
  padding: 0 10px;
  position: relative;
}
.turn-indicator {
  color: #27ae60;
  font-weight: bold;
  margin-left: 15px;
  padding: 3px 8px;
  background: rgba(39, 174, 96, 0.1);
  border-radius: 4px;
}

.rules-btn {
  padding: 6px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.rules-btn:hover {
  background: #2980b9;
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