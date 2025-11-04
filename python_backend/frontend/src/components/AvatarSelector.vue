<template>
  <div class="avatar-selector">
    <h3 class="selector-title">选择头像</h3>
    
    <!-- 默认头像选项 -->
    <div class="default-avatars">
      <h4>默认头像</h4>
      <div class="avatar-grid">
        <div 
          v-for="avatar in defaultAvatars" 
          :key="avatar.id"
          class="avatar-option"
          :class="{ active: selectedAvatar === avatar.url }"
          @click="selectDefaultAvatar(avatar.url)"
        >
          <img :src="avatar.url" :alt="avatar.name" class="avatar-img" />
        </div>
      </div>
    </div>

    <!-- 自定义头像上传 -->
    <div class="custom-avatar">
      <h4>自定义头像</h4>
      <div class="upload-section">
        <button @click="triggerFileInput" class="upload-btn">
          {{ imageUrl ? '重新上传' : '上传图片' }}
        </button>
        <input 
          ref="fileInput"
          type="file" 
          accept="image/*" 
          @change="onFileChange" 
          style="display: none"
        />
      </div>

      <!-- 裁剪预览区域 -->
      <div v-if="imageUrl" class="cropper-section">
        <div class="cropper-wrapper">
          <VueCropper
            ref="cropperRef"
            :src="imageUrl"
            :aspect-ratio="1"
            :view-mode="1"
            :auto-crop-area="1"
            :zoomable="true"
            :rotatable="true"
            :crop-box-resizable="true"
            :toggle-drag-mode-on-dblclick="false"
            style="width: 100%; height: 300px"
          />
        </div>
        <button @click="applyCrop" class="apply-crop-btn">应用裁剪</button>
      </div>
    </div>

    <!-- 当前选择预览 -->
    <div class="current-selection">
      <h4>当前选择</h4>
      <div class="preview">
        <img :src="currentAvatar" alt="头像预览" class="preview-avatar" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import VueCropper from 'vue-cropperjs';
import 'cropperjs/dist/cropper.css';

const emit = defineEmits(['avatar-selected']);

// 响应式数据
const selectedAvatar = ref('');
const imageUrl = ref(null);
const fileInput = ref(null);
const cropperRef = ref(null);

// 默认头像选项
const defaultAvatars = [
  {
    id: 1,
    name: '默认头像1',
    url: 'https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format'
  },
  {
    id: 2,
    name: '默认头像2',
    url: 'https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format&brightness=0.8'
  },
  {
    id: 3,
    name: '默认头像3',
    url: 'https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format&brightness=1.2'
  },
  {
    id: 4,
    name: '默认头像4',
    url: 'https://images.unsplash.com/photo-1560169573-5ff6f7f35fe4?w=300&h=300&fit=crop&q=85&auto=format&contrast=1.2'
  }
];

// 计算当前头像
const currentAvatar = computed(() => {
  return selectedAvatar.value || defaultAvatars[0].url;
});

// 监听当前头像变化
watch(currentAvatar, (newAvatar) => {
  emit('avatar-selected', newAvatar);
});

// 选择默认头像
function selectDefaultAvatar(avatarUrl) {
  selectedAvatar.value = avatarUrl;
  // 清除自定义头像
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
    imageUrl.value = null;
  }
}

// 触发文件选择
function triggerFileInput() {
  fileInput.value?.click();
}

// 文件选择处理
function onFileChange(e) {
  const file = e.target.files[0];
  if (!file) return;

  // 清理旧的 Object URL
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
  }

  // 创建新 URL
  imageUrl.value = URL.createObjectURL(file);
  selectedAvatar.value = ''; // 清除默认头像选择
}

// 应用裁剪
function applyCrop() {
  if (cropperRef.value && cropperRef.value.cropper && imageUrl.value) {
    const canvas = cropperRef.value.cropper.getCroppedCanvas({ width: 300, height: 300 });
    selectedAvatar.value = canvas.toDataURL('image/png');
    
    // 清理临时URL
    URL.revokeObjectURL(imageUrl.value);
    imageUrl.value = null;
  }
}

// 暴露方法给父组件
defineExpose({
  getCurrentAvatar: () => currentAvatar.value
});
</script>

<style scoped>
.avatar-selector {
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.selector-title {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.default-avatars h4,
.custom-avatar h4,
.current-selection h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.avatar-option {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.3s;
}

.avatar-option:hover {
  transform: scale(1.05);
  border-color: #667eea;
}

.avatar-option.active {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-section {
  margin-bottom: 20px;
}

.upload-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.upload-btn:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.cropper-section {
  margin-top: 20px;
}

.cropper-wrapper {
  border: 2px solid #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 15px;
}

.apply-crop-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.apply-crop-btn:hover {
  background: #218838;
  transform: translateY(-2px);
}

.current-selection {
  margin-top: 30px;
  text-align: center;
}

.preview-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #667eea;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}
</style>