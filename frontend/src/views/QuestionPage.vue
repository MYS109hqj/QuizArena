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
            <!-- 根据模式显示得分或生命 -->
            <template v-if="currentMode === 'scoring'">
              <span> - 分数: {{ player.score }}</span>
            </template>
            <template v-else-if="currentMode === 'survival'">
              <span> - 生命: {{ player.lives }}</span>
            </template>
          </li>
        </ul>
      </div>
  
      <!-- 模式选择和按钮 -->
      <div class="form-group mode-update">
        <label for="mode-selection">选择模式:</label>
        <select id="mode-selection" v-model="currentMode">
          <option value="none">无模式</option>
          <option value="scoring">计分模式</option>
          <option value="survival">生存模式</option>
        </select>
        <button @click="updateMode" class="update-button">更新房间模式</button>
      </div>
  
      <!-- 新增：展示当前轮次和总轮次 -->
      <div class="round-info">
        <h3>轮次信息</h3>
        <p>当前轮次: {{ currentRound }} / {{ totalRounds }}</p>
      </div>
  
      <!-- 新增：设置总轮次和当前轮次 -->
      <div class="round-controls">
        <label for="total-rounds">设置总轮次:</label>
        <input type="number" v-model="totalRounds" id="total-rounds">
        <button @click="updateTotalRounds">更新总轮次</button>
  
        <label for="current-round">设置当前轮次:</label>
        <input type="number" v-model="currentRound" id="current-round">
        <button @click="updateCurrentRound">更新当前轮次</button>
      </div>
  
      <!-- 显示模式并初始化分数或生命 -->
      <div v-if="currentMode === 'scoring'">
        <span> - 分数: {{ player.score }}</span>
        <label for="init-scores">初始化分数:</label>
        <input type="number" v-model="initScores">
        <button @click="initializeScores">初始化分数</button>
      </div>
  
      <div v-else-if="currentMode === 'survival'">
        <span> - 生命: {{ player.lives }}</span>
        <label for="init-lives">初始化生命:</label>
        <input type="number" v-model="initLives">
        <button @click="initializeLives">初始化生命</button>
      </div>
  
      <div class="player-answers">
        <h2>玩家提交的答案</h2>
        <ul>
          <li v-for="(answer, index) in playerAnswers" :key="index">
            <p><strong>{{ answer.name }}</strong> 提交了: {{ answer.text }}</p>
            <input v-model="judgementResults[answer.playerId].score" placeholder="分数">
            <button @click="judgeAnswer(answer.playerId, true)">正确</button>
            <button @click="judgeAnswer(answer.playerId, false)">错误</button>
          </li>
        </ul>
        <button @click="submitJudgement">提交判题结果</button>
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
  
      <!-- 玩家提交的答案区域，添加分值输入框 -->
      <div class="player-answers">
        <h2>玩家提交的答案</h2>
        <ul>
          <li v-for="(answer, index) in playerAnswers" :key="index">
            <p><strong>{{ answer.name }}</strong> 提交了: {{ answer.text }}</p>
            <input v-if="currentMode == 'scoring'" type="number" v-model="judgementResults[answer.playerId].score" placeholder="输入得分" />
            <input v-else-if="currentMode == 'survival'" type="number" v-model="judgementResults[answer.playerId].lostLives" placeholder="输入丢失生命" />
            <button @click="judgeAnswer(answer.playerId, true)">正确</button>
            <button @click="judgeAnswer(answer.playerId, false)">错误</button>
          </li>
        </ul>
        <button @click="submitJudgement">提交判题结果</button>
      </div>
  
    </div>
  </template>
  
  
  <script>
  import { ref, watch, onUnmounted, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  
  export default {
    setup() {
      const route = useRoute();
      const questionRoomId = ref(route.params.roomId); // 从路由参数获取房间ID
      const playerId = ref(route.query.playerId); // 获取 playerId 查询参数
      const question = ref('');
      const questionType = ref('qa');
      const currentMode = ref('none'); // 模式选择，默认无模式
      const options = ref(['', '', '', '']);
      const basicHint = ref('');
      const additionalHints = ref(['', '', '', '']);
      const answers = ref([]);
      const onlinePlayers = ref([]);
      const socket = ref(null);
      const isConnected = ref(false);
      const avatarDefault = "https://i0.hippopx.com/photos/490/240/938/connect-connection-cooperation-hands-thumb.jpg".trim();
      const playerAnswers = ref([]);
      const judgementResults = ref({});
      const totalRounds = ref('');
      const currentRound = ref('');
      const initScores = ref(0);
      const initLives = ref(3);
  
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
              id: playerId.value || generateUniqueId('questioner'), // 使用传入的 playerId
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
            question.value = data.content.question; // 更新当前题目
            questionType.value = data.content.type; // 更新题目类型
            if (data.content.type === 'mcq') {
              options.value = data.content.options || ['', '', '', '']; // 更新选择题的选项
            } else if (data.content.type === 'hints') {
              basicHint.value = data.content.basicHint || ''; // 更新基本提示
              additionalHints.value = data.content.additionalHints || ['', '', '', '']; // 更新追加提示
            }
          } else if (data.type === 'answer') {
            answers.value.push(data);
            playerAnswers.value.push(data);  // 收到玩家答案
          } else if (data.type === 'player_list') {
            onlinePlayers.value = data.players; // 更新在线玩家列表，含分数和生命信息
          } else if (data.type === 'mode_change') {
            if (currentMode.value == None && data.currentMode != None)
            currentMode.value = data.currentMode; // 更新在线玩家列表，含分数和生命信息
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
  
      const sendQuestion = () => {
        const questionData = {
          type: 'question',
          content: {
            question: question.value,
            type: questionType.value,
            options: questionType.value === 'mcq' ? options.value : null,
            basicHint: questionType.value === 'hints' ? basicHint.value : null,
            additionalHints: questionType.value === 'hints' ? additionalHints.value : null
          },
          questionId: generateUniqueId('question')
        };
        socket.value.send(JSON.stringify(questionData));
      };
  
      // 提问者判定答案正确与否，以及模式相关的内容
      const judgeAnswer = (playerId, isCorrect) => {
        if (!judgementResults.value[playerId]) {
          // 初始化每个玩家的结果对象
          judgementResults.value[playerId] = { correct: isCorrect, score: 0, lostLives: 0 }; 
        }
        // 设置判题正确与否
        judgementResults.value[playerId].correct = isCorrect;
        
        // 根据当前模式设置得分或丢失的生命数
        if (currentMode.value === 'scoring') {
          // 如果是计分模式，默认初始化分数为 0
          judgementResults.value[playerId].score = judgementResults.value[playerId].score || 0;
        } else if (currentMode.value === 'survival') {
          // 如果是生存模式，默认初始化丢失的生命为 0
          judgementResults.value[playerId].lostLives = judgementResults.value[playerId].lostLives || 0;
        }
      };
  
  
      // 提交判题结果
      const submitJudgement = () => {
        const judgementData = {
          type: 'judgement',
          results: judgementResults.value,
          currentRound: currentRound.value,  // 发送当前轮次信息
        };
        socket.value.send(JSON.stringify(judgementData));
  
        // 清空答案和判题结果
        playerAnswers.value = [];
        judgementResults.value = {};
      };
  
      // 更新模式的方法
      const updateMode = () => {
        const modeData = {
          type: 'mode_change',
          mode: currentMode.value,
        };
        // socket.value.send(JSON.stringify(modeData));
        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
          socket.value.send(JSON.stringify(modeData));
        }
      };
  
      // 设置更新轮次
      const updateTotalRounds = () => {
        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
          const roundData = {
            type: 'update_rounds',
            totalRounds: totalRounds.value,
          };
          socket.value.send(JSON.stringify(roundData));
        }
      };
  
      const updateCurrentRound = () => {
        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
          const roundData = {
            type: 'update_rounds',
            currentRound: currentRound.value,
          };
          socket.value.send(JSON.stringify(roundData));
        }
      };
  
      const initializeScores = () => {
        // 发送初始化分数的消息
        const initData = {
          type: 'initialize_scores',
          score: initScores.value, // 从输入框获取的分数
        };
        socket.value.send(JSON.stringify(initData)); // 发送初始化分数的请求
      };
  
      const initializeLives = () => {
        // 发送初始化生命的消息
        const initData = {
          type: 'initialize_lives',
          lives: initLives.value, // 从输入框获取的生命值
        };
        socket.value.send(JSON.stringify(initData)); // 发送初始化生命的请求
      };
  
      const generateUniqueId = (prefix) => {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
      };
  
      const resetFields = () => {
        question.value = '';
        options.value = ['', '', '', ''];
        basicHint.value = '';
        additionalHints.value = ['', '', '', ''];
      };
  
      const clearQuestion = () => {
        question.value = '';
      };
  
      const clearAnswers = () => {
        answers.value = [];
      };
  
      watch(questionRoomId, (newRoomId) => {
        if (newRoomId.trim()) {
          createSocketConnection();
        }
      });
  
      onMounted(() => {
        createSocketConnection(); // 启动时创建WebSocket连接
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
        currentMode,
        options,
        basicHint,
        additionalHints,
        answers,
        resetFields,
        isConnected,
        onlinePlayers,
        sendQuestion,
        clearQuestion,
        clearAnswers,
        playerAnswers,
        judgeAnswer,
        submitJudgement,
        updateMode,
        updateTotalRounds,
        updateCurrentRound,
        initializeScores,
        initializeLives,
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
  
  .mode-update {
    display: flex;
    align-items: center; /* 垂直居中对齐 */
  }
  
  .update-button {
    margin-left: 10px; /* 按钮与选择框之间的间距 */
  }
  
  .button-group {
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
  