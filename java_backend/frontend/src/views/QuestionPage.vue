<template>
    <div class="container">
      <h1>出题端</h1>
  
      <!-- 连接状态 -->
      <ConnectionStatus :isConnected="isConnected" />

      <!-- 在线玩家展示 -->
      <OnlinePlayersQ :onlinePlayers="onlinePlayers" :currentMode="currentMode" />
    
      <!-- 模式选择和按钮 -->
      <ModeSelector :currentMode="currentMode" :updateModeCallback="updateMode" />
      
      <!-- 轮次更新 -->
      <RoundControls
        :totalRounds="totalRounds"
        :currentRound="currentRound"
        :updateCurrentRoundCallback="updateCurrentRound"
      />
      
      <!-- 分数或生命初始化 -->
      <ScoreLifeInitializer
        :currentMode="currentMode"
        :initializeScoresCallback="initializeScores"
        :initializeLivesCallback="initializeLives"
      />
  
      <!-- 玩家提交的答案区域 -->
      <div class="player-answers">
        <h2>玩家提交的答案</h2>
        <button @click="getLatestAnswers" class="primary-button">获取最新答案（会覆盖！）</button>
        <ul>
          <li v-for="(answer, index) in playerAnswers" :key="index">
            <p><strong>{{ answer.name }}</strong> 提交了: {{ answer.text }}</p>
            <span>时间戳: {{ answer.timestamp }}</span>

            <!-- 评分和判题功能 -->
            <template v-if="judgementResults[answer.playerId]">
              <span v-if="currentMode === 'scoring'">输入该玩家得分：</span>
              <input
                v-if="currentMode === 'scoring'"
                type="number"
                v-model="judgementResults[answer.playerId].score"
                placeholder="输入得分" />

              <span v-if="currentMode === 'survival'">输入该玩家丢失生命：</span>
              <input
                v-if="currentMode === 'survival'"
                type="number"
                v-model="judgementResults[answer.playerId].lostLives"
                placeholder="输入丢失生命" />
            </template>

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
  
    </div>
  </template>
  
  
  <script>
  import { ref, watch, onUnmounted, onMounted } from 'vue';
  import { useRoute } from 'vue-router';

  import ConnectionStatus from '../components/ConnectionStatus.vue';
  import OnlinePlayersQ from '../components/OnlinePlayersQ.vue';
  import ModeSelector from '../components/ModeSelector.vue';
  import RoundControls from '../components/RoundControls.vue';
  import ScoreLifeInitializer from '../components/ScoreLifeInitializer.vue';
  // import PlayerAnswers from '../components/PlayerAnswers.vue';

  export default {
    components: {
    ConnectionStatus,
    OnlinePlayersQ,
    ModeSelector,
    RoundControls,
    ScoreLifeInitializer,
    // PlayerAnswers,
    },
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
      const totalRounds = ref(0);
      const currentRound = ref(0);
      const initScores = ref(0);
      const initLives = ref(3);
      
      watch(currentRound, (newValue) => {
        console.log('Current Round changed to:', newValue);
      });

      watch(totalRounds, (newValue) => {
        console.log('Total Rounds changed to:', newValue);
      });

      const createSocketConnection = () => {
        if (socket.value) {
          socket.value.close(); // 关闭已有连接
        }
  
        if (!questionRoomId.value.trim()) {
          return; // 如果房间 ID 为空，则不创建连接
        }
  
        socket.value = new WebSocket(`${import.meta.env.VITE_WEBSOCKET_URL}/${questionRoomId.value}`);
  
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
            if (currentMode.value == 'none' && data.currentMode != 'none')
            currentMode.value = data.currentMode; // 更新在线玩家列表，含分数和生命信息
          } else if (data.type === 'round') {
            // 更新当前轮次和总轮次
            currentRound.value = data.currentRound;
            totalRounds.value = data.totalRounds;
            console.log(currentRound.value, totalRounds.value)
          } else if (data.type === 'latest_answers'){
            playerAnswers.value = data.latest_answers.map(answer => ({
            playerId: answer.id,
            name: answer.name,
            avatar: answer.avatar || avatarDefault,
            text: answer.submitted_answer,
            timestamp: answer.timestamp,
            }));
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
      
      const getLatestAnswers = () => {
        const requestData = {
          type: 'get_latest_answers',
          questionerId: playerId.value
        };
        socket.value.send(JSON.stringify(requestData));
      }

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
      
      const judgeAnswer = (playerId, isCorrect) => {
        console.log("In function judgeAnswer: playerId is:", playerId)
        if (!judgementResults.value[playerId]) {
          judgementResults.value[playerId] = { correct: isCorrect, score: 0, lostLives: 0 }; 
        }
        judgementResults.value[playerId].correct = isCorrect;
      };

      const initializeJudgement = (playerId) => {
        if (!judgementResults.value[playerId]) {
          judgementResults.value[playerId] = { score: 0, lostLives: 0, correct: false }; // 初始化对象
        }
      };
  
      // 提交判题结果
      const submitJudgement = () => {
        const judgementData = {
          type: 'judgement',
          results: judgementResults.value,
          currentRound: currentRound.value,  // 发送当前轮次信息
        };
        console.log(judgementResults.value);
        console.log(judgementData);
        socket.value.send(JSON.stringify(judgementData));
  
        // 清空答案和判题结果
        playerAnswers.value = [];
        judgementResults.value = {};
      };
  
      // 更新模式的方法
      const updateMode = (selectedMode) => {
        currentMode.value = selectedMode;  // 更新本地的模式状态

        const modeData = {
          type: 'mode_change',
          mode: selectedMode,
        };

        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
          socket.value.send(JSON.stringify(modeData));  // 发送模式更新
        }
      };
  
    // 子组件回调，用于更新轮次
    const updateCurrentRound = (newCurrentRound, newTotalRounds) => {
      currentRound.value = newCurrentRound;
      totalRounds.value = newTotalRounds;

      if (socket.value && socket.value.readyState === WebSocket.OPEN) {
        const roundData = {
          type: 'round_update',
          currentRound: currentRound.value,
          totalRounds: totalRounds.value,
        };
        socket.value.send(JSON.stringify(roundData));
      }
    };

    // 子组件回调，用于初始化分数
    const initializeScores = (score) => {
      initScores.value = score;
      const initData = {
        type: 'initialize_scores',
        score: initScores.value,
      };
      socket.value.send(JSON.stringify(initData)); 
    };

    // 子组件回调，用于初始化生命
    const initializeLives = (lives) => {
      initLives.value = lives;
      const initData = {
        type: 'initialize_lives',
        lives: initLives.value,
      };
      socket.value.send(JSON.stringify(initData));
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
        initializeJudgement,
        judgementResults,
        updateMode,
        totalRounds,
        currentRound,
        // updateTotalRounds,
        updateCurrentRound,
        initScores,
        initLives,
        initializeScores,
        initializeLives,
        // getJudgementScore,
        getLatestAnswers,
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
  