<!-- components/GameOverModal.vue -->
<template>
  <div v-if="show" class="game-over-modal">
    <div class="modal-content">
      <h2>游戏结束！</h2>
      <div class="ranking-list">
        <div class="rank-item" v-for="(p, index) in rankedPlayers" :key="p.id">
          <span class="rank">{{ medalEmoji(index) }} {{ index + 1 }}</span>
          <span class="player-name">{{ p.name }}</span>
          <span class="player-score">分数：{{ p.score }}</span>
        </div>
      </div>
      <div class="button-group">
        <button @click="onPlayAgain" class="green-btn">再来一局</button>
        <button @click="onLeave" class="gray-btn">返回大厅</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

defineProps({
  show: Boolean,
  rankedPlayers: { type: Array, default: () => [] }
});

const emit = defineEmits(['leave', 'playAgain']);

const onPlayAgain = () => {
  emit('playAgain');
};

const onLeave = () => {
  if (confirm('确定要退出游戏吗？')) {
    emit('leave');
  }
};

const medalEmoji = (index) => {
  return index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅';
};
</script>

<style scoped>
.game-over-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  min-width: 300px;
}

.ranking-list {
  margin: 20px 0;
  text-align: left;
}

.rank-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.rank {
  font-weight: bold;
  color: #27ae60;
  width: 40px;
}

.green-btn {
  background: #27ae60;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 0 8px rgba(39, 174, 96, 0.5);
  cursor: pointer;
  font-size: 1em;
  transition: background 0.3s;
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.green-btn {
  background: #27ae60;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 0 8px rgba(39, 174, 96, 0.5);
  cursor: pointer;
  font-size: 1em;
  transition: background 0.3s;
}

.green-btn:hover {
  background: #219653;
}

.gray-btn {
  background: #95a5a6;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  transition: background 0.3s;
}

.gray-btn:hover {
  background: #7f8c8d;
}
</style>