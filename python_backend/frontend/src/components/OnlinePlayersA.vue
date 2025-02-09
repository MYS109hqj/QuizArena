<template>
    <div class="online-players">
      <div class="round-info">
        <p>房间模式: {{ currentMode }}</p>
        <p>当前轮次: {{ currentRound }} / {{ totalRounds }}</p>
      </div>
      <h2>在线玩家:</h2>
      <ul>
        <li v-for="(player, index) in onlinePlayers" :key="index">
          <img v-if="player.avatar" :src="player.avatar" alt="Avatar" class="avatar" />
          <strong>{{ player.name }}</strong>
          <template v-if="currentMode === 'scoring'">
            <span> - 分数: {{ player.score }}</span>
          </template>
          <template v-else-if="currentMode === 'survival'">
            <span> - 生命: {{ player.lives }}</span>
          </template>
        </li>
      </ul>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      onlinePlayers: {
        type: Array,
        required: true
      },
      currentMode: {
        type: String,
        required: true
      },
      currentRound: {
        type: Number,
        required: true
      },
      totalRounds: {
        type: Number,
        required: true
      }
    }
  };
  </script>
  
  <style scoped>
  .online-players {
    margin-top: 20px;
  }
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-right: 10px;
  }
  </style>
  