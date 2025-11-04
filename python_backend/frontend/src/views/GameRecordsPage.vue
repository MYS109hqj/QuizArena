<template>
  <div class="game-records-page">
    <!-- Header -->
    <div class="page-header">
      <button class="back-button" @click="goBack">← 返回</button>
      <h1>游戏记录</h1>
      <p>查看您的游戏历史和统计信息</p>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ totalGames }}</div>
        <div class="stat-label">总游戏次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ averageScore.toFixed(1) }}</div>
        <div class="stat-label">平均得分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ bestScore }}</div>
        <div class="stat-label">最高得分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ averageAccuracy.toFixed(1) }}%</div>
        <div class="stat-label">平均准确率</div>
      </div>
    </div>

    <!-- 游戏类型筛选 -->
    <div class="game-filter">
      <select v-model="selectedGameType" @change="loadGameRecords">
        <option value="">所有游戏</option>
        <option value="same_pattern_hunt">相同图案狩猎</option>
        <!-- 可以添加更多游戏类型 -->
      </select>
    </div>

    <!-- 游戏记录列表 -->
    <div class="records-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="gameRecords.length === 0" class="no-records">
        暂无游戏记录
      </div>
      <div v-else class="records-container">
        <div v-for="record in gameRecords" :key="record.id" class="record-item">
          <div class="record-header">
            <span class="game-type">{{ getGameTypeName(record.game_type) }}</span>
            <span class="record-date">{{ formatDate(record.start_time) }}</span>
          </div>
          <div class="record-details">
            <div class="detail-item">
              <span class="label">得分:</span>
              <span class="value">{{ record.score }}</span>
            </div>
            <div class="detail-item">
              <span class="label">准确率:</span>
              <span class="value">{{ record.accuracy }}%</span>
            </div>
            <div class="detail-item">
              <span class="label">游戏时长:</span>
              <span class="value">{{ formatDuration(record.duration_seconds) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">回合:</span>
              <span class="value">{{ record.rounds_played }}/{{ record.rounds_total }}</span>
            </div>
          </div>
          <div class="record-status" :class="record.status">
            {{ getStatusText(record.status) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 加载更多按钮 -->
    <div v-if="hasMoreRecords" class="load-more">
      <button @click="loadMore" :disabled="loadingMore">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

// 从环境变量获取API基础URL，默认使用localhost
const API_BASE_URL = import.meta.env.VITE_URL || 'http://localhost:8000';

const userStore = useUserStore()
const router = useRouter()

// 响应式数据
const gameRecords = ref([])
const playerStats = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const selectedGameType = ref('')
const currentPage = ref(1)
const hasMoreRecords = ref(false)

// 计算属性
const totalGames = computed(() => {
  if (selectedGameType.value) {
    const stat = playerStats.value.find(s => s.game_type === selectedGameType.value)
    return stat ? stat.total_games : 0
  }
  return playerStats.value.reduce((sum, stat) => sum + stat.total_games, 0)
})

const averageScore = computed(() => {
  if (selectedGameType.value) {
    const stat = playerStats.value.find(s => s.game_type === selectedGameType.value)
    return stat ? stat.average_score : 0
  }
  const total = playerStats.value.reduce((sum, stat) => sum + stat.average_score * stat.total_games, 0)
  const totalGames = playerStats.value.reduce((sum, stat) => sum + stat.total_games, 0)
  return totalGames > 0 ? total / totalGames : 0
})

const bestScore = computed(() => {
  if (selectedGameType.value) {
    const stat = playerStats.value.find(s => s.game_type === selectedGameType.value)
    return stat ? stat.best_score : 0
  }
  return Math.max(...playerStats.value.map(stat => stat.best_score), 0)
})

const averageAccuracy = computed(() => {
  if (selectedGameType.value) {
    const stat = playerStats.value.find(s => s.game_type === selectedGameType.value)
    return stat ? stat.average_accuracy : 0
  }
  const total = playerStats.value.reduce((sum, stat) => sum + stat.average_accuracy * stat.total_games, 0)
  const totalGames = playerStats.value.reduce((sum, stat) => sum + stat.total_games, 0)
  return totalGames > 0 ? total / totalGames : 0
})

// 方法
const loadPlayerStats = async () => {
  try {
    // 检查用户是否已登录
    if (!userStore.isLoggedIn) {
      console.log('用户未登录，无法加载统计信息')
      return
    }

    console.log('获取统计信息，用户状态:', userStore.isLoggedIn ? '已登录' : '未登录')

    const response = await fetch(`${API_BASE_URL}/game-records/stats`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    console.log('统计API响应状态:', response.status)

    if (response.ok) {
      const data = await response.json()
      playerStats.value = data
      console.log('玩家统计加载成功:', data)
    } else {
      console.error('统计API错误:', response.status, await response.text())
    }
  } catch (error) {
    console.error('加载玩家统计失败:', error)
  }
}

const loadGameRecords = async (page = 1) => {
  // 检查用户是否已登录
  if (!userStore.isLoggedIn) {
    console.log('用户未登录，无法加载游戏记录')
    return
  }

  loading.value = page === 1
  loadingMore.value = page > 1

  try {
    // 确保page是有效的数字
    const pageNum = Number(page) || 1
    const offset = (pageNum - 1) * 10

    console.log('计算参数 - page:', page, 'pageNum:', pageNum, 'offset:', offset)

    // 确保offset是有效的数字
    if (isNaN(offset) || offset < 0) {
      console.error('无效的offset参数:', offset)
      return
    }

    const params = new URLSearchParams({
      limit: '10',
      offset: String(offset)
    })

    if (selectedGameType.value) {
      params.append('game_type', selectedGameType.value)
    }

    console.log('最终API请求URL:', `${API_BASE_URL}/game-records/sessions?${params}`)
    console.log('API请求参数:', params.toString())
    console.log('使用cookie认证，credentials配置为: include')
    console.log('用户登录状态:', userStore.isLoggedIn)

    // 现在使用cookie进行身份验证，不需要手动检查token

    const response = await fetch(`${API_BASE_URL}/game-records/sessions?${params}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    console.log('游戏记录API响应状态:', response.status)

    if (response.ok) {
      const records = await response.json()

      // 添加详细日志记录返回的数据
      console.log('API返回的完整数据:', records)
      console.log('数据类型:', Array.isArray(records) ? '数组' : typeof records)

      if (Array.isArray(records)) {
        if (page === 1) {
          gameRecords.value = records
        } else {
          gameRecords.value.push(...records)
        }

        hasMoreRecords.value = records.length === 10
        currentPage.value = page
        console.log('游戏记录加载成功，数量:', records.length)
      } else {
        console.error('API返回的数据不是数组:', records)
        gameRecords.value = []
      }
    } else {
      console.error('游戏记录API错误:', response.status, await response.text())
    }
  } catch (error) {
    console.error('加载游戏记录失败:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadGameRecords(currentPage.value + 1)
}

const getGameTypeName = (gameType) => {
  const gameNames = {
    'same_pattern_hunt': '相同图案狩猎',
    'samePatternHunt': '相同图案狩猎'
  }
  return gameNames[gameType] || gameType
}

const formatDate = (dateString) => {
  try {
    // 尝试处理不同格式的日期字符串
    if (!dateString.includes('Z')) {
      dateString += 'Z'
    }
    const date = new Date(dateString)
    console.log(date, dateString);
    // 检查是否是有效的日期
    if (isNaN(date.getTime())) {
      console.warn('无效的日期字符串:', dateString)
      return '未知时间'
    }

    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    console.error('日期格式化错误:', error)
    return '日期错误'
  }
}

const formatDuration = (seconds) => {
  if (seconds < 60) {
    return `${seconds}秒`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
}

const getStatusText = (status) => {
  const statusTexts = {
    'completed': '已完成',
    'abandoned': '已放弃',
    'timeout': '超时'
  }
  return statusTexts[status] || status
}

const goBack = () => {
  router.back()
}

// 生命周期
onMounted(() => {
  // 检查用户是否已登录
  if (!userStore.isLoggedIn) {
    console.log('用户未登录，跳转到登录页面')
    // 在实际应用中应该跳转到登录页面
    return
  }

  console.log('用户已登录，开始加载游戏记录')
  console.log('使用cookie认证方式，credentials: include')
  loadPlayerStats()
  loadGameRecords()
})
</script>

<style scoped>
.game-records-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  padding-top: 20px;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 10px;
}

.page-header p {
  font-size: 1.1rem;
  color: #666;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  padding: 30px 20px;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.9;
}

.game-filter {
  margin-bottom: 30px;
  text-align: center;
}

.game-filter select {
  padding: 10px 20px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
}

.records-list {
  min-height: 300px;
}

.loading,
.no-records {
  text-align: center;
  padding: 60px 20px;
  font-size: 1.2rem;
  color: #666;
}

.records-container {
  display: grid;
  gap: 20px;
}

.record-item {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.record-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.game-type {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.record-date {
  color: #666;
  font-size: 0.9rem;
}

.record-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #666;
  font-weight: 500;
}

.value {
  color: #333;
  font-weight: bold;
}

.record-status {
  text-align: right;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 5px 10px;
  border-radius: 20px;
  display: inline-block;
}

.record-status.completed {
  background: #e8f5e8;
  color: #2e7d32;
}

.record-status.abandoned {
  background: #ffebee;
  color: #c62828;
}

.record-status.timeout {
  background: #fff3e0;
  color: #ef6c00;
}

.load-more {
  text-align: center;
  margin-top: 30px;
}

.back-button {
  position: absolute;
  left: 20px;
  top: 20px;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.back-button:hover {
  background-color: #ddd;
}

.load-more button {
  padding: 12px 30px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.load-more button:hover:not(:disabled) {
  background: #45a049;
}

.load-more button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .record-details {
    grid-template-columns: 1fr;
  }

  .record-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>