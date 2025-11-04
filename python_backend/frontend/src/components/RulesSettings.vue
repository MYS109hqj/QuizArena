<template>
  <div class="rules-settings">
    <h3>游戏规则设置</h3>
    
    <div class="rule-group">
      <h4>翻牌限制规则</h4>
      
      <div class="rule-item">
        <label class="switch">
          <input 
            type="checkbox" 
            v-model="localRules.flipRestrictions.actionLockEnabled"
            @change="updateRules"
          >
          <span class="slider"></span>
        </label>
        <span class="rule-label">有行动正在进行，暂不能进行下一次翻牌</span>
      </div>

      <div class="rule-item">
        <label class="switch">
          <input 
            type="checkbox" 
            v-model="localRules.flipRestrictions.preventFlipDuringAnimation"
            @change="updateRules"
          >
          <span class="slider"></span>
        </label>
        <span class="rule-label">牌未翻回，无法翻开新牌</span>
      </div>

      <div class="rule-item">
        <label class="switch">
          <input 
            type="checkbox" 
            v-model="localRules.flipRestrictions.waitForOthersToFlipBack"
            @change="updateRules"
          >
          <span class="slider"></span>
        </label>
        <span class="rule-label">其他玩家翻开的牌未翻回，到自己的轮次无法立刻翻牌</span>
      </div>
    </div>

    <div class="rule-group">
      <h4>高级设置</h4>
      
      <div class="rule-item">
        <label>翻牌动画时长 (毫秒)</label>
        <input 
          type="number" 
          v-model.number="localRules.animationDuration"
          @change="updateRules"
          min="1000"
          max="10000"
          step="500"
        >
      </div>

      <div class="rule-item">
        <label>最大同时翻牌数</label>
        <input 
          type="number" 
          v-model.number="localRules.maxConcurrentFlips"
          @change="updateRules"
          min="1"
          max="5"
        >
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore'

const store = useSamePatternHuntStore()
const localRules = ref({ ...store.gameRules })

// 监听store规则变化
watch(() => store.gameRules, (newRules) => {
  localRules.value = { ...newRules }
}, { deep: true })

const updateRules = () => {
  store.updateGameRules(localRules.value)
}
</script>

<style scoped>
.rules-settings {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rule-group {
  margin-bottom: 20px;
}

.rule-group h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.rule-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.rule-item:hover {
  background: #e9ecef;
  border-color: #dee2e6;
}

.rule-label {
  margin-left: 15px;
  flex: 1;
  min-width: 0; /* 防止文本溢出影响布局 */
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
  line-height: 1.4;
}

.switch {
  position: relative;
  display: inline-block;
  flex-shrink: 0;  /* 防止被压缩 */
  width: 60px;  /* 固定宽度 */
  height: 30px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transform: translateX(0);
}

input:checked + .slider {
  background-color: #2196F3;
}

input:checked + .slider:before {
  transform: translateX(30px);  /* 60px容器 - 22px滑块 - 4px右边距 - 4px左边距 = 30px */
}

/* 添加焦点状态 */
input:focus + .slider {
  box-shadow: 0 0 1px #2196F3;
}

/* 添加禁用状态 */
input:disabled + .slider {
  opacity: 0.6;
  cursor: not-allowed;
}

.rule-item > label:not(.switch) {
  margin-right: 12px;
  font-size: 14px;
  color: #2c3e50;
  min-width: 140px;
  font-weight: 500;
}

.rule-item input[type="number"] {
  width: 90px;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.rule-item input[type="number"]:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}
</style>