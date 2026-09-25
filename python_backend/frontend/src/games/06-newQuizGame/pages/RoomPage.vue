<template>
  <main class="page">
    <section class="panel">
      <p>房间 {{ route.params.roomId }}</p>
      <h1>抢答准备室</h1>
      <div class="players">
        <article v-for="(p, id) in store.players" :key="id">
          <b>{{ p.name }}</b
          ><small>{{
            String(id) === String(store.room.owner?.id)
              ? '房主'
              : p.ready
                ? '已准备'
                : '未准备'
          }}</small>
        </article>
      </div>
      <section class="settings">
        <label
          >题库<select
            v-model="rules.bank_id"
            :disabled="!owner"
            @change="save"
          >
            <option :value="null">请选择</option>
            <option v-for="bank in store.banks" :key="bank.id" :value="bank.id">
              {{ bank.title }} · v{{ bank.current_version }}
            </option>
          </select></label
        ><label
          >题目数<input
            v-model.number="rules.question_count"
            type="number"
            min="1"
            max="100"
            :disabled="!owner"
            @change="save" /></label
        ><label
          >每题时间<input
            v-model.number="rules.time_limit_seconds"
            type="number"
            min="5"
            max="300"
            :disabled="!owner"
            @change="save" /></label
        ><label
          ><input
            v-model="rules.random_order"
            type="checkbox"
            :disabled="!owner"
            @change="save"
          />随机题序</label
        >
      </section>
      <button v-if="!owner" class="primary" @click="store.toggleReady()">
        {{ me?.ready ? '取消准备' : '准备' }}</button
      ><button
        v-else
        class="primary"
        :disabled="!canStart"
        @click="store.startGame()"
      >
        开始</button
      ><button @click="leave">离开</button>
      <p class="error">{{ store.notice }}</p>
    </section>
  </main>
</template>
<script setup>
import { computed, onMounted, reactive, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useNewQuizGameStore } from '@/stores/newQuizGameStore';
const store = useNewQuizGameStore(),
  route = useRoute(),
  router = useRouter(),
  rules = reactive({
    bank_id: null,
    question_count: 10,
    time_limit_seconds: 20,
    random_order: false,
  });
const owner = computed(
    () => String(store.room.owner?.id) === String(store.player_id)
  ),
  me = computed(() => store.players[store.player_id]),
  canStart = computed(
    () =>
      rules.bank_id &&
      Object.entries(store.players).every(
        ([id, p]) => String(id) === String(store.room.owner?.id) || p.ready
      )
  );
watch(
  () => store.room.rules,
  (r) => {
    if (r) Object.assign(rules, r);
  },
  { deep: true, immediate: true }
);
watch(
  () => store.gameStatus,
  (s) => {
    if (s === 'playing')
      router.push(`/newQuizGame/game/${route.params.roomId}`);
  }
);
function save() {
  if (owner.value) store.updateRules({ ...rules });
}
async function leave() {
  await store.leaveRoom();
  router.push('/newQuizGame');
}
onMounted(async () => {
  if (!store.room_id) await store.enterRoom(route.params.roomId);
  await store.fetchBanks();
});
</script>
<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #251d48;
  color: #fff;
  font-family: system-ui;
}
.panel {
  width: min(760px, 92vw);
  padding: 35px;
  border-radius: 25px;
  background: #352966;
}
.players {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
}
.players article,
.settings {
  padding: 16px;
  border-radius: 14px;
  background: #ffffff13;
}
.players article {
  display: grid;
}
.settings {
  display: grid;
  gap: 15px;
  margin: 22px 0;
}
.settings label {
  display: flex;
  justify-content: space-between;
}
.settings input,
.settings select {
  padding: 7px;
}
.primary {
  background: #ffe66d;
  font-weight: 900;
}
button {
  padding: 11px 18px;
  border: 0;
  border-radius: 10px;
  margin-right: 8px;
}
.error {
  color: #ffb4ab;
}
</style>
