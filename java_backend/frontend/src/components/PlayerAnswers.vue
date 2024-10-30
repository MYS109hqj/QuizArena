<template>
    <div class="player-answers">
      <h2>玩家提交的答案</h2>
      <ul>
        <li v-for="(answer, index) in playerAnswers" :key="index">
          <p><strong>{{ answer.name }}</strong> 提交了: {{ answer.text }}</p>
          <!-- 评分模式 -->
          <template v-if="judgementResults[answer.playerId]">
            <span v-if="currentMode === 'scoring'">输入该玩家得分：</span>
            <input
              v-if="currentMode === 'scoring'"
              type="number"
              v-model="judgementResults[answer.playerId].score"
              placeholder="输入得分" />
  
            <!-- 生存模式 -->
            <span v-if="currentMode === 'survival'">输入该玩家丢失生命：</span>
            <input
              v-else-if="currentMode === 'survival'"
              type="number"
              v-model="judgementResults[answer.playerId].lostLives"
              placeholder="输入丢失生命" />
          </template>
  
          <button @click="judgeAnswer(answer.playerId, true)">正确</button>
          <button @click="judgeAnswer(answer.playerId, false)">错误</button>
        </li>
      </ul>
      <button @click="submitJudgement">提交判题结果</button>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      playerAnswers: Array,
      judgementResults: Object,
      currentMode: String,
      judgeAnswer: Function,
      submitJudgement: Function,
    },
  };
  </script>
  
  <style scoped>
  .player-answers {
    margin-top: 20px;
  }
  </style>
  