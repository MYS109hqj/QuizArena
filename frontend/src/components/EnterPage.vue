<template>
  <div class="container">
    <h1>进入答题端</h1>
    <div class="input-group">
      <input v-model="name" placeholder="输入姓名" class="input-field" />
      <input v-model="avatarUrl" placeholder="输入头像 URL" class="input-field" />
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
    const avatarUrl = ref('');
    const roomId = ref('');
    const questionRoomId = ref('');
    const router = useRouter();

    const enterRoom = () => {
      if (name.value.trim() && roomId.value.trim()) {
        console.log('Entering room with data:', {
          roomId: roomId.value.trim(),
          name: name.value.trim(),
          avatarUrl: avatarUrl.value.trim() || ''
        });

        router.push({
          name: 'AnswerPage',
          params: {
            roomId: roomId.value.trim(),
          },
          query: {
            name: name.value.trim(),
            avatarUrl: avatarUrl.value.trim() || ''
          }
        });

      } else {
        console.warn('Name or roomId is empty.');
      }
    };

    const enterQuestionPage = () => {
      if (questionRoomId.value.trim()) {
        router.push({
          name: 'QuestionPage',
          params: {
            roomId: questionRoomId.value.trim()
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
      enterRoom,
      enterQuestionPage
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
</style>
