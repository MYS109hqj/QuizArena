<template>
  <main class="page">
    <header>
      <button @click="$router.push('/newQuizGame')">← 游戏大厅</button>
      <h1>我的题库</h1>
      <button class="primary" @click="createBank">新建题库</button>
    </header>
    <section class="layout">
      <aside>
        <button
          v-for="bank in banks"
          :key="bank.id"
          :class="{ active: selected?.id === bank.id }"
          @click="select(bank)"
        >
          <b>{{ bank.title }}</b
          ><small>{{ bank.status }} · v{{ bank.current_version }}</small>
        </button>
      </aside>
      <section v-if="selected" class="editor">
        <label>名称<input v-model="selected.title" /></label
        ><label>简介<textarea v-model="selected.description"></textarea></label
        ><label
          >可见性<select v-model="selected.visibility">
            <option value="private">私有</option>
            <option value="unlisted">链接可用</option>
            <option value="public">公开</option>
          </select></label
        >
        <div>
          <button @click="saveBank">保存</button
          ><button class="primary" @click="publish">发布新版本</button>
        </div>
        <h2>题目</h2>
        <article v-for="q in selected.questions" :key="q.id">
          <b>{{ q.prompt }}</b
          ><span>{{ typeLabel(q.type) }} · 答案 {{ answerLabel(q) }}</span
          ><button @click="editQuestion(q)">编辑</button
          ><button @click="removeQuestion(q.id)">删除</button>
        </article>
        <form @submit.prevent="addQuestion">
          <h3>{{ editingId ? '编辑题目' : '添加题目' }}</h3>
          <label>题型<select v-model="draft.question_type">
            <option value="single_choice">单选题</option><option value="text">普通问答题</option>
            <option value="jianying">鉴影问答题</option></select></label>
          <input v-model="draft.prompt" required placeholder="题干" /><input
            v-if="draft.question_type === 'single_choice'"
            v-for="(_, i) in draft.options"
            :key="i"
            v-model="draft.options[i]"
            required
            :placeholder="`选项 ${String.fromCharCode(65 + i)}`"
          /><label v-if="draft.question_type === 'single_choice'"
            >正确选项<select v-model.number="draft.correct_option_index">
              <option v-for="(_, i) in draft.options" :key="i" :value="i">
                {{ String.fromCharCode(65 + i) }}
              </option>
            </select></label>
          <label v-else>可接受答案（每行一个，第一行用于生成鉴影题板）
            <textarea v-model="draft.answersText" required placeholder="标准答案"></textarea></label
          ><textarea
            v-model="draft.explanation"
            placeholder="答案解析"
          ></textarea
          ><button class="primary">
            {{ editingId ? '保存题目' : '添加题目' }}</button
          ><button v-if="editingId" type="button" @click="resetDraft">
            取消编辑
          </button>
        </form>
      </section>
      <section v-else class="empty">选择或创建一个题库</section>
    </section>
    <p class="message">{{ message }}</p>
  </main>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue';
import axios from 'axios';
const API = import.meta.env.VITE_URL || '',
  banks = ref([]),
  selected = ref(null),
  message = ref(''),
  editingId = ref(null),
  draft = reactive({
    question_type: 'single_choice',
    prompt: '',
    options: ['', '', '', ''],
    correct_option_index: 0,
    explanation: '',
    default_score: 10,
    accepted_answers: [],
    answersText: '',
  });
async function load() {
  const { data } = await axios.get(`${API}/api/new-quiz/banks`);
  banks.value = data.banks || [];
}
async function select(bank) {
  const { data } = await axios.get(`${API}/api/new-quiz/banks/${bank.id}`);
  selected.value = data;
}
async function createBank() {
  const { data } = await axios.post(`${API}/api/new-quiz/banks`, {
    title: '未命名题库',
    description: '',
    visibility: 'private',
  });
  await load();
  await select(data);
}
async function saveBank() {
  await axios.put(`${API}/api/new-quiz/banks/${selected.value.id}`, {
    title: selected.value.title,
    description: selected.value.description,
    visibility: selected.value.visibility,
  });
  message.value = '已保存';
  await load();
}
async function addQuestion() {
  const endpoint = `${API}/api/new-quiz/banks/${selected.value.id}/questions`;
  const payload = { ...draft, accepted_answers: draft.answersText.split('\n').map(x=>x.trim()).filter(Boolean) };
  if (editingId.value) await axios.put(`${endpoint}/${editingId.value}`, payload);
  else await axios.post(endpoint, payload);
  resetDraft();
  await select(selected.value);
}
function editQuestion(question) {
  editingId.value = question.id;
  Object.assign(draft, {
    question_type: question.type,
    prompt: question.prompt,
    options: question.options?.map((option) => option.text) || ['', '', '', ''],
    correct_option_index: question.options?.findIndex(
      (option) => option.id === question.correct_option_id
    ) || 0,
    answersText: (question.accepted_answers || []).join('\n'),
    explanation: question.explanation || '',
    default_score: question.default_score || 10,
  });
}
function resetDraft() {
  editingId.value = null;
  Object.assign(draft, {
    question_type: 'single_choice',
    prompt: '',
    options: ['', '', '', ''],
    correct_option_index: 0,
    explanation: '',
    default_score: 10,
    accepted_answers: [],
    answersText: '',
  });
}
function typeLabel(type) { return ({single_choice:'单选题',text:'问答题',jianying:'鉴影问答题'})[type] || type; }
function answerLabel(question) { return question.correct_option_id || (question.accepted_answers || []).join(' / '); }
async function removeQuestion(id) {
  await axios.delete(
    `${API}/api/new-quiz/banks/${selected.value.id}/questions/${id}`
  );
  if (editingId.value === id) resetDraft();
  await select(selected.value);
}
async function publish() {
  const { data } = await axios.post(
    `${API}/api/new-quiz/banks/${selected.value.id}/publish`
  );
  message.value = `已发布 v${data.version}`;
  await load();
  await select(selected.value);
}
onMounted(load);
</script>
<style scoped>
.page {
  min-height: 100vh;
  padding: 25px;
  background: #f5f3ff;
  color: #251d45;
  font-family: system-ui;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1100px;
  margin: auto;
}
.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  max-width: 1100px;
  margin: 30px auto;
}
aside,
.editor,
.empty {
  padding: 20px;
  border-radius: 18px;
  background: #fff;
}
aside {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
aside button {
  display: grid;
  text-align: left;
}
.active {
  outline: 3px solid #725bd5;
}
.editor {
  display: grid;
  gap: 13px;
}
.editor label,
.editor form {
  display: grid;
  gap: 7px;
}
.editor input,
.editor textarea,
.editor select {
  padding: 10px;
  border: 1px solid #d8d2ef;
  border-radius: 8px;
}
.editor article {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  gap: 10px;
  padding: 12px;
  background: #f5f3ff;
}
.editor form {
  padding: 18px;
  border: 1px solid #e1dcf7;
  border-radius: 14px;
}
button {
  padding: 10px 14px;
  border: 0;
  border-radius: 9px;
  cursor: pointer;
}
.primary {
  background: #6c54db;
  color: #fff;
  font-weight: 800;
}
.message {
  text-align: center;
  color: #317a50;
}
@media (max-width: 750px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
