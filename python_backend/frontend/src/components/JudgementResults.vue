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

    <!-- 显示正确答案 -->
    <div v-if="correctAnswer" class="correct-answer">
      <h3>正确答案：</h3>
      <p>{{ correctAnswer }}</p>
    </div>

    <!-- 显示解析 -->
    <div v-if="explanation" class="explanation">
      <h3>解析：</h3>
      <p>{{ explanation }}</p>
    </div>
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
    correctAnswer: { // 新增正确答案
      type: String,
      required: false,
      default: ''
    },
    explanation: { // 新增解析
      type: String,
      required: false,
      default: ''
    }
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
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
}

/* 正确答案和解析的样式 */
.correct-answer, .explanation {
  margin-top: 15px;
  padding: 10px;
  background-color: #e8f5e9; /* 绿色背景 */
  border-left: 5px solid #4caf50;
}

.correct-answer h3, .explanation h3 {
  margin: 0;
  color: #2e7d32;
}

.correct-answer p, .explanation p {
  margin: 5px 0 0;
}
</style>
