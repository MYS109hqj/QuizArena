<template>
  <div class="container">
    <h1>出题端</h1>

    <!-- 连接状态指示 -->
    <div :class="{'status-indicator': true, 'connected': isConnected, 'disconnected': !isConnected}">
      <span v-if="isConnected">🟢 Connected</span>
      <span v-else>🔴 Disconnected</span>
    </div>

    <!-- 在线玩家展示 -->
    <div v-if="onlinePlayers.length >= 0" class="online-players">
      <h2>在线玩家:</h2>
      <ul>
        <li v-for="(player, index) in onlinePlayers" :key="index">
          <img :src="player.avatar" alt="Avatar" class="avatar" />
          <strong>{{ player.name }}</strong>
        </li>
      </ul>
    </div>

    <!-- 题目类型选择 -->
    <div class="form-group">
      <label for="question-type">选择题目类型:</label>
      <select id="question-type" v-model="questionType" @change="resetFields">
        <option value="qa">问答题</option>
        <option value="mcq">选择题</option>
        <option value="hints">多提示题</option>
      </select>
    </div>

    <!-- 输入题目 -->
    <div class="form-group">
      <label for="question-input">题目:</label>
      <input id="question-input" v-model="question" placeholder="输入题目" />
    </div>

    <!-- 选择题选项输入 -->
    <div v-if="questionType === 'mcq'" class="form-group">
      <label>输入选项:</label>
      <input v-model="options[0]" placeholder="选项 A" />
      <input v-model="options[1]" placeholder="选项 B" />
      <input v-model="options[2]" placeholder="选项 C" />
      <input v-model="options[3]" placeholder="选项 D" />
    </div>

    <!-- 多提示题输入 -->
    <div v-if="questionType === 'hints'" class="form-group">
      <label for="basic-hint">基本提示:</label>
      <input id="basic-hint" v-model="basicHint" placeholder="输入基本提示" />
      <label>追加提示:</label>
      <input v-model="additionalHints[0]" placeholder="追加提示 1" />
      <input v-model="additionalHints[1]" placeholder="追加提示 2" />
      <input v-model="additionalHints[2]" placeholder="追加提示 3" />
      <input v-model="additionalHints[3]" placeholder="追加提示 4" />
    </div>

    <!-- 房间 ID 输入 -->
    <div class="form-group">
      <label for="room-id">房间 ID:</label>
      <input id="room-id" v-model="questionRoomId" placeholder="输入房间 ID" />
    </div>

    <!-- 功能按钮 -->
    <div class="button-group">
      <button @click="sendQuestion" :disabled="!isConnected" class="primary-button">发送题目</button>
      <button @click="clearQuestion" class="secondary-button">清空问题</button>
      <button @click="clearAnswers" class="secondary-button">清空答案</button>
    </div>

    <!-- 收到的答案展示 -->
    <div v-if="answers.length >= 0" class="answers-section">
      <h2>收到的答案:</h2>
      <ul>
        <li v-for="(answer, index) in answers" :key="index" class="answer-item">
          <img :src="answer.avatar" alt="Avatar" class="avatar" />
          <p><strong>{{ answer.name }}</strong>: {{ answer.text }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { ref, watch, onUnmounted, onMounted } from 'vue';
import { useRoute } from 'vue-router';

export default {
  setup() {
    const route = useRoute();
    const question = ref('');
    const questionRoomId = ref('');
    const questionType = ref('qa');
    const options = ref(['', '', '', '']);
    const basicHint = ref('');
    const additionalHints = ref(['', '', '', '']);
    const answers = ref([]);
    const onlinePlayers = ref([]);
    const socket = ref(null);
    const isConnected = ref(false);
    const userId = generateUniqueId('user');
    const avatarDefault = "https://i0.hippopx.com/photos/490/240/938/connect-connection-cooperation-hands-thumb.jpg".trim();

    function generateUniqueId(type) {
      return `${type}-${Math.random().toString(36).substr(2, 9)}-${Date.now()}`;
    }

    const createSocketConnection = () => {
      if (socket.value) {
        socket.value.close(); // 关闭已有连接
      }

      if (!questionRoomId.value.trim()) {
        return; // 如果房间 ID 为空，则不创建连接
      }

      socket.value = new WebSocket(`ws://localhost:8000/ws/${questionRoomId.value}`);

      socket.value.onopen = () => {
        console.log('WebSocket connection opened');

        if (socket.value) {
          const joinData = {
            id: userId,
            type: 'join',
            name: "提问者",
            avatar: avatarDefault || '',
          };
          socket.value.send(JSON.stringify(joinData)); // 发送玩家信息
          isConnected.value = true;
        } else {
          console.error('Socket is not initialized properly');
        }
      };

      socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // 处理不同类型消息
        if (data.type === 'question') {
          // 接收到新题目
          // question.value = data.content; // 更新当前题目
          // answers.value = []; // 清空答案列表
        } else if (data.type === 'answer') {
          answers.value.push(data);
        } else if (data.type === 'player_list') {
          onlinePlayers.value = data.players; // 更新在线玩家列表
        }
      };

      socket.value.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.value.onclose = () => {
        console.log('WebSocket connection closed');
        isConnected.value = false;
      };
    };

    watch(questionRoomId, (newRoomId) => {
      if (newRoomId.trim()) {
        createSocketConnection();
      }
    });

    const sendQuestion = () => {
      if (isConnected.value) {
        let questionData = { type: 'question', questionId: generateUniqueId('question') };

        if (questionType.value === 'qa') {
          questionData.content = { type: 'qa', question: question.value };
        } else if (questionType.value === 'mcq') {
          questionData.content = { type: 'mcq', question: question.value, options: options.value };
        } else if (questionType.value === 'hints') {
          questionData.content = { type: 'hints', question: question.value, basicHint: basicHint.value, additionalHints: additionalHints.value };
        }

        console.log('Sending question:', questionData);
        socket.value.send(JSON.stringify(questionData));
      }
    };

    const clearQuestion = () => {
      question.value = '';
      options.value = ['', '', '', ''];
      basicHint.value = '';
      additionalHints.value = ['', '', '', ''];
    };

    const clearAnswers = () => {
      answers.value = [];
    };

    onMounted(() => {
      questionRoomId.value = route.params.roomId;
    });

    onUnmounted(() => {
      if (socket.value) {
        socket.value.close();
      }
    });

    return {
      question,
      questionRoomId,
      questionType,
      options,
      basicHint,
      additionalHints,
      sendQuestion,
      clearQuestion,
      clearAnswers,
      answers,
      isConnected,
      onlinePlayers,
    };
  }
};
</script>

<style scoped>
.container {
  width: 80%;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

.status-indicator {
  text-align: center;
  font-size: 1.2em;
  margin-bottom: 20px;
}

.connected {
  color: green;
}

.disconnected {
  color: grey;
}

.online-players {
  margin-bottom: 20px;
}

.online-players ul {
  list-style-type: none;
  padding: 0;
}

.online-players li {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.online-players .avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

input, select {
  width: 100%;
  padding: 10px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box;
}

input::placeholder {
  color: #999;
}

.button-group {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
}

.primary-button, .secondary-button {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 1em;
  cursor: pointer;
}

.primary-button {
  background-color: #4CAF50;
  color: white;
}

.primary-button:disabled {
  background-color: #ccc;
}

.secondary-button {
  background-color: #f0f0f0;
  color: #333;
}

.secondary-button:hover {
  background-color: #ddd;
}

.answers-section {
  margin-top: 30px;
}

.answers-section ul {
  list-style-type: none;
  padding: 0;
}

.answer-item {
  background-color: white;
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 10px;
  box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}

.answer-item p {
  margin-left: 15px;
  font-size: 1em;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}
</style>
