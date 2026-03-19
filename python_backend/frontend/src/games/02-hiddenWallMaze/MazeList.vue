<template>
  <div class="maze-list-container">
    <h1 class="page-title">隐藏墙迷宫挑战</h1>

    <!-- 游戏介绍区域 -->
    <div class="game-intro">
      <p class="intro-text">
        欢迎来到隐藏墙迷宫挑战！在这个游戏中，你需要从绿色起点到达红色终点。
        注意：墙壁是隐形的，撞到它们会返回起点，多次撞同个墙时才会显示。
        尝试完成所有迷宫挑战！
      </p>
    </div>

    <!-- 迷宫列表 -->
    <div class="maze-table-container">
      <table class="maze-table">
        <thead>
          <tr class="table-header">
            <th class="header-id">#</th>
            <th class="header-status">状态</th>
            <th class="header-steps">步数</th>
            <th class="header-time">时间</th>
            <th class="header-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(maze, index) in mazeList" :key="index" class="maze-item"
            :class="{ 'completed': maze.isCompleted }">
            <td class="maze-id">{{ index + 1 }}</td>
            <td class="maze-status">
              <span :class="['status-badge', maze.isCompleted ? 'status-completed' : 'status-pending']">
                {{ maze.isCompleted ? '已完成' : '未完成' }}
              </span>
            </td>
            <td class="maze-steps">{{ maze.steps || '--' }}</td>
            <td class="maze-time">{{ maze.time || '--' }}</td>
            <td class="maze-action">
              <button class="play-button" @click="navigateToMaze(index + 1)">
                开始游戏
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 统计信息 -->
    <div class="statistics">
      <div class="stat-item">
        <span class="stat-label">总迷宫数：</span>
        <span class="stat-value">{{ mazeList.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已完成：</span>
        <span class="stat-value">{{ completedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">完成率：</span>
        <span class="stat-value">{{ completionRate }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import mazeData from './mazes.json'; // 导入迷宫数据

// 路由
const router = useRouter();

// 响应式数据
const mazeList = ref([]);

// 计算已完成迷宫数量
const completedCount = computed(() => {
  return mazeList.value.filter(maze => maze.isCompleted).length;
});

// 计算完成率
const completionRate = computed(() => {
  if (mazeList.value.length === 0) return 0;
  return Math.round((completedCount.value / mazeList.value.length) * 100);
});

// 初始化迷宫列表数据
const initMazeList = () => {
  // 获取本地存储的游戏数据
  const savedData = localStorage.getItem('mazeGameData');
  const gameData = savedData ? JSON.parse(savedData) : {};

  // 从mazes.json创建迷宫列表
  const mazeCount = Object.keys(mazeData).length;
  mazeList.value = Array.from({ length: mazeCount }, (_, index) => {
    const mazeId = index + 1;
    const savedMaze = gameData[mazeId] || {};

    return {
      id: mazeId,
      isCompleted: savedMaze.isCompleted || false,
      steps: savedMaze.steps || null,
      time: savedMaze.time ? formatTime(savedMaze.time) : null,
      pathLength: mazeData[mazeId]?.path_length || 0
    };
  });
};

// 格式化时间为分:秒
const formatTime = (milliseconds) => {
  if (!milliseconds) return '--';
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

// 导航到迷宫游戏页面
const navigateToMaze = (mazeId) => {
  // 使用路由参数传递迷宫ID
  router.push({
    path: `/hiddenWallMaze/maze/${mazeId}`,
    query: { id: mazeId }
  });
};

// 监听本地存储变化，实时更新列表数据
const handleStorageChange = () => {
  initMazeList();
};

// 组件挂载时初始化数据
onMounted(() => {
  initMazeList();
  // 添加存储事件监听器
  window.addEventListener('storage', handleStorageChange);
});

// 组件卸载时移除监听器
onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
});
</script>

<style scoped>
/* 全局样式 */
.maze-list-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

/* 页面标题 */
.page-title {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 30px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  font-weight: bold;
}

/* 游戏介绍 */
.game-intro {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 30px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.intro-text {
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 0;
  text-align: center;
}

/* 表格容器 */
.maze-table-container {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 30px;
}

/* 迷宫表格 */
.maze-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

/* 表头样式 */
.table-header {
  background: rgba(255, 255, 255, 0.2);
}

.table-header th {
  padding: 15px 10px;
  text-align: left;
  font-weight: bold;
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}

.header-id {
  width: 50px;
  text-align: center;
}

.header-status {
  width: 120px;
}

.header-steps {
  width: 80px;
  text-align: center;
}

.header-time {
  width: 100px;
  text-align: center;
}

.header-action {
  width: 120px;
  text-align: center;
}

/* 表格行样式 */
.maze-item {
  transition: background-color 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.maze-item:last-child {
  border-bottom: none;
}

.maze-item:hover {
  background: rgba(255, 255, 255, 0.15);
}

.maze-item.completed {
  background: rgba(46, 204, 113, 0.15);
}

.maze-item td {
  padding: 12px 10px;
}

/* 迷宫ID */
.maze-id {
  font-weight: bold;
  text-align: center;
  font-size: 1.1rem;
}

/* 状态标签 */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: bold;
  text-transform: uppercase;
}

.status-pending {
  background: rgba(243, 156, 18, 0.2);
  color: #f39c12;
}

.status-completed {
  background: rgba(46, 204, 113, 0.2);
  color: #2ecc71;
}

/* 步数和时间 */
.maze-steps,
.maze-time {
  text-align: center;
  font-family: 'Courier New', monospace;
}

/* 操作按钮 */
.play-button {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.5px;
}

.play-button:hover {
  background: linear-gradient(135deg, #2980b9, #1f6dad);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.play-button:active {
  transform: translateY(0);
}

/* 统计信息 */
.statistics {
  display: flex;
  justify-content: center;
  gap: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 1.8rem;
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .maze-list-container {
    padding: 15px;
  }

  .page-title {
    font-size: 2rem;
    margin-bottom: 20px;
  }

  .intro-text {
    font-size: 1rem;
  }

  .table-header th {
    padding: 10px 5px;
    font-size: 0.8rem;
  }

  .maze-item td {
    padding: 10px 5px;
    font-size: 0.9rem;
  }

  .header-id {
    width: 40px;
  }

  .header-status {
    width: 100px;
  }

  .header-steps,
  .header-time {
    width: 70px;
  }

  .header-action {
    width: 100px;
  }

  .play-button {
    padding: 6px 12px;
    font-size: 0.8rem;
  }

  .statistics {
    flex-direction: column;
    gap: 20px;
    padding: 15px;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .maze-table {
    font-size: 0.85rem;
  }

  .table-header {
    display: none;
  }

  .maze-item {
    display: block;
    padding: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .maze-item td {
    display: block;
    text-align: left;
    padding: 5px 0;
  }

  .maze-item td.maze-action {
    text-align: center;
    margin-top: 10px;
  }

  .maze-item td:before {
    content: attr(data-label);
    font-weight: bold;
    display: inline-block;
    width: 80px;
    margin-right: 10px;
  }
}
</style>