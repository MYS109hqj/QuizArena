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
    const userId = generateUniqueId();  // 生成唯一的用户 ID
    const receivedQuestion = ref(null);
    const answer = ref('');
    const answers = ref([]);
    const selectedOption = ref(null);
    const players = ref([]);
    const questionerConnected = ref(false);  // 新增：提问者连接状态

    // 生成唯一用户 ID 的函数
    function generateUniqueId() {
      return 'user-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
    }

    // 处理 WebSocket 消息
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'question') {
        // 仅在接收到新的题目时更新
        console.log('Received question:', data);
        if (!receivedQuestion.value){
          receivedQuestion.value = data;  // 更新问题
          if (receivedQuestion.value.questionId !== data.questionId) {
            answers.value = [];  // 清空答案列表
            selectedOption.value = null;  // 重置选择题选项
          }
        }
      } else if (data.type === 'answer') {
        answers.value.push(data);  // 添加新答案
      } else if (data.type === 'player_list') {
        players.value = data.players;  // 更新玩家列表
        questionerConnected.value = data.questionerConnected;  // 更新提问者状态
      }
    };

    // 连接打开时发送用户信息
    socket.onopen = () => {
      console.log('连接建立:');
      console.log('name:', name, 'avatarUrl: ', avatarUrl, 'roomId:', route.params.roomId);

      const joinData = {
        id: userId,
        type: 'join',
        name: name.trim(),
        avatar: avatarUrl.trim() || '',
      };
      socket.send(JSON.stringify(joinData));
    };

    // 提交答题的函数
    const sendAnswer = () => {
      if (socket.readyState === WebSocket.OPEN) {
        if (answer.value.trim() !== '' && name.trim() !== '') {
          const answerData = {
            type: 'answer',
            name: name.trim(),
            avatar: avatarUrl.trim() || '',
            text: answer.value.trim(),
          };
          socket.send(JSON.stringify(answerData));
          answer.value = ''; // 清空输入框
        }
      }
    };

    // 提交选择题答案
    const submitMCQAnswer = () => {
      if (selectedOption.value !== null) {
        const answerData = {
          type: 'answer',
          name: name.trim(),
          avatar: avatarUrl.trim() || '',
          text: `选项 ${String.fromCharCode(65 + selectedOption.value)}`,
        };
        socket.send(JSON.stringify(answerData));
        selectedOption.value = null; // 清空选择
      }
    };

    // 选择选项
    const selectOption = (index) => {
      selectedOption.value = index;
    };

    // 清空已发送答案
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
