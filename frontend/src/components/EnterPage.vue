<template>
  <div>
    <h1>进入答题端</h1>
    <input v-model="name" placeholder="输入姓名" />
    <input v-model="avatarUrl" placeholder="输入头像 URL" />
    <input v-model="roomId" placeholder="输入房间 ID" />
    <button @click="enterRoom">进入房间</button>
    
    <h1>进入提问端</h1>
    <input v-model="questionRoomId" placeholder="输入房间 ID" />
    <button @click="enterQuestionPage">进入提问端</button>
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
        // 输出表单数据以便调试
        console.log('Entering room with data:', {
          roomId: roomId.value.trim(),
          name: name.value.trim(),
          avatarUrl: avatarUrl.value.trim() || ''
        });

        // 跳转到 AnswerPage 并传递表单数据
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
