<template>
  <main class="page">
    <header>
      <span>{{ state.bank_title }}</span
      ><b>第 {{ state.question_index + 1 }} / {{ state.question_count }} 题</b
      ><span>{{ secondsLeft }}s</span>
    </header>
    <section v-if="state.state === 'finished'" class="card final">
      <h1>最终排行榜</h1>
      <ol>
        <li v-for="id in state.ranking" :key="id">
          <b>{{ state.players[id]?.name }}</b
          ><span>{{ state.scores[id] }} 分</span>
        </li>
      </ol>
      <button @click="exit">返回大厅</button>
    </section>
    <section v-else-if="state.question" class="card">
      <p class="phase">
        {{ state.phase === 'result' ? '本题结果' : '请选择答案' }}
      </p>
      <h1>{{ state.question.prompt }}</h1>
      <JianyingBoard v-if="state.question.type === 'jianying'" :board="state.question.hint_board" />
      <div v-if="state.question.type === 'single_choice'" class="options">
        <button
          v-for="option in state.question.options"
          :key="option.id"
          :disabled="submitted || state.phase !== 'answering'"
          :class="optionClass(option.id)"
          @click="answer(option.id)"
        >
          <b>{{ option.id }}</b
          >{{ option.text }}
        </button>
      </div>
      <form v-else class="text-answer" @submit.prevent="answerText">
        <input v-model="textAnswer" :disabled="submitted || state.phase !== 'answering'"
          maxlength="200" required autocomplete="off" placeholder="输入答案" />
        <button :disabled="submitted || state.phase !== 'answering'">提交答案</button>
      </form>
      <p v-if="store.answerFeedback" :class="{ success: store.answerFeedback.correct }">
        {{ store.answerFeedback.message }}<span v-if="store.answerFeedback.can_retry">（第 {{ store.answerFeedback.attempt_count }} 次尝试）</span>
      </p>
      <p v-if="submitted">答案已提交，等待其他玩家</p>
      <section v-if="result" class="result">
        <h2>正确答案：{{ correctAnswer }}</h2>
        <p>{{ result.question.explanation }}</p>
        <ol>
          <li v-for="row in resultRows" :key="row.id">
            <span>{{ row.name }}</span
            ><b>{{ row.reason }} · +{{ row.score }}</b>
          </li>
        </ol>
      </section>
    </section>
    <aside>
      <h3>实时分数</h3>
      <p v-for="(player, id) in state.players" :key="id">
        <span>{{ player.name }}</span
        ><b>{{ state.scores[id] || 0 }}</b>
      </p>
    </aside>
  </main>
</template>
<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useNewQuizGameStore } from '@/stores/newQuizGameStore';
import JianyingBoard from '../components/JianyingBoard.vue';
const store = useNewQuizGameStore(),
  route = useRoute(),
  router = useRouter(),
  now = ref(Date.now()), textAnswer = ref('');
let timer;
const state = computed(() => store.gameState),
  submitted = computed(() =>
    (state.value.submitted_player_ids || [])
      .map(String)
      .includes(String(store.player_id))
  ),
  result = computed(() =>
    store.latestResult?.question?.id === state.value.question?.id
      ? store.latestResult
      : null
  ),
  secondsLeft = computed(() =>
    Math.max(
      0,
      Math.ceil(
        (state.value.question_closes_at_ms - (now.value + store.timeOffsetMs)) /
          1000
      )
    )
  ),
  resultRows = computed(() =>
    result.value
      ? Object.entries(result.value.results)
          .map(([id, x]) => ({
            id,
            name: state.value.players[id]?.name || id,
            ...x,
          }))
          .sort((a, b) => (a.rank || 999) - (b.rank || 999))
      : []
  ), correctAnswer = computed(() => result.value?.question.correct_option_id ||
    (result.value?.question.accepted_answers || []).join(' / '));
watch(
  () => state.value.question?.id,
  () => {
    store.latestResult = null;
    store.answerFeedback = null;
    textAnswer.value = '';
  }
);
function answer(id) {
  store.submitAnswer(id);
}
function answerText() { const value=textAnswer.value.trim(); if(value){store.submitAnswer(value);textAnswer.value='';} }
function optionClass(id) {
  return { correct: result.value?.question.correct_option_id === id };
}
async function exit() {
  await store.leaveRoom();
  router.push('/newQuizGame');
}
onMounted(async () => {
  if (!store.room_id) await store.enterRoom(route.params.roomId);
  store.syncTime();
  timer = setInterval(() => (now.value = Date.now()), 200);
});
onUnmounted(() => clearInterval(timer));
</script>
<style scoped>
.page {
  min-height: 100vh;
  padding: 22px;
  background: radial-gradient(circle at top, #6c54db, #21183e 70%);
  color: #fff;
  font-family: system-ui;
}
header {
  max-width: 850px;
  margin: auto;
  display: flex;
  justify-content: space-between;
}
.card {
  max-width: 760px;
  margin: 35px auto;
  padding: 35px;
  border-radius: 26px;
  background: #fff;
  color: #241c43;
  box-shadow: 0 25px 70px #160d32;
}
.phase {
  text-transform: uppercase;
  color: #705bd0;
  font-weight: 900;
}
.options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.options button {
  min-height: 75px;
  padding: 15px;
  text-align: left;
  border: 2px solid #ded8f7;
  border-radius: 14px;
  background: #f8f7ff;
  font-size: 17px;
}
.options button b {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  margin-right: 12px;
  border-radius: 50%;
  background: #6c54db;
  color: #fff;
}
.options button.correct {
  border-color: #2fa66a;
  background: #e9fff2;
}
.text-answer { display:flex; gap:10px; margin-top:20px; }
.text-answer input { flex:1; padding:14px; border:2px solid #ded8f7; border-radius:12px; font-size:18px; }
.text-answer button { padding:0 22px; border:0; border-radius:12px; background:#6c54db; color:#fff; font-weight:800; }
.success { color:#18794e; font-weight:800; }
.result {
  margin-top: 20px;
  padding: 18px;
  border-radius: 15px;
  background: #eefaf3;
}
.result li,
.final li,
aside p {
  display: flex;
  justify-content: space-between;
  padding: 8px;
}
aside {
  position: fixed;
  right: 15px;
  top: 80px;
  width: 190px;
  padding: 16px;
  border-radius: 18px;
  background: #17102dcc;
}
.final button {
  padding: 11px 18px;
}
@media (max-width: 1050px) {
  aside {
    position: static;
    max-width: 760px;
    width: auto;
    margin: auto;
  }
  .options {
    grid-template-columns: 1fr;
  }
}
</style>
