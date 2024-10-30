<!-- OnlinePlayers.vue -->
<template>
    <div v-if="onlinePlayers.length > 0" class="online-players">
      <h2>在线玩家:</h2>
      <ul>
        <li v-for="(player, index) in onlinePlayers" :key="index">
          <img :src="player.avatar" alt="Avatar" class="avatar" />
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
  