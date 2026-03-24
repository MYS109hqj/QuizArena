import { defineStore } from 'pinia'
import { ref } from 'vue'

// 从环境变量获取服务器URL
const API_BASE_URL = import.meta.env.VITE_URL || 'http://localhost:8000';

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  // 不再从localStorage获取token，而是依赖cookie自动发送
  const isLoggedIn = ref(false)

  // 初始化时验证用户是否已登录
  async function checkLoginStatus() {
    try {
      // 这里不需要手动设置Authorization头，因为cookie会自动发送
      const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
        credentials: 'include'  // 关键：允许发送cookie
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.valid) {
          // 获取用户信息
          await getUserProfile()
          isLoggedIn.value = true
        }
      }
    } catch (error) {
      console.error('检查登录状态失败:', error)
      isLoggedIn.value = false
    }
  }

  // 验证token有效性
  async function verifyToken() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
        credentials: 'include'  // 允许发送cookie
      })
      
      if (!response.ok) {
        throw new Error('Token验证失败')
      }
      
      const data = await response.json()
      if (data.valid) {
        // 获取用户信息
        await getUserProfile()
      } else {
        logout()
      }
    } catch (error) {
      console.error('Token验证失败:', error)
      logout()
    }
  }

  // 获取用户信息
  async function getUserProfile() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        credentials: 'include'  // 允许发送cookie
      })
      
      if (response.ok) {
        user.value = await response.json()
        isLoggedIn.value = true
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  // 更新用户资料
  async function updateProfile(profileData) {
    try {
      // 验证用户是否已登录
      if (!isLoggedIn.value) {
        throw new Error('用户未登录')
      }
      
      console.log('更新用户资料:', profileData)
      
      // 调用后端API更新用户资料
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',  // 允许发送cookie
        body: JSON.stringify(profileData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '更新失败')
      }
      
      // 获取更新后的用户信息
      const updatedUser = await response.json()
      
      // 更新本地用户信息
      user.value = updatedUser
      
      console.log('用户资料更新成功（服务器存储）')
      return { success: true, message: '资料更新成功' }
    } catch (error) {
      console.error('更新用户资料失败:', error)
      throw new Error('更新失败: ' + error.message)
    }
  }

  // 用户登录
  async function login(credentials) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',  // 允许接收和发送cookie
        body: JSON.stringify(credentials)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '登录失败')
      }
      
      const data = await response.json()
      user.value = data.user
      isLoggedIn.value = true
      
      // 不再需要手动保存token到localStorage，cookie由后端设置
      
      return data
    } catch (error) {
      throw error
    }
  }

  // 用户注册
  async function register(userData) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',  // 允许接收和发送cookie
        body: JSON.stringify(userData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '注册失败')
      }
      
      return await response.json()
    } catch (error) {
      throw error
    }
  }

  // 用户退出
  async function logout() {
    try {
      // 调用后端logout接口清除server-side session
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'  // 允许发送cookie
      })
    } catch (error) {
      console.error('退出登录失败:', error)
    } finally {
      // 清除本地状态
      user.value = null
      isLoggedIn.value = false
    }
  }

  // 获取认证头 - 不再需要，使用cookie自动发送
  function getAuthHeader() {
    return {} // 空对象，因为认证信息通过cookie发送
  }

  // 初始化调用checkLoginStatus
  checkLoginStatus()

  return {
    user,
    isLoggedIn,
    login,
    register,
    logout,
    getAuthHeader,
    verifyToken,
    getUserProfile,
    updateProfile,
    checkLoginStatus
  }
})