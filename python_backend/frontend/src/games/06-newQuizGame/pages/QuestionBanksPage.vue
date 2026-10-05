<template>
  <main class="page">
    <nav class="main-tabs"><b>NEW QUIZ</b><button @click="$router.push('/newQuizGame')">游戏大厅</button><button class="active">题库</button><button disabled>我的记录</button></nav>
    <header class="toolbar">
      <div><strong>{{ selected?.title || '题库' }}</strong><span :class="saveState">{{ saveLabel }}</span></div>
      <div class="actions"><button @click="createBank">＋ 新建题库</button><button :disabled="!selected" @click="saveBank">保存</button><button class="primary" :disabled="!selected" @click="publish">发布新版本</button></div>
    </header>
    <section class="workspace">
      <aside class="banks panel">
        <div class="panel-title"><span>我的题库</span><small>{{ banks.length }}</small></div>
        <button v-for="bank in banks" :key="bank.id" :class="{ selected:selected?.id===bank.id }" @click="select(bank)"><b>{{ bank.title }}</b><small>{{ bank.status==='published'?'已发布':'草稿' }} · v{{ bank.current_version }}</small></button>
        <p v-if="!banks.length" class="empty-small">还没有题库</p>
      </aside>
      <aside class="questions panel">
        <div class="panel-title"><span>题目</span><button :disabled="!selected" @click="newQuestion">＋</button></div>
        <template v-if="selected">
          <button class="bank-settings" :class="{ selected:editorMode==='bank' }" @click="showBankSettings">⚙ 题库设置</button>
          <button v-for="(question,index) in selected.questions" :key="question.id" :class="{ selected:editingId===question.id }" @click="editQuestion(question)"><span class="index">{{ index+1 }}</span><span><b>{{ question.prompt }}</b><small>{{ typeLabel(question.type) }}</small></span></button>
          <button class="add-question" @click="newQuestion">＋ 添加题目</button>
        </template>
        <p v-else class="empty-small">先选择一个题库</p>
      </aside>
      <section class="editor panel" v-if="selected">
        <form v-if="editorMode==='bank'" class="form" @submit.prevent="saveBank">
          <div class="editor-heading"><div><p>题库设置</p><h1>{{ selected.title }}</h1></div><span class="badge">{{ selected.questions.length }} 道题</span></div>
          <label>题库名称<input v-model="selected.title" required maxlength="120" /></label>
          <label>题库简介<textarea v-model="selected.description" rows="5" placeholder="介绍这个题库的主题和用途"></textarea></label>
          <label>可见性<select v-model="selected.visibility"><option value="private">私有</option><option value="unlisted">链接可用</option><option value="public">公开</option></select></label>
          <button class="primary">保存题库设置</button>
        </form>
        <form v-else class="form" @submit.prevent="saveQuestion">
          <div class="editor-heading"><div><p>{{ editingId?'编辑题目':'新建题目' }}</p><h1>{{ typeLabel(draft.question_type) }}</h1></div><button v-if="editingId" type="button" class="danger" @click="removeQuestion(editingId)">删除</button></div>
          <label>题型<select v-model="draft.question_type"><option value="single_choice">单选题</option><option value="text">普通问答题</option><option value="jianying">鉴影问答题</option><option value="multi_hint">多提示题</option><option value="streaming_text">流文本题</option></select></label>
          <label>题目提示<textarea v-model="draft.prompt" required rows="3" placeholder="输入玩家看到的题目或提示"></textarea></label>
          <template v-if="draft.question_type==='single_choice'">
            <fieldset><legend>选项</legend><label v-for="(_,index) in draft.options" :key="index" class="option-row"><input type="radio" v-model.number="draft.correct_option_index" :value="index" /><b>{{ String.fromCharCode(65+index) }}</b><input v-model="draft.options[index]" required :placeholder="`选项 ${String.fromCharCode(65+index)}`" /></label></fieldset>
          </template>
          <template v-else>
            <label>标准答案<input v-model="primaryAnswer" required placeholder="鉴影题将使用此答案生成题板" /></label>
            <label>其他可接受答案<textarea v-model="alternativeAnswers" rows="3" placeholder="每行一个，可留空"></textarea></label>
            <div v-if="draft.question_type==='jianying'" class="jianying-note"><b>鉴影题板</b><span>发布时按“5块 · 最小不失真 · 慢速”生成；作答阶段不会向浏览器发送答案。</span></div>
            <fieldset v-if="draft.question_type==='multi_hint'"><legend>六个阶段提示</legend><label v-for="(_,index) in draft.hints" :key="index">提示 {{ index+1 }}<input v-model="draft.hints[index]" required :placeholder="`第 ${index+1} 个提示`" /></label><label>提示间隔（秒）<input v-model.number="draft.hint_interval_seconds" type="number" min="1" max="300" required /></label></fieldset>
            <fieldset v-if="draft.question_type==='streaming_text'"><legend>流文本设置</legend><label>每字间隔（毫秒）<input v-model.number="draft.character_interval_ms" type="number" min="20" max="5000" required /></label><label>流完后答题时间（秒）<input v-model.number="draft.answer_time_after_reveal_seconds" type="number" min="0" max="300" required /></label></fieldset>
          </template>
          <label>答案解析<textarea v-model="draft.explanation" rows="3" placeholder="本题结束后展示"></textarea></label>
          <div class="form-actions"><button class="primary">{{ editingId?'保存题目':'添加题目' }}</button><button type="button" @click="showBankSettings">取消</button></div>
        </form>
      </section>
      <section v-else class="editor panel empty">选择或创建一个题库开始编辑</section>
    </section>
    <div v-if="message" class="message">{{ message }}</div>
  </main>
</template>
<script setup>
import { computed,onMounted,reactive,ref } from 'vue'; import axios from 'axios';
const API=import.meta.env.VITE_URL||'',banks=ref([]),selected=ref(null),message=ref(''),editingId=ref(null),editorMode=ref('bank'),savedAt=ref(null),saving=ref(false),primaryAnswer=ref(''),alternativeAnswers=ref('');
const draft=reactive({question_type:'single_choice',prompt:'',options:['','','',''],correct_option_index:0,explanation:'',default_score:10,accepted_answers:[],hints:['','','','','',''],hint_interval_seconds:20,character_interval_ms:120,answer_time_after_reveal_seconds:10});
const saveState=computed(()=>saving.value?'saving':savedAt.value?'saved':''),saveLabel=computed(()=>saving.value?'正在保存…':savedAt.value?`已保存 · ${savedAt.value.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}`:'尚未保存');
async function load(){const{data}=await axios.get(`${API}/api/new-quiz/banks`);banks.value=data.banks||[]}
async function select(bank){const{data}=await axios.get(`${API}/api/new-quiz/banks/${bank.id}`);selected.value=data;showBankSettings()}
async function createBank(){const{data}=await axios.post(`${API}/api/new-quiz/banks`,{title:'未命名题库',description:'',visibility:'private'});await load();await select(data)}
async function saveBank(){if(!selected.value)return;saving.value=true;try{await axios.put(`${API}/api/new-quiz/banks/${selected.value.id}`,{title:selected.value.title,description:selected.value.description,visibility:selected.value.visibility});savedAt.value=new Date();message.value='题库已保存';await load()}finally{saving.value=false}}
function showBankSettings(){editorMode.value='bank';editingId.value=null}
function newQuestion(){if(!selected.value)return;editorMode.value='question';editingId.value=null;primaryAnswer.value='';alternativeAnswers.value='';Object.assign(draft,{question_type:'single_choice',prompt:'',options:['','','',''],correct_option_index:0,explanation:'',default_score:10,accepted_answers:[],hints:['','','','','',''],hint_interval_seconds:20,character_interval_ms:120,answer_time_after_reveal_seconds:10})}
function editQuestion(question){editorMode.value='question';editingId.value=question.id;const answers=question.accepted_answers||[],content=question.content||{};primaryAnswer.value=answers[0]||'';alternativeAnswers.value=answers.slice(1).join('\n');Object.assign(draft,{question_type:question.type,prompt:question.prompt,options:question.options?.map(option=>option.text)||['','','',''],correct_option_index:Math.max(0,question.options?.findIndex(option=>option.id===question.correct_option_id)??0),explanation:question.explanation||'',default_score:question.default_score||10,hints:content.hints||['','','','','',''],hint_interval_seconds:content.hint_interval_seconds||20,character_interval_ms:content.character_interval_ms||120,answer_time_after_reveal_seconds:content.answer_time_after_reveal_seconds??10})}
async function saveQuestion(){const endpoint=`${API}/api/new-quiz/banks/${selected.value.id}/questions`,accepted=[primaryAnswer.value,...alternativeAnswers.value.split('\n')].map(value=>value.trim()).filter(Boolean),payload={...draft,accepted_answers:accepted};if(editingId.value)await axios.put(`${endpoint}/${editingId.value}`,payload);else await axios.post(endpoint,payload);savedAt.value=new Date();message.value=editingId.value?'题目已保存':'题目已添加';const id=selected.value.id;await select({id});}
async function removeQuestion(id){if(!confirm('确定删除这道题吗？'))return;await axios.delete(`${API}/api/new-quiz/banks/${selected.value.id}/questions/${id}`);message.value='题目已删除';await select({id:selected.value.id})}
async function publish(){try{const{data}=await axios.post(`${API}/api/new-quiz/banks/${selected.value.id}/publish`);message.value=`已发布 v${data.version} · 共 ${data.question_count} 道题`;savedAt.value=new Date();await load();await select({id:selected.value.id})}catch(error){message.value=error.response?.data?.detail||'发布失败'}}
function typeLabel(type){return({single_choice:'单选题',text:'普通问答题',jianying:'鉴影问答题',multi_hint:'多提示题',streaming_text:'流文本题'})[type]||type}
onMounted(load);
</script>
<style scoped>
.page{min-height:100vh;background:#f4f6fb;color:#222944;font-family:Inter,"Microsoft YaHei",system-ui}.main-tabs{height:66px;display:flex;align-items:center;gap:8px;padding:0 30px;border-bottom:1px solid #e3e6ef;background:#fff}.main-tabs b{margin-right:35px;color:#5f59e7;letter-spacing:.1em}.main-tabs button{height:100%;padding:0 22px;border:0;border-bottom:3px solid transparent;background:none;color:#666d87;cursor:pointer}.main-tabs button.active{border-color:#625ced;color:#242a4a;font-weight:900}.toolbar{position:sticky;z-index:10;top:0;display:flex;align-items:center;justify-content:space-between;padding:14px 30px;border-bottom:1px solid #dfe3ed;background:#ffffffed;box-shadow:0 8px 25px #1c23400d;backdrop-filter:blur(15px)}.toolbar>div:first-child{display:flex;align-items:center;gap:16px}.toolbar span{color:#8a90a8;font-size:13px}.toolbar span.saved{color:#1b865b}.actions,.form-actions{display:flex;gap:9px}.workspace{display:grid;grid-template-columns:230px 270px minmax(420px,1fr);gap:16px;max-width:1400px;margin:auto;padding:22px}.panel{border:1px solid #e0e4ee;border-radius:17px;background:#fff;box-shadow:0 10px 35px #2831530a}.banks,.questions{display:flex;flex-direction:column;gap:7px;min-height:calc(100vh - 155px);padding:14px}.panel-title{display:flex;align-items:center;justify-content:space-between;padding:8px;font-weight:900}.panel-title small{display:grid;place-items:center;min-width:25px;height:25px;border-radius:13px;background:#eef0fa}.panel-title button{padding:3px 9px;font-size:20px}.banks>button,.questions>button{display:grid;gap:4px;padding:12px;border:1px solid transparent;border-radius:11px;background:transparent;color:#282e4a;text-align:left;cursor:pointer}.banks>button:hover,.questions>button:hover,.banks>button.selected,.questions>button.selected{border-color:#dcdafb;background:#f0efff}.banks small,.questions small{color:#888fa8}.questions>button{grid-template-columns:auto 1fr;align-items:center}.questions .index{display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:#eff1f8;color:#6d7390}.questions .bank-settings,.questions .add-question{display:block;border:1px dashed #d8dce8}.editor{min-height:calc(100vh - 155px);padding:30px}.form{display:grid;gap:20px;max-width:780px}.editor-heading{display:flex;align-items:start;justify-content:space-between;padding-bottom:15px;border-bottom:1px solid #eceef4}.editor-heading p{margin:0;color:#777e99}.editor-heading h1{margin:5px 0}.badge{padding:8px 12px;border-radius:20px;background:#eeedff;color:#5f59e7}.form>label{display:grid;gap:8px;font-weight:800}.form input,.form textarea,.form select{box-sizing:border-box;width:100%;padding:12px;border:1px solid #d8dce8;border-radius:10px;background:#fff;font:inherit;font-weight:400}.form input:focus,.form textarea:focus,.form select:focus{outline:3px solid #625ced20;border-color:#625ced}fieldset{display:grid;gap:9px;border:1px solid #e1e4ed;border-radius:13px}.option-row{display:grid;grid-template-columns:auto 30px 1fr;align-items:center}.option-row>input:first-child{width:auto}.jianying-note{display:grid;gap:5px;padding:16px;border:1px solid #d8d4ff;border-radius:13px;background:#f1f0ff;color:#57518a}.jianying-note span{font-size:14px}.primary{border:0;background:#625ced!important;color:#fff!important;font-weight:900}.danger{color:#b83232!important;background:#fff0f0!important}button{padding:10px 14px;border:1px solid #dfe2eb;border-radius:9px;background:#fff;color:#343a56;cursor:pointer}button:disabled{opacity:.45;cursor:not-allowed}.empty,.empty-small{display:grid;place-items:center;color:#9298ad}.message{position:fixed;z-index:30;left:50%;bottom:25px;transform:translateX(-50%);padding:12px 20px;border-radius:30px;background:#202744;color:#fff;box-shadow:0 10px 30px #151b3666}
@media(max-width:950px){.workspace{grid-template-columns:200px 1fr}.questions{grid-column:1}.editor{grid-column:2;grid-row:1/3}.banks,.questions{min-height:auto}.main-tabs{padding:0 12px}.main-tabs b{margin-right:5px}.main-tabs button{padding:0 10px}.toolbar{padding:12px 16px}}
@media(max-width:680px){.workspace{display:block;padding:10px}.panel{margin-bottom:10px}.editor{padding:20px}.toolbar{align-items:start;gap:10px}.toolbar,.actions{flex-wrap:wrap}.main-tabs b{display:none}}
</style>
