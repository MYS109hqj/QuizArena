<template> 
    <div class="final-results">
      <h2>最终结算</h2>
      <table>
        <thead>
          <tr>
            <th>排名</th>
            <th>头像</th>
            <th>玩家</th>
            <th v-if="currentMode === 'scoring'">得分</th>
            <th v-if="currentMode === 'survival'">生命值</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(player, index) in sortedPlayers" :key="player.id">
            <td>{{ index + 1 }}</td>
            <td>
              <img v-if="player.avatar" :src="player.avatar" alt="Avatar" class="avatar" />
            </td>
            <td>{{ player.name }}</td>
            <td v-if="currentMode === 'scoring'">{{ player.score }}</td>
            <td v-if="currentMode === 'survival'">{{ player.lives }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      players: {
        type: Object,  // 修改为 Object，因为后端 `results` 是对象
        required: true,
      },
      currentMode: {
        type: String,
        required: true,
      },
    },
    computed: {
      processedPlayers() {
        return Object.entries(this.players).map(([id, player]) => ({
          id,  // 原本的 key 作为 id
          name: player.name,
          avatar: player.avatar,
          score: player.score || 0, // 计分模式的得分
          lives: player.lives || 0 // 假设初始生命是 3
        }));
      },
      sortedPlayers() {
        if (this.currentMode === 'scoring') {
          return [...this.processedPlayers].sort((a, b) => b.score - a.score);
        } else if (this.currentMode === 'survival') {
          return [...this.processedPlayers].sort((a, b) => b.lives - a.lives);
        }
        return this.processedPlayers;
      },
    },
  };
  </script>
  
  <style scoped>
  .final-results {
    border: 1px solid #ccc;
    padding: 15px;
    margin-top: 20px;
    background-color: #f9f9f9;
    border-radius: 10px;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }
  
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
  }
  
  th {
    background-color: #3498db;
    color: white;
  }
  
  /* 头像默认大小 */
  .avatar {
    width: 50px;  
    height: 50px;
    border-radius: 50%;
    object-fit: cover; 
    display: block;
    margin: auto;
    border: 2px solid #ddd;
  }
  
  /* 平板端（宽度 < 1024px） */
  @media (max-width: 1024px) {
    .avatar {
      width: 40px;
      height: 40px;
    }
  }
  
  /* 手机端（宽度 < 600px） */
  @media (max-width: 600px) {
    .avatar {
      width: 30px;
      height: 30px;
    }
  }
  </style>
  