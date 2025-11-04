<template>
  <div class="user-settings-page">
    <div class="settings-container">
      <h1 class="page-title">用户设置</h1>
      
      <!-- 用户信息卡片 -->
      <div class="user-card">
        <div class="user-avatar-section">
          <div class="avatar-preview">
            <img :src="tempAvatar" alt="头像预览" class="avatar-image" />
          </div>
          <p class="avatar-hint">点击下方选择器更换头像</p>
        </div>
        
        <div class="user-info-section">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              id="username"
              v-model="tempUsername" 
              type="text" 
              class="form-input" 
              placeholder="请输入用户名"
            />
          </div>
          
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-label">游戏次数</span>
              <span class="stat-value">{{ userStats.gameCount || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">胜率</span>
              <span class="stat-value">{{ userStats.winRate || '0%' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 头像选择器 -->
      <AvatarSelector 
        ref="avatarSelectorRef"
        @avatar-selected="handleAvatarSelected"
      />

      <!-- 设置操作按钮 -->
      <div class="settings-actions">
        <button @click="saveSettings" class="save-btn" :disabled="!isFormValid">
          保存设置
        </button>
        <button @click="cancelChanges" class="cancel-btn">
          取消
        </button>
      </div>

      <!-- 其他设置选项 -->
      <div class="additional-settings">
        <h3>其他设置</h3>
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="settings.notifications" />
            接收游戏通知
          </label>
        </div>
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="settings.soundEffects" />
            启用音效
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/userStore';
import AvatarSelector from '../components/AvatarSelector.vue';

const router = useRouter();
const userStore = useUserStore();

// 响应式数据
const tempUsername = ref('');
const tempAvatar = ref('');
const avatarSelectorRef = ref(null);

// 用户统计信息
const userStats = ref({
  gameCount: 0,
  winRate: '0%'
});

// 其他设置
const settings = ref({
  notifications: true,
  soundEffects: true
});

// 计算属性：表单验证
const isFormValid = computed(() => {
  return tempUsername.value.trim().length > 0;
});

// 生命周期
onMounted(() => {
  // 初始化用户数据
  if (userStore.user) {
    tempUsername.value = userStore.user.username || '';
    tempAvatar.value = userStore.user.avatar || getDefaultAvatar();
  } else {
    // 如果没有用户数据，也显示默认头像
    tempAvatar.value = getDefaultAvatar();
  }
  
  // 尝试从localStorage加载用户设置
  try {
    const savedProfile = localStorage.getItem('quizarena_user_profile');
    if (savedProfile) {
      const profileData = JSON.parse(savedProfile);
      if (profileData.settings) {
        settings.value = { ...settings.value, ...profileData.settings };
      }
    }
  } catch (error) {
    console.warn('加载用户设置失败:', error);
  }
});

// 获取默认头像
function getDefaultAvatar() {
  return "https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format";
}

// 处理头像选择
function handleAvatarSelected(avatarUrl) {
  tempAvatar.value = avatarUrl;
}

// 保存设置
async function saveSettings() {
  try {
    // 获取最终选择的头像
    let finalAvatar = tempAvatar.value;
    
    // 如果头像选择器有当前头像，使用它
    if (avatarSelectorRef.value) {
      const currentAvatar = avatarSelectorRef.value.getCurrentAvatar?.();
      if (currentAvatar) {
        finalAvatar = currentAvatar;
      }
    }

    // 更新用户信息
    const updateData = {
      username: tempUsername.value,
      avatar: finalAvatar,
      settings: settings.value
    };

    // 使用用户存储的更新功能
    const result = await userStore.updateProfile(updateData);
    
    // 显示成功消息
    if (result && result.success) {
      alert(result.message || '设置保存成功！');
    } else {
      alert('设置保存失败，请稍后重试');
    }
    
    // 返回上一页
    router.back();
  } catch (error) {
    console.error('保存设置失败:', error);
    alert('保存设置失败: ' + error.message);
    router.back();
  }
}

// 取消更改
function cancelChanges() {
  router.back();
}
</script>

<style scoped>
.user-settings-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.settings-container {
  max-width: 600px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.page-title {
  text-align: center;
  color: #2c3e50;
  font-size: 2.5rem;
  margin-bottom: 40px;
  font-weight: 600;
}

.user-card {
  display: flex;
  gap: 30px;
  margin-bottom: 40px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.user-avatar-section {
  text-align: center;
  flex-shrink: 0;
}

.avatar-preview {
  margin-bottom: 15px;
}

.avatar-image {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #667eea;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.avatar-hint {
  margin-top: 10px;
  color: #6c757d;
  font-size: 0.9rem;
  text-align: center;
}

.user-info-section {
  flex: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 600;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 10px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
}

.user-stats {
  display: flex;
  gap: 30px;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: #667eea;
}

/* 头像选择器样式调整 */
.avatar-selector {
  margin-bottom: 30px;
}

.settings-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 40px;
}

.save-btn, .cancel-btn {
  padding: 12px 30px;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.save-btn {
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.save-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

.additional-settings {
  border-top: 1px solid #e9ecef;
  padding-top: 30px;
}

.additional-settings h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #2c3e50;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #667eea;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 20px;
  }
  
  .user-card {
    flex-direction: column;
    text-align: center;
  }
  
  .user-stats {
    justify-content: center;
  }
  
  .settings-actions {
    flex-direction: column;
  }
}
</style>