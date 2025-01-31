<template>
  <div class="container">
    <h1>答题端</h1>

    <!-- 连接状态 -->
    <ConnectionStatus :isConnected="isConnected" />

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
          <!-- 判题结果展示 -->
          <JudgementResults 
            v-if="judgementResults" 
            :results="judgementResults" 
            :currentMode="currentMode" 
            :round="judgementResultsRound"
            :correctAnswer="correct_answer"
            :explanation="explanation"
          />
          <FinalResults 
            v-if="isFinalResultsVisible" 
            :players="finalResultsData" 
            :currentMode="currentMode" 
            @close="closeFinalResults" 
          />
      </div>

      <div class="sidebar">
        <OnlinePlayersA 
          :onlinePlayers="players" 
          :currentMode="currentMode" 
          :currentRound="currentRound" 
          :totalRounds="totalRounds" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRoute } from 'vue-router';

import ConnectionStatus from '../components/ConnectionStatus.vue';
import OnlinePlayersA from '../components/OnlinePlayersA.vue';
import JudgementResults from '../components/JudgementResults.vue';
import FinalResults from '@/components/FinalResults.vue';

export default {
  components: {
    ConnectionStatus,
    OnlinePlayersA,
    JudgementResults,
    FinalResults,
  },
  setup() {
    const route = useRoute();
    const socket = new WebSocket(`${import.meta.env.VITE_WEBSOCKET_URL}/${route.params.roomId}`);
    const name = route.query.name || 'your name';
    const avatarUrl = route.query.avatarUrl || '';
    const userId = route.query.playerId || generateUniqueId();  // 从路由查询参数中获取 playerId 或生成新的 ID
    const receivedQuestion = ref(null);
    const answer = ref('');
    const correct_answer = ref('');
    const explanation = ref('');
    const answers = ref([]);
    const selectedOption = ref(null);
    const players = ref([]);
    const isConnected = ref(false);
    const questionerConnected = ref(false);  // 提问者连接状态
    const currentMode = ref('none');  // 当前模式
    const playerScore = ref(0);  // 玩家得分
    const playerLives = ref(3);  // 玩家生命值（生存模式）
    const currentRound = ref(1);  // 初始化当前轮次
    const totalRounds = ref(1);   // 初始化总轮次
    const awaitingJudgement = ref(false);  // 等待判题状态
    const judgementResults = ref(null);  // 判题结果
    const judgementResultsRound = ref(0);
    const finalResultsData = ref(null);
    const isFinalResultsVisible = ref(false);  // 控制结算窗口显示

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
        awaitingJudgement.value = false;  
        judgementResults.value = data.results; 
        judgementResultsRound.value = data.round;
        correct_answer.value = data.correct_answer;  // 存储正确答案
        explanation.value = data.explanation;  // 存储解析
      } else if (data.type === 'mode_change') {
        currentMode.value = data.currentMode;  // 更新当前模式
      } else if (data.type === 'round') {
        // 更新当前轮次和总轮次
        currentRound.value = data.currentRound;
        totalRounds.value = data.totalRounds;
      } else if (data.type === 'congratulations_complete') {
        finalResultsData.value = data.results; // 服务器返回的最终分数或生命值数据
        isFinalResultsVisible.value = true;  // 显示结算窗口
      }
    };

    // WebSocket 打开时发送用户信息
    socket.onopen = () => {
      console.log('连接建立:', { name, avatarUrl, roomId: route.params.roomId });
      isConnected.value = true;
      const joinData = {
        id: userId,  // 使用从 URL 查询参数传入的 playerId
        type: 'join',
        name: name.trim(),
        avatar: avatarUrl.trim() || '',
      };
      socket.send(JSON.stringify(joinData));
    };

    socket.onclose = () => {
          console.log('WebSocket connection closed');
          isConnected.value = false;
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

    // 关闭结算窗口
    const closeFinalResults = () => {
      isFinalResultsVisible.value = false;
    };

    return {
      name,
      avatarUrl,
      receivedQuestion,
      answer,
      answers,
      correct_answer,
      explanation,
      sendAnswer,
      submitMCQAnswer,
      selectOption,
      clearAnswers,
      selectedOption,
      players,
      isConnected,
      questionerConnected,
      currentMode,
      playerScore,
      playerLives,
      currentRound,
      totalRounds,
      awaitingJudgement,
      judgementResults,
      judgementResultsRound,
      FinalResults,
      finalResultsData,
      isFinalResultsVisible,
      closeFinalResults,
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
