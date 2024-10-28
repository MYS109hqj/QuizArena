<template>
  <div class="container">
    <h1>答题端</h1>
    <div class="content">
      <!-- 左侧主要内容 -->
      <div class="main-content">
        <!-- 显示用户信息 -->
        <div v-if="name" class="user-info">
          <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="avatar" />
          <p>姓名: {{ name }}</p>
        </div>

        <!-- 根据问题类型显示题目 -->
        <div v-if="receivedQuestion">
          <p>题目: {{ receivedQuestion.content.question }}</p>
          
          <!-- 问答题类型 -->
          <div v-if="receivedQuestion.content.type === 'qa'">
            <input v-model="answer" placeholder="输入答案" />
            <button @click="sendAnswer">提交答案</button>
          </div>

          <!-- 选择题类型 -->
          <div v-else-if="receivedQuestion.content.type === 'mcq'">
            <div v-for="(option, index) in receivedQuestion.content.options" :key="index">
              <button 
                :class="{ selected: selectedOption === index }" 
                @click="selectOption(index)">
                {{ String.fromCharCode(65 + index) }}. {{ option }}
              </button>
            </div>
            <button @click="submitMCQAnswer" :disabled="selectedOption === null">提交答案</button>
          </div>
          
          <!-- 多提示题类型 -->
          <div v-else-if="receivedQuestion.content.type === 'hints'" class="question-section">
            <p>基本提示: {{ receivedQuestion.content.basicHint }}</p>
            <ul>
              <li v-for="(hint, index) in receivedQuestion.content.additionalHints" :key="index">
                追加提示词 {{ index + 1 }}: {{ hint }}
              </li>
            </ul>
            <input v-model="answer" placeholder="输入答案" class="input-field"/>
            <button @click="sendAnswer" class="primary-button">提交答案</button>
          </div>
        </div>
        
        <!-- 显示等待判题状态 -->
        <div v-if="awaitingJudgement">
          <p>答案已提交，等待提问者判题...</p>
        </div>

        <!-- 清空答案按钮 -->
        <div class="button-group">
          <button @click="clearAnswers" class="secondary-button">清空答案</button>
        </div>

        <!-- 显示已发送的答案 -->
        <div v-if="answers.length > 0" class="answers-section">
          <h2>已发送的答案:</h2>
          <ul>
            <li v-for="(ans, index) in answers" :key="index" class="answer-item">
              <img v-if="ans.avatar" :src="ans.avatar" alt="Avatar" class="avatar" />
              <p><strong>{{ ans.name }}</strong>: {{ ans.text }}</p>
            </li>
          </ul>
        </div>
      </div>

      <!-- 右侧玩家列表 -->
      <div class="sidebar">
        <h2>玩家列表</h2>
        <p>提问者：<span :class="{'online': questionerConnected, 'offline': !questionerConnected}">
          {{ questionerConnected ? '在线' : '离线' }}
        </span>
        </p>
        <ul>
          <li v-for="(player, index) in players" :key="index">
            <img v-if="player.avatar" :src="player.avatar" alt="Avatar" class="avatar-small" />
            {{ player.name }}
            <!-- 根据模式显示分数或生命 -->
            <template v-if="currentMode === 'scoring'">
              - 分数: {{ player.score }}
            </template>
            <template v-else-if="currentMode === 'survival'">
              - 生命: {{ player.lives }}
            </template>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRoute } from 'vue-router';

export default {
  setup() {
    const route = useRoute();
    const socket = new WebSocket(`ws://localhost:8000/ws/${route.params.roomId}`);
    const name = route.query.name || 'your name';
    const avatarUrl = route.query.avatarUrl || '';
    const userId = route.query.playerId || generateUniqueId();  // 从路由查询参数中获取 playerId 或生成新的 ID
    const receivedQuestion = ref(null);
    const answer = ref('');
    const answers = ref([]);
    const selectedOption = ref(null);
    const players = ref([]);
    const questionerConnected = ref(false);  // 提问者连接状态
    const currentMode = ref('none');  // 当前模式
    const playerScore = ref(0);  // 玩家得分
    const playerLives = ref(3);  // 玩家生命值（生存模式）
    const awaitingJudgement = ref(false);  // 等待判题状态

    // 生成唯一用户 ID 的函数
    function generateUniqueId() {
      return 'user-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
    }

    // WebSocket 消息处理
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'question') {
        console.log('Received question:', data);
        // 只在接收到新问题时更新
        receivedQuestion.value = data;
        if (receivedQuestion.value.questionId !== data.questionId) {
          answers.value = [];  // 清空答案列表
          selectedOption.value = null;  // 重置选择题选项
        }
      } else if (data.type === 'answer') {
        answers.value.push(data);  // 添加新答案
      } else if (data.type === 'player_list') {
        players.value = data.players;  // 更新玩家列表
        questionerConnected.value = data.questionerConnected;  // 更新提问者连接状态
      } else if (data.type === 'judgement_complete') {
        awaitingJudgement.value = false;  // 判题完成
      } else if (data.type === 'mode_update') {
        currentMode.value = data.currentMode;  // 更新当前模式
      }
    };

    // WebSocket 打开时发送用户信息
    socket.onopen = () => {
      console.log('连接建立:', { name, avatarUrl, roomId: route.params.roomId });

      const joinData = {
        id: userId,  // 使用从 URL 查询参数传入的 playerId
        type: 'join',
        name: name.trim(),
        avatar: avatarUrl.trim() || '',
      };
      socket.send(JSON.stringify(joinData));
    };

    // 提交文本答案
    const sendAnswer = () => {
      if (socket.readyState === WebSocket.OPEN && answer.value.trim() !== '') {
        const answerData = {
          type: 'answer',
          playerId: userId,  // 包含 playerId 以便提问者识别
          name: name.trim(),
          avatar: avatarUrl.trim() || '',
          text: answer.value.trim(),
        };
        socket.send(JSON.stringify(answerData));
        answer.value = ''; // 清空输入框
        awaitingJudgement.value = true;  // 等待判题
      }
    };

    // 提交选择题答案
    const submitMCQAnswer = () => {
      if (selectedOption.value !== null) {
        const answerData = {
          type: 'answer',
          playerId: userId,
          name: name.trim(),
          avatar: avatarUrl.trim() || '',
          text: `选项 ${String.fromCharCode(65 + selectedOption.value)}`, // 例如选项 A、B、C 等
        };
        socket.send(JSON.stringify(answerData));
        selectedOption.value = null; // 清空选择
        awaitingJudgement.value = true;  // 等待判题
      }
    };

    // 选择题选项
    const selectOption = (index) => {
      selectedOption.value = index;
    };

    // 清空答案
    const clearAnswers = () => {
      answers.value = [];
    };

    return {
      name,
      avatarUrl,
      receivedQuestion,
      answer,
      answers,
      sendAnswer,
      submitMCQAnswer,
      selectOption,
      clearAnswers,
      selectedOption,
      players,
      questionerConnected,
      currentMode,
      playerScore,
      playerLives,
      awaitingJudgement,
    };
  }
};
</script>

<style scoped>
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.content {
  display: flex;
  flex-direction: row;
}

.main-content {
  flex: 3;
  margin-right: 20px;
}

.sidebar {
  flex: 1;
  background-color: #ecf0f1;
  padding: 15px;
  border-radius: 10px;
}

.sidebar h2 {
  text-align: center;
  color: #34495e;
}

.sidebar ul {
  list-style-type: none;
  padding: 0;
}

.sidebar li {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.avatar-small {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
}

.online {
  color: green;
}

.offline {
  color: red;
}

.user-info {
  margin-bottom: 20px;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.button-group {
  margin-top: 20px;
}

.secondary-button {
  background-color: #f39c12;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

.secondary-button:hover {
  background-color: #e67e22;
}

.answers-section {
  margin-top: 20px;
}

.answer-item {
  margin-bottom: 10px;
}

.answer-item img {
  margin-right: 10px;
}
</style>
