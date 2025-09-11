<!-- components/TargetDisplay.vue -->
<template>
  <div class="target-display">
    <h3>当前目标</h3>
    <div class="target-pattern" :class="{ pulse: isPulsing }">
      <img 
        :src="getPatternImage(currentTargetPattern)" 
        :alt="currentTargetPattern || 'placeholder'" 
        class="target-img"
      />
      <span class="target-id">{{ currentTargetPattern || '等待游戏开始' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const store = useSamePatternHuntStore();
const isPulsing = ref(false);

// 获取当前玩家的目标图案
const currentTargetPattern = computed(() => {
  return store.gameState?.gameInfo?.[store.player_id]?.next_pattern || null;
});

// 目标更新时触发脉冲动画
watch(currentTargetPattern, (newVal) => {
  if (newVal) {
    isPulsing.value = true;
    setTimeout(() => (isPulsing.value = false), 1000);
  }
});

// 图片路径工具
const getPatternImage = (patternId) => {
  if (!patternId) {
    return new URL('/assets/placeholder.svg', import.meta.url).href;
  }
  return new URL(`/assets/patterns/${patternId}.svg`, import.meta.url).href;
};
</script>

<style scoped>
.target-display {
  text-align: center;
  margin: 20px 0;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.target-pattern {
  display: inline-flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
}

.target-img {
  width: 60px;
  height: 60px;
  object-fit: contain;
  border: 2px solid #27ae60;
  border-radius: 4px;
  padding: 5px;
}

.target-id {
  font-size: 1.2em;
  font-weight: bold;
  color: #333;
}

.pulse {
  animation: pulse 1s ease-in-out;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>