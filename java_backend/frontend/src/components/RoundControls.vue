<template>
    <div class="round-controls">
      <h3>轮次信息</h3>
      <p>当前轮次: {{ currentRound }} / {{ totalRounds }}</p>
  
      <label for="total-rounds">设置总轮次:</label>
      <input type="number" v-model="totalRoundsLocal" id="total-rounds" />
      <br />
  
      <label for="current-round">设置当前轮次:</label>
      <input type="number" v-model="currentRoundLocal" id="current-round" />
      <br />
  
      <button @click="updateCurrentRound">更新轮次信息</button>
    </div>
  </template>
  
  <script>
  import { ref, computed, watch } from 'vue';
  
  export default {
    props: {
      totalRounds: {
        type: Number,
        required: true,
      },
      currentRound: {
        type: Number,
        required: true,
      },
      updateCurrentRoundCallback: {
        type: Function,
        required: true,
      },
    },
    setup(props) {
      // 本地状态，用于存储输入的轮次值
      const totalRoundsLocal = ref(props.totalRounds);
      const currentRoundLocal = ref(props.currentRound);
  
      // 监听 prop 变化，更新本地状态
      const updateLocalValues = () => {
        totalRoundsLocal.value = props.totalRounds;
        currentRoundLocal.value = props.currentRound;
      };
  
      // 在 props 变化时更新本地变量
      watch(() => props.totalRounds, updateLocalValues);
      watch(() => props.currentRound, updateLocalValues);
  
      // 更新轮次信息
      const updateCurrentRound = () => {
        props.updateCurrentRoundCallback(currentRoundLocal.value, totalRoundsLocal.value);
      };
  
      return {
        totalRoundsLocal,
        currentRoundLocal,
        updateCurrentRound,
      };
    },
  };
  </script>
  
  <style scoped>
  .round-controls {
    margin-bottom: 20px;
  }
  </style>
  