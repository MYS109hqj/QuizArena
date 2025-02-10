<template>
  <div class="container">
    <h1>进入答题端</h1>
    <div class="input-group">
      <input v-model="name" placeholder="输入姓名" class="input-field" />
      <div class="avatar-container">
        <select v-model="selectedAvatar" @change="updateAvatarUrl" class="input-field">
          <option value="">选择头像</option>
          <option v-for="avatar in avatarOptions" :key="avatar" :value="avatar">
            {{ avatar }}
          </option>
        </select>
        <input 
          v-model="customAvatarUrl" 
          @input="updateAvatarUrl" 
          placeholder="或输入自定义头像 URL" 
          class="input-field" 
        />
        <div class="avatar-preview" v-if="avatarUrl">
          <img :src="avatarUrl" alt="头像预览" class="avatar-image" />
        </div>
      </div>
      <input v-model="roomId" placeholder="输入房间 ID" class="input-field" />
      <button @click="enterRoom" class="primary-button">进入房间</button>
    </div>

    <h1>进入提问端</h1>
    <div class="input-group">
      <input v-model="questionRoomId" placeholder="输入房间 ID" class="input-field" />
      <button @click="enterQuestionPage" class="primary-button">进入提问端</button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const name = ref('');
    const avatarUrl = ref(''); // 最终头像 URL
    const selectedAvatar = ref(''); // 选中的头像
    const roomId = ref('');
    const questionRoomId = ref('');
    const customAvatarUrl = ref(''); // 自定义头像 URL
    const router = useRouter();

    // 备选头像 URL 列表
    const avatarOptions = ref([
      'https://i0.hippopx.com/photos/562/605/256/coffee-cup-of-coffee-coffee-beans-drink-preview.jpg',
      'https://i0.hippopx.com/photos/16/106/420/hummingbird-anna-s-hummingbird-bird-preview.jpg',
      'https://i0.hippopx.com/photos/811/1016/50/woman-model-street-beijing-beauty-preview.jpg',
      'https://i0.hippopx.com/photos/768/377/295/lighthouse-sea-water-eastbourne-preview.jpg',
      'https://i0.hippopx.com/photos/486/41/106/coding-computer-hacker-hacking-preview.jpg',
      'https://i0.hippopx.com/photos/139/572/1003/macro-macro-photo-macro-photography-close-preview.jpg',
    ]);

    // 生成唯一用户 ID 的函数
    const generateUniqueId = (prefix) => {
      return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
    };

    // 进入答题端的函数
    const enterRoom = () => {
      if (name.value.trim() && roomId.value.trim()) {
        const playerId = generateUniqueId('user');  // 生成随机 playerId

        // 最终头像 URL 选择逻辑
        avatarUrl.value = customAvatarUrl.value.trim() || selectedAvatar.value || ''; // 使用自定义 URL 或选中的头像

        console.log('Entering room with data:', {
          roomId: roomId.value.trim(),
          name: name.value.trim(),
          avatarUrl: avatarUrl.value.trim() || '',
          playerId: playerId
        });

        // 将 playerId 作为查询参数带入 AnswerPage
        router.push({
          name: 'AnswerPage',
          params: {
            roomId: roomId.value.trim(),
          },
          query: {
            name: name.value.trim(),
            avatarUrl: avatarUrl.value.trim() || '',
            playerId: playerId  // 将 playerId 添加到 URL 查询参数
          }
        });

      } else {
        console.warn('Name or roomId is empty.');
      }
    };

    // 更新头像 URL
    const updateAvatarUrl = () => {
      // 先检查是否有自定义 URL，有则使用自定义 URL
      avatarUrl.value = customAvatarUrl.value.trim() || selectedAvatar.value;
    };

    // 进入提问端的函数
    const enterQuestionPage = () => {
      if (questionRoomId.value.trim()) {
        const playerId = generateUniqueId('questioner');  // 生成随机 playerId

        // 将 playerId 作为查询参数带入 QuestionPage
        router.push({
          name: 'QuestionPage',
          params: {
            roomId: questionRoomId.value.trim()
          },
          query: {
            playerId: playerId // 将 playerId 添加到 URL 查询参数
          }
        });
      } else {
        console.warn('questionRoomId is empty.');
      }
    };

    return {
      name,
      avatarUrl,
      roomId,
      questionRoomId,
      avatarOptions,
      selectedAvatar,
      customAvatarUrl, // 返回自定义头像 URL
      enterRoom,
      enterQuestionPage,
      updateAvatarUrl
    };
  }
};
</script>

<style scoped>
.container {
  width: 80%;
  margin: 0 auto;
  padding: 20px;
  background-color: #f7fafc;
  border-radius: 10px;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #34495e;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.input-field {
  width: 100%;
  max-width: 400px;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box;
  font-size: 1em;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
}

.primary-button {
  background-color: #27ae60;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s;
  margin-top: 10px;
  width: 100%;
  max-width: 400px;
}

.primary-button:hover {
  background-color: #2ecc71;
}

.avatar-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  width: 100%;
  max-width: 400px;
}

.avatar-preview {
  margin-left: 10px;
}

.avatar-image {
  width: 50px;
  height: 50px;
  border-radius: 50%; /* 圆形 */
  object-fit: cover; /* 确保图片填满整个区域 */
}
</style>
