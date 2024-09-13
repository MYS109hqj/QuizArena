<template>
  <div>
    <h1>出题端</h1>
    <div :class="{'status-indicator': true, 'connected': isConnected, 'disconnected': !isConnected}">
      <span v-if="isConnected">🟢 Connected</span>
      <span v-else>🔴 Disconnected</span>
    </div>

    <select v-model="questionType" @change="resetFields">
      <option value="qa">问答题</option>
      <option value="mcq">选择题</option>
      <option value="hints">多提示题</option>
    </select>

    <input v-model="question" placeholder="输入题目" />
    <div v-if="questionType === 'mcq'">
      <input v-model="options[0]" placeholder="选项 A" />
      <input v-model="options[1]" placeholder="选项 B" />
      <input v-model="options[2]" placeholder="选项 C" />
      <input v-model="options[3]" placeholder="选项 D" />
    </div>
    <div v-if="questionType === 'hints'">
      <input v-model="basicHint" placeholder="基本提示" />
      <input v-model="additionalHints[0]" placeholder="追加提示词 1" />
      <input v-model="additionalHints[1]" placeholder="追加提示词 2" />
      <input v-model="additionalHints[2]" placeholder="追加提示词 3" />
      <input v-model="additionalHints[3]" placeholder="追加提示词 4" />
    </div>
    
    <input v-model="questionRoomId" placeholder="输入房间 ID" />
    <button @click="sendQuestion" :disabled="!isConnected">发送题目</button>
    <button @click="clearQuestion">清空问题</button>
    <button @click="clearAnswers">清空答案</button>

    <div v-if="answers.length > 0">
      <h2>收到的答案:</h2>
      <ul>
        <li v-for="(answer, index) in answers" :key="index">
          <img :src="answer.avatar" alt="Avatar" class="avatar" />
          <p><strong>{{ answer.name }}</strong>: {{ answer.text }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { ref, watch, onUnmounted } from 'vue';

export default {
  setup() {
    const question = ref('');
    const questionRoomId = ref('');
    const questionType = ref('qa');
    const options = ref(['', '', '', '']);
    const basicHint = ref('');
    const additionalHints = ref(['', '', '', '']);
    const answers = ref([]);
    const socket = ref(null);
    const isConnected = ref(false);

    // 创建或更新 WebSocket 连接
    const createSocketConnection = () => {
      if (socket.value) {
        socket.value.close();
      }
      
      if (!questionRoomId.value.trim()) {
        return;
      }

      socket.value = new WebSocket(`ws://localhost:8000/ws/${questionRoomId.value}`);
      
      socket.value.onopen = () => {
        console.log('WebSocket connection opened');
        isConnected.value = true;
      };

      socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'answer') {
          answers.value.push(data);
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

    // 监听房间 ID 变化
    watch(questionRoomId, (newRoomId) => {
      if (newRoomId.trim()) {
        createSocketConnection();
      }
    });

    // 发送问题
    const sendQuestion = () => {
      if (isConnected.value) {
        let questionData = { type: 'question' };
        
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

    // 清空问题字段
    const clearQuestion = () => {
      question.value = '';
      if (questionType.value === 'mcq') {
        options.value = ['', '', '', ''];
      } else if (questionType.value === 'hints') {
        basicHint.value = '';
        additionalHints.value = ['', '', '', ''];
      }
    };

    // 清空答案字段
    const clearAnswers = () => {
      answers.value = [];
    };

    // 清理 WebSocket 连接
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
      isConnected
    };
  }
};
</script>


<style scoped>
.status-indicator {
  margin-bottom: 10px;
  font-size: 1.2em;
}
.connected {
  color: green;
}
.disconnected {
  color: grey;
}
.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}
</style>
