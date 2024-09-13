<template>
  <div>
    <h1>答题端</h1>

    <!-- 显示调试信息 -->
    <div v-if="debug">
      <h2>Debug Info:</h2>
      <p>Name: {{ name }}</p>
      <p>Avatar URL: {{ avatarUrl }}</p>
      <p>received question: {{ receivedQuestion }}</p>
      <p>debug: {{ receivedQuestion.value }}</p>
    </div>

    <!-- 显示用户信息 -->
    <div v-if="name">
      <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="avatar" />
      <p>姓名: {{ name }}</p>
    </div>

    <!-- 根据问题类型显示题目 -->
    <div v-if="receivedQuestion && receivedQuestion.content.type == 'qa'">
      <p>题目: {{ receivedQuestion.content.question }}</p>
      <input v-model="answer" placeholder="输入答案" />
      <button @click="sendAnswer">提交答案</button>
    </div>

    <div v-if="receivedQuestion && receivedQuestion.content.type == 'mcq'">
      <p>题目: {{ receivedQuestion.content.question }}</p>
      <div v-for="(option, index) in receivedQuestion.content.options" :key="index">
        <button 
          :class="{ selected: selectedOption === index }" 
          @click="selectOption(index)">
          {{ String.fromCharCode(65 + index) }}. {{ option }}
        </button>
      </div>
      <button @click="submitMCQAnswer" :disabled="selectedOption === null">提交答案</button>
    </div>

    <div v-if="receivedQuestion && receivedQuestion.content.type == 'hints'">
      <p>题目: {{ receivedQuestion.content.question }}</p>
      <p>基本提示: {{ receivedQuestion.content.basicHint }}</p>
      <ul>
        <li v-for="(hint, index) in receivedQuestion.content.additionalHints" :key="index">
          追加提示词 {{ index + 1 }}: {{ hint }}
        </li>
      </ul>
      <input v-model="answer" placeholder="输入答案" />
      <button @click="sendAnswer">提交答案</button>
    </div>

    <!-- 清空问题和答案记录的按钮 -->
    <!-- <button @click="resetFields">清空问题</button> -->
    <button @click="clearAnswers">清空答案</button>

    <!-- 显示已发送的答案 -->
    <div v-if="answers.length > 0">
      <h2>已发送的答案:</h2>
      <ul>
        <li v-for="(ans, index) in answers" :key="index">
          <img v-if="ans.avatar" :src="ans.avatar" alt="Avatar" class="avatar" />
          <p><strong>{{ ans.name }}</strong>: {{ ans.text }}</p>
        </li>
      </ul>
    </div>

    <!-- debug div: 仅在 debug 为 true 时显示 -->
    <div v-if="debug">
      <h2>Debug Messages</h2>
      <ul>
        <li v-for="(msg, index) in debugMessages" :key="index">{{ msg }}</li>
      </ul>
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
    let receivedQuestion = ref({ type: '', content: { question: '', options: [], basicHint: '', additionalHints: [] } });
    const answer = ref('');
    const answers = ref([]);
    const debugMessages = ref([]);
    const debug = ref(false);
    const selectedOption = ref(null);

    // 处理 WebSocket 消息
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Message received:', data);

      debugMessages.value.push(event.data);

      if (data.type === 'question') {
        receivedQuestion.value = data;
        answers.value = [];
      } else if (data.type === 'answer') {
        answers.value.push(data);
      }
      console.log("debug0:" + receivedQuestion.value)
      console.log("debug1:" + receivedQuestion.value.type);
      console.log("debug2:" + receivedQuestion.value.content);
      if (receivedQuestion.value.content)
        console.log("true");
      else
        console.log("false");
      console.log("debug3:" + receivedQuestion.value.content.type);
      console.log("debug4:" + receivedQuestion.value.content.question);
    };

    // 发送答案到 WebSocket
    const sendAnswer = () => {
      if (socket.readyState === WebSocket.OPEN) {
        if (answer.value.trim() !== '' && name.trim() !== '') {
          const answerData = {
            type: 'answer',
            name: name.trim(),
            avatar: avatarUrl.trim() || '',
            text: answer.value.trim(),
          };
          console.log('Sending answer:', answerData);
          socket.send(JSON.stringify(answerData));
          answer.value = '';
        } else {
          console.warn('Name or answer is empty.');
        }
      } else {
        console.error('WebSocket is not open.');
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
        console.log('Sending answer:', answerData);
        socket.send(JSON.stringify(answerData));
        selectedOption.value = null; // 清空选择
      } else {
        console.warn('No option selected.');
      }
    };

    // 选择选项
    const selectOption = (index) => {
      selectedOption.value = index;
    };

    // 清空题目和答案记录
    const resetFields = () => {
      answer.value = '';
      selectedOption.value = null;
      if (receivedQuestion.value.content.type === 'mcq') {
        // 不重置选项，因为选择题的选项是静态的
      } else if (receivedQuestion.value.content.type === 'hints') {
        // 处理提示问题的重置
      }
    };

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
      resetFields,
      clearAnswers,
      debug,
      debugMessages,
      selectedOption,
    };
  }
};
</script>

<style scoped>
.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

button.selected {
  background-color: #007bff;
  color: white;
}
</style>
