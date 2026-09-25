<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>🔐 登录 QuizArena</h1>
        <p>登录后保存游戏记录和成就</p>
      </div>

      <div class="form-container">
        <!-- 登录表单 -->
        <form v-if="!showRegister" @submit.prevent="handleLogin" class="login-form">
          <h2>登录账户</h2>
          
          <div class="form-group">
            <label for="login-username">用户名</label>
            <input
              id="login-username"
              v-model="loginData.username"
              type="text"
              name="username"
              autocomplete="username"
              required
              placeholder="请输入用户名"
            />
          </div>

          <div class="form-group">
            <label for="login-password">密码</label>
            <input
              id="login-password"
              v-model="loginData.password"
              type="password"
              name="password"
              autocomplete="current-password"
              required
              placeholder="请输入密码"
            />
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>

          <p class="switch-form">
            还没有账户？
            <a href="#" @click.prevent="showRegister = true">立即注册</a>
          </p>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister" class="register-form">
          <h2>注册新账户</h2>
          
          <div class="form-group">
            <label for="register-username">用户名</label>
            <input
              id="register-username"
              v-model="registerData.username"
              type="text"
              name="username"
              autocomplete="username"
              required
              placeholder="3-50个字符"
              minlength="3"
              maxlength="50"
            />
          </div>

          <div class="form-group">
            <label for="register-email">邮箱</label>
            <input
              id="register-email"
              v-model="registerData.email"
              type="email"
              name="email"
              autocomplete="email"
              required
              placeholder="请输入有效邮箱"
            />
          </div>

          <div class="form-group">
            <label for="register-password">密码</label>
            <input
              id="register-password"
              v-model="registerData.password"
              type="password"
              name="new-password"
              autocomplete="new-password"
              required
              placeholder="至少6个字符"
              minlength="6"
            />
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? '注册中...' : '注册' }}
          </button>

          <p class="switch-form">
            已有账户？
            <a href="#" @click.prevent="showRegister = false">立即登录</a>
          </p>
        </form>

        <!-- 错误提示 -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>

      <div class="back-to-home">
        <button @click="navigateToHome" class="back-btn">
          ← 返回主页
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

export default {
  name: 'LoginPage',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    
    const showRegister = ref(false)
    const loading = ref(false)
    const error = ref('')

    const loginData = ref({
      username: '',
      password: ''
    })

    const registerData = ref({
      username: '',
      email: '',
      password: ''
    })

    const handleLogin = async () => {
      if (!loginData.value.username || !loginData.value.password) {
        error.value = '请输入用户名和密码'
        return
      }

      loading.value = true
      error.value = ''

      try {
        await userStore.login(loginData.value)
        
        // 检查是否有重定向目标
        const redirectPath = sessionStorage.getItem('redirectAfterLogin')
        if (redirectPath) {
          sessionStorage.removeItem('redirectAfterLogin')
          router.push(redirectPath)
        } else {
          router.push('/')
        }
      } catch (err) {
        error.value = err.message || '登录失败，请检查用户名和密码'
      } finally {
        loading.value = false
      }
    }

    const handleRegister = async () => {
      if (!registerData.value.username || !registerData.value.email || !registerData.value.password) {
        error.value = '请填写所有字段'
        return
      }

      if (registerData.value.password.length < 6) {
        error.value = '密码至少需要6个字符'
        return
      }

      loading.value = true
      error.value = ''

      try {
        await userStore.register(registerData.value)
        // 注册成功后自动登录
        await userStore.login({
          username: registerData.value.username,
          password: registerData.value.password
        })
        
        // 检查是否有重定向目标
        const redirectPath = sessionStorage.getItem('redirectAfterLogin')
        if (redirectPath) {
          sessionStorage.removeItem('redirectAfterLogin')
          router.push(redirectPath)
        } else {
          router.push('/')
        }
      } catch (err) {
        error.value = err.message || '注册失败，请重试'
      } finally {
        loading.value = false
      }
    }

    const navigateToHome = () => {
      router.push('/')
    }

    return {
      showRegister,
      loading,
      error,
      loginData,
      registerData,
      handleLogin,
      handleRegister,
      navigateToHome
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #333;
  font-size: 2rem;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 1rem;
}

.form-container h2 {
  color: #333;
  text-align: center;
  margin-bottom: 30px;
  font-size: 1.5rem;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.submit-btn {
  width: 100%;
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.3s;
  margin-bottom: 20px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.switch-form {
  text-align: center;
  color: #666;
}

.switch-form a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.switch-form a:hover {
  text-decoration: underline;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 12px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: center;
  font-size: 0.9rem;
}

.back-to-home {
  text-align: center;
  margin-top: 20px;
}

.back-btn {
  background: transparent;
  border: 2px solid #667eea;
  color: #667eea;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #667eea;
  color: white;
}

@media (max-width: 480px) {
  .login-container {
    padding: 30px 20px;
    margin: 10px;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>
