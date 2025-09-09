<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-card" @click.stop>
      <h2 class="modal-title">设置个人资料</h2>

      <!-- 名字输入 -->
      <div class="form-group">
        <label>昵称</label>
        <input v-model="tempName" class="form-input" placeholder="输入名字" />
      </div>

      <!-- 头像上传 -->
      <div class="form-group">
        <label>头像</label>
        <input type="file" accept="image/*" @change="onFileChange" />
      </div>

      <!-- 裁剪区域 -->
      <div v-if="imageUrl" class="cropper-wrapper">
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

      <!-- 默认头像预览（无上传时） -->
      <div v-else class="avatar-preview">
        <img :src="tempAvatar" alt="头像预览" />
      </div>

      <!-- 按钮 -->
      <div class="modal-actions">
        <button @click="saveProfile" class="action-btn create">保存</button>
        <button @click="close" class="action-btn cancel">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue';
import VueCropper from 'vue-cropperjs';
import 'cropperjs/dist/cropper.css';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const props = defineProps({ show: Boolean });
const emits = defineEmits(['close']);

const store = useSamePatternHuntStore();
const tempName = ref(store.player_name);
const tempAvatar = ref(store.avatarUrl);
const imageUrl = ref(null);
const cropperRef = ref(null); // 用于访问 VueCropper 实例

// 监听弹窗显示，重置状态
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      tempName.value = store.player_name;
      tempAvatar.value = store.avatarUrl;
      imageUrl.value = null;
    }
  }
);

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

  // 等待 DOM 更新后再初始化 cropper
  nextTick(() => {
    // VueCropper 会自动初始化，无需手动调用 new Cropper()
  });
}

// 保存裁剪结果
function saveProfile() {
  let avatarBase64 = tempAvatar.value;

  // ✅ 正确方式：检查 cropperRef.value.cropper
  console.log(cropperRef.value);
  if (cropperRef.value && cropperRef.value.cropper && imageUrl.value) {
    const canvas = cropperRef.value.cropper.getCroppedCanvas({ width: 300, height: 300 });
    avatarBase64 = canvas.toDataURL('image/png');
  }

  store.setPlayerProfile(tempName.value, avatarBase64);
  close();
}

// 关闭弹窗
function close() {
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
    imageUrl.value = null;
  }
  emits('close');
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-title {
  margin: 0 0 16px;
  color: #333;
  font-size: 1.5em;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.cropper-wrapper {
  margin: 16px 0;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
}

.avatar-preview {
  margin: 16px 0;
  text-align: center;
}

.avatar-preview img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.action-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.action-btn.create {
  background: #007bff;
  color: white;
}

.action-btn.cancel {
  background: #6c757d;
  color: white;
}
</style>