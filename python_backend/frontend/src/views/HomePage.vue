<template>
  <div class="home-page">
    <header class="header">
      <h1>🎯 QuizArena</h1>
      <p>欢迎来到多人知识竞技场</p>
    </header>

    <main class="main-content">
      <!-- 用户信息区域 -->
      <div class="user-section" v-if="userStore.isLoggedIn">
        <div class="user-info">
          <div class="avatar-container">
            <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-image" alt="用户头像" />
            <div v-else class="avatar-placeholder">{{ userStore.user?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
          </div>
          <div class="user-details">
            <h3>欢迎, {{ userStore.user?.username }}</h3>
            <p>已登录</p>
          </div>
        </div>
        <div class="user-actions">
          <button @click="navigateToRecords" class="records-btn">游戏记录</button>
          <button @click="navigateToSettings" class="settings-btn">设置</button>
          <button @click="userStore.logout" class="logout-btn">退出登录</button>
        </div>
      </div>

      <!-- 游戏选择区域 -->
      <div class="games-section">
        <h2>选择游戏</h2>
        <div class="games-grid">
          <div class="game-card" @click="navigateToGame('quiz')">
            <div class="game-icon">❓</div>
            <h3>知识问答</h3>
            <p>多人实时知识竞赛</p>
            <button class="play-btn">开始游戏</button>
          </div>

          <div class="game-card" @click="navigateToGame('samePatternHunt')">
            <div class="game-icon">🔍</div>
            <h3>找相同</h3>
            <p>快速找出相同图案</p>
            <button class="play-btn">开始游戏</button>
          </div>
        </div>
      </div>

      <!-- 登录提示区域 -->
      <div class="auth-section" v-if="!userStore.isLoggedIn">
        <div class="auth-prompt">
          <p>登录后可以保存游戏记录和成就</p>
          <button @click="navigateToLogin" class="login-btn">登录/注册</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

export default {
  name: 'HomePage',
  setup() {
    const userStore = useUserStore()
    const router = useRouter()

    const navigateToGame = (gameType) => {
      if (gameType === 'quiz') {
        router.push('/quiz/enter')
      } else if (gameType === 'samePatternHunt') {
        router.push('/samePatternHunt')
      }
    }

    const navigateToLogin = () => {
      router.push('/login')
    }

    const navigateToSettings = () => {
      router.push('/settings')
    }

    const navigateToRecords = () => {
      router.push('/records')
    }

    return {
      userStore,
      navigateToGame,
      navigateToLogin,
      navigateToSettings,
      navigateToRecords
    }
  }
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e6ffe6 0%, #b2f7b2 70%, #f8fbf8 100%);
  color: #2c3e50;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 2;
}

.header h1 {
  font-size: 3rem;
  margin-bottom: 10px;
  color: #2c3e50;
  text-shadow: 0 1px 3px rgba(255, 255, 255, 0.7);
}

.header p {
  font-size: 1.2rem;
  color: #34495e;
  opacity: 0.9;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.user-section {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 20px;
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-actions {
  display: flex;
  gap: 10px;
}

.records-btn {
  background: #3a9d6a;
  border: none;
  color: white;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.records-btn:hover {
  background: #2e8058;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.settings-btn {
  background: #5ca97a;
  border: none;
  color: white;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.settings-btn:hover {
  background: #4a906a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.avatar-container {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: 2px solid rgba(58, 157, 106, 0.3);
}

.avatar-placeholder {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(58, 157, 106, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  border: 2px solid rgba(58, 157, 106, 0.3);
}

.user-details h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #2c3e50;
}

.user-details p {
  margin: 0;
  color: #34495e;
  font-size: 0.9rem;
}

.logout-btn {
  background: #7eb88e;
  border: none;
  color: white;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.logout-btn:hover {
  background: #6d9b7e;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.games-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 30px;
  color: #2c3e50;
}

.games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-bottom: 40px;
}

.game-card {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border-radius: 16px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(58, 157, 106, 0.25);
}

.game-icon {
  font-size: 4rem;
  margin-bottom: 15px;
}

.game-card h3 {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: #2c3e50;
}

.game-card p {
  opacity: 0.8;
  margin-bottom: 20px;
  color: #34495e;
}

.play-btn {
  background: #3a9d6a;
  border: none;
  color: white;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.play-btn:hover {
  background: #2e8058;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.auth-section {
  text-align: center;
}

.auth-prompt {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 20px;
  display: inline-block;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.auth-prompt p {
  color: #34495e;
  margin-bottom: 15px;
}

.login-btn {
  background: #3a9d6a;
  border: none;
  color: white;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.login-btn:hover {
  background: #2e8058;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

@media (max-width: 768px) {
  .games-grid {
    grid-template-columns: 1fr;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .user-section {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .user-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>