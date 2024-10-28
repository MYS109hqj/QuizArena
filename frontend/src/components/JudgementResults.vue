<template>
    <div v-if="results && Object.keys(results).length > 0" class="judgement-results">
      <h2>第{{ round }}轮判题结果</h2>
      <ul>
        <li v-for="(result, playerId) in results" :key="playerId" class="result-item">
          <img v-if="result.avatar" :src="result.avatar" alt="Avatar" class="avatar" />
          <strong>{{ result.name }}</strong>: 
          <span v-if="result.correct">正确 ✅</span>
          <span v-else>错误 ❌</span>
          <span v-if="currentMode === 'scoring'"> - 获得分数: {{ result.score }}</span>
          <span v-else-if="currentMode === 'survival'"> - 失去生命: {{ result.lostLives }}</span>
        </li>
      </ul>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      results: {
        type: Object,
        required: true
      },
      currentMode: {
        type: String,
        required: true
      },
      round: {
        type: Number,
        required: true
      },
    }
  };
  </script>
  
  <style scoped>
  .judgement-results {
    border: 1px solid #ccc;
    padding: 10px;
    margin-top: 20px;
    background-color: #f9f9f9;
  }
  
  .result-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .avatar {
    width: 30px; /* 控制头像大小 */
    height: 30px; /* 控制头像大小 */
    border-radius: 50%; /* 使头像圆形 */
    margin-right: 10px; /* 头像与名称之间的间距 */
  }
  </style>
  