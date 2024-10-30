<template>
    <div>
      <div v-if="currentMode === 'scoring'">
        <label for="init-scores">初始化分数:</label>
        <input type="number" v-model="initScores" />
        <button @click="initializeScores">初始化分数</button>
      </div>
      <div v-else-if="currentMode === 'survival'">
        <label for="init-lives">初始化生命:</label>
        <input type="number" v-model="initLives" />
        <button @click="initializeLives">初始化生命</button>
      </div>
    </div>
  </template>
  
  <script>
  import { ref } from 'vue';
  
  export default {
    props: {
      currentMode: String,
      initializeScoresCallback: Function,
      initializeLivesCallback: Function,
    },
    setup(props) {
      const initScores = ref(0);
      const initLives = ref(3);
  
      const initializeScores = () => {
        props.initializeScoresCallback(initScores.value);
      };
  
      const initializeLives = () => {
        props.initializeLivesCallback(initLives.value);
      };
  
      return {
        initScores,
        initLives,
        initializeScores,
        initializeLives,
      };
    },
  };
  </script>
  
  <style scoped>
  </style>
  