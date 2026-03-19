<template>
  <div class="game-container">
    <h1>隐藏墙壁迷宫游戏</h1>
    
    <div class="game-info">
      <div class="info-row">
        <span>时间：</span><span>{{ formattedTime }}</span>
        <span style="margin-left: 20px;">步数：</span><span>{{ gameState.steps }}</span>
      </div>
    </div>

    <div class="maze-container">
      <div class="maze-grid" :style="{ gridTemplateColumns: `repeat(${mazeData.rownum || 8}, 50px)`, gridTemplateRows: `repeat(${mazeData.rownum || 8}, 50px)` }">
        <div
          v-for="(cell, index) in totalCells"
          :key="index"
          class="maze-cell"
          :class="getCellClass(index)"
          :data-index="index"
        >
          <!-- 起点标记 -->
          <div v-if="index === gameState.startPosition" class="start-point">START</div>
          
          <!-- 终点标记 -->
          <div v-if="index === gameState.endPosition" class="end-point">FINISH</div>
          
          <!-- 玩家 -->
          <div v-if="index === gameState.currentPosition" class="player"></div>
          
          <!-- 墙壁显示 -->
          <div v-if="gameState.showWalls && mazeDataState.wall && mazeDataState.wall[index] && mazeDataState.wall[index][0] === 1" class="wall-top"></div>
          <div v-if="gameState.showWalls && mazeDataState.wall && mazeDataState.wall[index] && mazeDataState.wall[index][1] === 1" class="wall-left"></div>
          <div v-if="gameState.showWalls && mazeDataState.wall && mazeDataState.wall[index] && mazeDataState.wall[index][2] === 1" class="wall-right"></div>
          <div v-if="gameState.showWalls && mazeDataState.wall && mazeDataState.wall[index] && mazeDataState.wall[index][3] === 1" class="wall-bottom"></div>
          
          <!-- 撞过的墙显示 -->
          <div v-if="showCollidedWalls && getWallCollision(index, 'top')" class="collided-wall-top"></div>
          <div v-if="showCollidedWalls && getWallCollision(index, 'left')" class="collided-wall-left"></div>
          <div v-if="showCollidedWalls && getWallCollision(index, 'right')" class="collided-wall-right"></div>
          <div v-if="showCollidedWalls && getWallCollision(index, 'bottom')" class="collided-wall-bottom"></div>
        </div>
      </div>
    </div>

    <div class="controls">
      <div class="control-buttons">
        <button class="btn-up" @click="movePlayer('up')" :disabled="!gameState.gameStarted">↑</button>
        <button class="btn-left" @click="movePlayer('left')" :disabled="!gameState.gameStarted">←</button>
        <button class="btn-right" @click="movePlayer('right')" :disabled="!gameState.gameStarted">→</button>
        <button class="btn-down" @click="movePlayer('down')" :disabled="!gameState.gameStarted">↓</button>
      </div>
      
      <div class="options-container">
        <div class="options">
          <input type="checkbox" id="wallCollisionReset" v-model="wallCollisionReset" />
          <label for="wallCollisionReset">撞墙返回起点</label>
        </div>
        <div class="options">
          <input type="checkbox" id="showCollidedWalls" v-model="showCollidedWalls" />
          <label for="showCollidedWalls">显示撞过多次的墙</label>
        </div>
        
        <div class="action-buttons">
          <button id="giveUpBtn" @click="giveUpGame" :disabled="!gameState.gameStarted">放弃</button>
          <button id="restartBtn" @click="restartGame">重新开始</button>
          <button @click="backToList" style="margin-left: 10px;">返回列表</button>
        </div>
      </div>
    </div>

    <div class="keyboard-hint">
      <p>使用键盘 WASD 或方向键移动</p>
    </div>

    <!-- 成功消息弹窗 -->
    <div class="success-message" v-if="showSuccessMessage">
      <h2>恭喜通关！</h2>
      <p>耗时：<span>{{ formattedTime }}</span></p>
      <p>步数：<span>{{ gameState.steps }}</span></p>
      <button @click="restartGame">重新开始</button>
        <button @click="goToNextMaze" style="margin-left: 10px;">下一个迷宫</button>
        <button @click="backToList" style="margin-left: 10px;">返回列表</button>
    </div>
    
    <!-- 自定义弹窗 -->
    <div class="custom-alert" v-if="showCustomAlert">
      <div class="custom-alert-content">
        <p>{{ alertMessage }}</p>
        <button @click="closeCustomAlert">确定</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SimpleMazeDecoder } from './decodeMaze';
import mazeData from './mazes.json';

// 路由
const route = useRoute();
const router = useRouter();

// Props
const props = defineProps({
  mazeId: {
    type: String,
    default: '1'
  }
});

// 响应式数据
const mazeDataState = ref({});
const gameState = reactive({
  currentPosition: 56,
  steps: 0,
  startTime: 0,
  endTime: 0,
  timer: null,
  showWalls: false,
  gameStarted: false,
  startPosition: 56,
  endPosition: 7
});
const wallCollisionReset = ref(true);
const showCollidedWalls = ref(false);
const showSuccessMessage = ref(false);
const showCustomAlert = ref(false);
const alertMessage = ref('');
const wallRecordRow = ref([]);
const wallRecordColumn = ref([]);
const decoder = ref(new SimpleMazeDecoder());
const currentTime = ref(Date.now());

// 计算属性
const totalCells = computed(() => {
  const rows = mazeDataState.value.rownum || 8;
  return rows * rows;
});

const formattedTime = computed(() => {
  if (!gameState.startTime) return '00:00';
  
  const endTime = gameState.endTime || currentTime.value;
  const elapsedTime = Math.floor((endTime - gameState.startTime) / 1000);
  const minutes = Math.floor(elapsedTime / 60).toString().padStart(2, '0');
  const seconds = (elapsedTime % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
});

// 方法
function getCellClass(index) {
  const rows = mazeDataState.value.rownum || 8;
  const row = Math.floor(index / rows);
  const col = index % rows;
  
  // 交替颜色
  return row % 2 === 0 ? (col % 2 === 0 ? 'even-row-even-col' : 'even-row-odd-col') : (col % 2 === 0 ? 'odd-row-even-col' : 'odd-row-odd-col');
}

function getWallCollision(index, direction) {
  const rows = mazeDataState.value.rownum || 8;
  const row = Math.floor(index / rows);
  const col = index % rows;
  
  switch (direction) {
    case 'top':
      return row > 0 && wallRecordRow.value[row - 1] && wallRecordRow.value[row - 1][col] >= 2;
    case 'left':
      return col > 0 && wallRecordColumn.value[row] && wallRecordColumn.value[row][col - 1] >= 2;
    case 'right':
      return col < rows - 1 && wallRecordColumn.value[row] && wallRecordColumn.value[row][col] >= 2;
    case 'bottom':
      return row < rows - 1 && wallRecordRow.value[row] && wallRecordRow.value[row][col] >= 2;
    default:
      return false;
  }
}

async function initGame(id) {
  try {
    // 获取迷宫数据
    const mazeInfo = mazeData[id];
    if (!mazeInfo) {
      throw new Error('迷宫数据不存在');
    }
    
    // 解码迷宫数据
    const encodedBytes = decoder.value.hexToBytes(mazeInfo.compressed);
    mazeDataState.value = decoder.value.decode(encodedBytes);
    
    // 初始化游戏状态
    gameState.steps = 0;
    gameState.startPosition = mazeDataState.value.greenIndex;
    gameState.endPosition = 7; // 设置终点为右上角位置（索引7）
    gameState.currentPosition = mazeDataState.value.greenIndex;
    gameState.showWalls = false;
    gameState.endTime = 0;
    
    // 初始化撞墙记录
    const rows = mazeDataState.value.rownum;
    wallRecordRow.value = Array(rows - 1).fill().map(() => Array(rows).fill(0));
    wallRecordColumn.value = Array(rows).fill().map(() => Array(rows - 1).fill(0));
    
    // 隐藏弹窗
    showSuccessMessage.value = false;
    showCollidedWalls.value = false;
    
    // 开始游戏
    startGame();
  } catch (error) {
    console.error('初始化游戏失败:', error);
    showCustomAlert.value = true;
    alertMessage.value = '迷宫加载失败，请重试！';
  }
}

function startGame() {
  gameState.gameStarted = true;
  gameState.startTime = Date.now();
  currentTime.value = Date.now();
  
  // 启动计时器
  gameState.timer = setInterval(() => {
    currentTime.value = Date.now();
  }, 1000);
}

function isValidMove(from, direction) {
  if (!mazeDataState.value.wall || !Array.isArray(mazeDataState.value.wall) || !mazeDataState.value.wall[from]) {
    return { valid: false };
  }
  
  const walls = mazeDataState.value.wall[from]; // [上, 左, 右, 下]
  const rows = mazeDataState.value.rownum || 8;
  let to = from;
  
  switch (direction) {
    case 'up':
      if (walls[0] === 1) return { valid: false };
      to = from - rows;
      break;
    case 'left':
      if (walls[1] === 1) return { valid: false };
      to = from - 1;
      break;
    case 'right':
      if (walls[2] === 1) return { valid: false };
      to = from + 1;
      break;
    case 'down':
      if (walls[3] === 1) return { valid: false };
      to = from + rows;
      break;
  }
  
  // 检查是否超出边界
  if (to < 0 || to >= totalCells.value) {
    return { valid: false };
  }
  
  // 检查水平移动是否跨越行边界
  if (direction === 'left' && from % rows === 0) {
    return { valid: false };
  }
  if (direction === 'right' && from % rows === rows - 1) {
    return { valid: false };
  }
  
  return { valid: true, position: to };
}

function movePlayer(direction) {
  if (!gameState.gameStarted) {
    return;
  }
  
  const currentPosition = gameState.currentPosition;
  const currentRow = Math.floor(currentPosition / (mazeDataState.value.rownum || 8));
  const currentCol = currentPosition % (mazeDataState.value.rownum || 8);
  
  const result = isValidMove(currentPosition, direction);
  
  if (result.valid) {
    // 有效移动
    gameState.currentPosition = result.position;
    gameState.steps++;
    
    // 检查是否到达终点
    if (result.position === gameState.endPosition) {
      endGame(true);
    }
  } else {
    // 撞墙处理
    const walls = mazeDataState.value.wall[currentPosition];
    if (Array.isArray(walls)) {
      // 记录撞墙次数
      const rows = mazeDataState.value.rownum || 8;
      switch (direction) {
        case 'up':
          if (walls[0] === 1 && currentRow > 0) {
            wallRecordRow.value[currentRow - 1][currentCol]++;
          }
          break;
        case 'left':
          if (walls[1] === 1 && currentCol > 0) {
            wallRecordColumn.value[currentRow][currentCol - 1]++;
          }
          break;
        case 'right':
          if (walls[2] === 1 && currentCol < rows - 1) {
            wallRecordColumn.value[currentRow][currentCol]++;
          }
          break;
        case 'down':
          if (walls[3] === 1 && currentRow < rows - 1) {
            wallRecordRow.value[currentRow][currentCol]++;
          }
          break;
      }
    }
    
    // 撞墙返回起点
    if (wallCollisionReset.value) {
      gameState.currentPosition = gameState.startPosition;
      showCustomAlert.value = true;
      alertMessage.value = '撞墙了！返回起点。';
    }
  }
}

function handleKeyPress(event) {
  switch (event.key) {
    case 'ArrowUp':
    case 'w':
    case 'W':
      event.preventDefault();
      movePlayer('up');
      break;
    case 'ArrowDown':
    case 's':
    case 'S':
      event.preventDefault();
      movePlayer('down');
      break;
    case 'ArrowLeft':
    case 'a':
    case 'A':
      event.preventDefault();
      movePlayer('left');
      break;
    case 'ArrowRight':
    case 'd':
    case 'D':
      event.preventDefault();
      movePlayer('right');
      break;
  }
}

function endGame(isSuccess) {
  gameState.gameStarted = false;
  gameState.endTime = Date.now();
  clearInterval(gameState.timer);
  gameState.timer = null;
  
  // 显示墙壁
  gameState.showWalls = true;
  
  if (isSuccess) {
    // 显示成功消息
    showSuccessMessage.value = true;
    
    // 保存游戏结果
    saveGameResult();
  }
}

function giveUpGame() {
  if (confirm('确定要放弃游戏吗？这将显示所有墙壁。')) {
    endGame(false);
  }
}

function restartGame() {
  // 隐藏弹窗
  showSuccessMessage.value = false;
  showCustomAlert.value = false;
  
  // 重新初始化游戏
  const id = route.params.id || route.query.id || props.mazeId;
  initGame(id);
}

function closeCustomAlert() {
  showCustomAlert.value = false;
}

// 保存游戏结果到本地存储
function saveGameResult() {
  try {
    const savedData = localStorage.getItem('mazeGameData');
    const gameData = savedData ? JSON.parse(savedData) : {};
    
    const currentMazeId = route.params.id || route.query.id || props.mazeId;
    
    gameData[currentMazeId] = {
      isCompleted: true,
      steps: gameState.steps,
      time: Math.floor((Date.now() - gameState.startTime) / 1000) * 1000,
      completedAt: new Date().toISOString()
    };
    
    localStorage.setItem('mazeGameData', JSON.stringify(gameData));
    // 触发存储事件，以便其他标签页可以更新
    window.dispatchEvent(new Event('storage'));
  } catch (error) {
    console.error('保存游戏结果失败:', error);
  }
}

// 返回迷宫列表页面
function backToList() {
  router.push('/hiddenWallMaze');
}

// 前往下一个迷宫
function goToNextMaze() {
  const currentId = parseInt(props.mazeId, 10);
  const nextId = currentId + 1;
  
  if (mazeData[nextId.toString()]) {
    router.push({
      path: `/hiddenWallMaze/maze/${nextId}`,
      query: { id: nextId }
    });
  } else {
    alert('恭喜你！你已经完成了所有迷宫挑战！');
    backToList();
  }
}

// 监听器
watch(() => route.query.id, (newId) => {
  if (newId && newId !== props.mazeId) {
    initGame(newId);
  }
}, { immediate: true });

watch(() => props.mazeId, (newId) => {
  initGame(newId);
}, { immediate: true });

watch(() => route.params.id, (newId) => {
  if (newId && newId !== props.mazeId) {
    initGame(newId);
  }
}, { immediate: true });

watch(showCollidedWalls, () => {
  // 当选项改变时，自动更新显示
});

// 生命周期钩子
onMounted(() => {
  // 添加键盘事件监听
  document.addEventListener('keydown', handleKeyPress);
  
  // 从路由参数中获取ID并初始化游戏
  const id = route.params.id || route.query.id || props.mazeId || '1';
  initGame(id);
});

onBeforeUnmount(() => {
  // 清理定时器和事件监听
  if (gameState.timer) {
    clearInterval(gameState.timer);
  }
  document.removeEventListener('keydown', handleKeyPress);
});
</script>


<style scoped>
.game-container {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.maze-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px 0;
}

.maze-grid {
  display: grid;
  gap: 0;
  border: 2px solid #333;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
}

.maze-cell {
  width: 50px;
  height: 50px;
  position: relative;
}

/* 棋盘格样式 */
.even-row-even-col, .odd-row-odd-col {
  background-color: #f8f8f8;
}

.even-row-odd-col, .odd-row-even-col {
  background-color: #f0f0f0;
}

.wall-top {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: #000;
}

.wall-left {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background-color: #000;
}

.wall-right {
  position: absolute;
  top: 0;
  right: 0;
  width: 3px;
  height: 100%;
  background-color: #000;
}

.wall-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: #000;
}

/* 撞过多次的墙（红色） */
.collided-wall-top,
.collided-wall-bottom {
  position: absolute;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: #ff0000;
  z-index: 5;
}

.collided-wall-top {
  top: 0;
}

.collided-wall-bottom {
  bottom: 0;
}

.collided-wall-left,
.collided-wall-right {
  position: absolute;
  top: 0;
  width: 3px;
  height: 100%;
  background-color: #ff0000;
  z-index: 5;
}

.collided-wall-left {
  left: 0;
}

.collided-wall-right {
  right: 0;
}

.player {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 35px;
  height: 35px;
  background-color: blue;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  box-shadow: 0 2px 5px rgba(0, 0, 255, 0.3);
}

.start-point {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: green;
}

.end-point {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: red;
}

.game-info {
  margin: 20px 0;
  text-align: center;
}

.info-row {
  margin: 5px 0;
  font-size: 16px;
  color: #666;
}

.controls {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
}

.control-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
  margin-right: 40px;
}

.control-buttons button {
  padding: 15px 15px;
  font-size: 18px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.control-buttons button:hover:not(:disabled) {
  background-color: #45a049;
}

.control-buttons button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-up, .btn-down {
  grid-column: 2;
}

.btn-left {
  grid-column: 1;
  grid-row: 2;
}

.btn-right {
  grid-column: 3;
  grid-row: 2;
}

.options-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.action-buttons button {
  padding: 10px 15px;
  font-size: 14px;
  background-color: #008CBA;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.action-buttons button:hover:not(:disabled) {
  background-color: #007B9A;
}

.action-buttons button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.options {
  margin: 15px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.success-message {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 30px;
  border-radius: 10px;
  text-align: center;
  z-index: 100;
}

.custom-alert {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 101;
}

.custom-alert-content {
  background-color: white;
  padding: 30px;
  border-radius: 10px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 300px;
}

.custom-alert-content p {
  margin-bottom: 20px;
  font-size: 16px;
  color: #333;
}

.custom-alert-content button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.custom-alert-content button:hover {
  background-color: #45a049;
}

.success-message h2 {
  margin-bottom: 15px;
  color: #4CAF50;
}

.success-message p {
  margin: 10px 0;
}

.success-message button {
  padding: 10px 20px;
  margin-top: 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.keyboard-hint {
  margin-top: 20px;
  font-size: 14px;
  color: #666;
  text-align: center;
}

/* 响应式设计 */
@media(max-width: 576px) {
  .game-container {
    padding: 15px;
    max-width: 100%;
  }
  
  .maze-cell {
    width: 35px;
    height: 35px;
  }
  
  .maze-grid {
    border-width: 1px;
  }
  
  .player {
    width: 24px;
    height: 24px;
  }
  
  .wall-top,
  .wall-bottom {
    height: 2px;
  }
  
  .wall-left,
  .wall-right {
    width: 2px;
  }
  
  .controls {
    flex-direction: column;
    gap: 20px;
  }
  
  .control-buttons {
    margin-right: 0;
  }
  
  .control-buttons button {
    padding: 12px 12px;
    font-size: 16px;
  }
}
</style>