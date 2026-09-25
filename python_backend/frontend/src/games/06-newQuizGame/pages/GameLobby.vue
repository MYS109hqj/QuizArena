<template>
  <main class="page">
    <header>
      <button @click="$router.push('/')">← 首页</button>
      <h1>New Quiz Game</h1>
      <button @click="$router.push('/newQuizGame/banks')">管理题库</button>
    </header>
    <section class="hero">
      <p>题库驱动的实时多人抢答</p>
      <h2>准备好，用知识和速度赢下比赛</h2>
      <button class="primary" :disabled="store.creatingRoom" @click="create">
        创建房间</button
      ><button @click="load">刷新</button>
    </section>
    <section class="rooms">
      <button v-for="room in store.rooms" :key="room.id" @click="join(room.id)">
        <b>{{ room.name }}</b
        ><span>{{ room.owner }}</span
        ><span>{{ room.players.length }} / {{ room.maxPlayers }}</span>
      </button>
      <p v-if="!store.rooms.length">暂无房间</p>
    </section>
    <p class="error">{{ store.notice }}</p>
  </main>
</template>
<script setup>
import { onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useNewQuizGameStore } from '@/stores/newQuizGameStore';
const store = useNewQuizGameStore(),
  router = useRouter();
watch(
  () => store.room_id,
  (id) => {
    if (id) router.push(`/newQuizGame/room/${id}`);
  }
);
async function create() {
  try {
    await store.createRoom();
  } catch (e) {
    store.notice = e.response?.data?.detail || e.message;
  }
}
async function join(id) {
  try {
    await store.enterRoom(id);
  } catch (e) {
    store.notice = e.response?.data?.detail || e.message;
  }
}
async function load() {
  try {
    await store.fetchRooms();
  } catch (e) {
    store.notice = e.message;
  }
}
onMounted(load);
</script>
<style scoped>
.page {
  min-height: 100vh;
  padding: 28px;
  background: #f3f0ff;
  color: #241b45;
  font-family: system-ui;
}
header {
  max-width: 960px;
  margin: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hero,
.rooms {
  max-width: 820px;
  margin: 35px auto;
}
.hero {
  text-align: center;
  padding: 52px;
  border-radius: 28px;
  background: linear-gradient(135deg, #5c45d8, #9e57d9);
  color: #fff;
}
.hero h2 {
  font-size: clamp(30px, 6vw, 55px);
}
button {
  padding: 11px 18px;
  border: 0;
  border-radius: 12px;
  cursor: pointer;
}
.hero button {
  margin: 5px;
}
.primary {
  background: #ffe66d;
  font-weight: 900;
}
.rooms {
  display: grid;
  gap: 10px;
}
.rooms button {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  text-align: left;
  background: #fff;
}
.error {
  color: #b42318;
  text-align: center;
}
</style>
