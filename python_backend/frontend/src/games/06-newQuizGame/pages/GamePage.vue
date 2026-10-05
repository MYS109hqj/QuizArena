<template>
  <main class="game-page">
    <header class="game-meta"><span>{{ state.bank_title }}</span><b>第 {{ state.question_index + 1 }} / {{ state.question_count }} 题</b><span class="timer">{{ secondsLeft }}s</span></header>
    <section v-if="state.state === 'finished'" class="final-card">
      <p class="eyebrow">GAME OVER</p><h1>最终排行榜</h1>
      <ol><li v-for="(id,index) in state.ranking" :key="id"><span class="place">{{ index+1 }}</span><b>{{ state.players[id]?.name }}</b><strong>{{ state.scores[id] }} 分</strong></li></ol>
      <button class="primary" @click="exit">返回大厅</button>
    </section>
    <template v-else-if="state.question">
      <section class="quiz-shell">
        <div class="prompt"><p>{{ state.question.type==='multi_hint'?'题目：':'提示：' }}</p><h1>{{ state.question.prompt }}<span v-if="state.question.type==='streaming_text'" class="cursor">▍</span></h1><small v-if="state.flow?.stage_count">第 {{ state.flow.stage }} / {{ state.flow.stage_count }} 阶段</small></div>
        <SubmissionToastStack :events="currentEvents" :submitted="submittedCount" :total="playerCount" />
        <section v-if="['jianying','single_choice','multi_hint'].includes(state.question.type)" class="stage">
          <JianyingBoard v-if="state.question.type === 'jianying'" :board="state.question.hint_board" />
          <div v-else-if="state.question.type === 'single_choice'" class="options">
            <button v-for="option in state.question.options" :key="option.id" :disabled="!canAnswer" :class="{ selected:selectedOption===option.id, correct:result?.question.correct_option_id===option.id }" @click="selectedOption=option.id"><b>{{ option.id }}</b><span>{{ option.text }}</span></button>
          </div>
          <ol v-else-if="state.question.type === 'multi_hint'" class="hints"><li v-for="(hint,index) in state.question.visible_hints" :key="index"><b>{{ index+1 }}</b><span>{{ hint }}</span></li></ol>
        </section>
        <form class="answer-bar" @submit.prevent="submit">
          <label>你的答案：</label>
          <input v-if="state.question.type !== 'single_choice'" v-model="textAnswer" :disabled="!canAnswer" maxlength="200" required autocomplete="off" :placeholder="answerPermission?.reason || '请输入答案'" />
          <div v-else class="choice-value">{{ selectedOption ? `已选择 ${selectedOption}` : '请先选择一个选项' }}</div>
          <button class="primary" :disabled="!canSubmit">提交</button>
        </form>
        <p v-if="store.answerFeedback" class="feedback" :class="{ success:store.answerFeedback.correct }">{{ store.answerFeedback.message }}<span v-if="store.answerFeedback.can_retry"> · 第 {{ store.answerFeedback.attempt_count }} 次尝试</span></p>
        <section v-if="result" class="result"><h2>正确答案：{{ correctAnswer }}</h2><p>{{ result.question.explanation }}</p><ol><li v-for="row in resultRows" :key="row.id"><span>{{ row.name }}</span><b>{{ row.reason }} · +{{ row.score }}</b></li></ol></section>
      </section>
      <PlayerStatusDrawer :players="state.players" :scores="state.scores" :submitted-ids="state.submitted_player_ids" />
    </template>
  </main>
</template>
<script setup>
import { computed,onMounted,onUnmounted,ref,watch } from 'vue';
import { useRoute,useRouter } from 'vue-router';
import { useNewQuizGameStore } from '@/stores/newQuizGameStore';
import JianyingBoard from '../components/JianyingBoard.vue';
import PlayerStatusDrawer from '../components/PlayerStatusDrawer.vue';
import SubmissionToastStack from '../components/SubmissionToastStack.vue';
const store=useNewQuizGameStore(),route=useRoute(),router=useRouter(),now=ref(Date.now()),textAnswer=ref(''),selectedOption=ref(''); let timer;
const state=computed(()=>store.gameState), submitted=computed(()=>(state.value.submitted_player_ids||[]).map(String).includes(String(store.player_id))), answerPermission=computed(()=>state.value.answer_permissions?.[store.player_id]), canAnswer=computed(()=>state.value.phase==='answering'&&!submitted.value&&(answerPermission.value?.can_submit??true)), submittedCount=computed(()=>state.value.submitted ?? state.value.submitted_player_ids?.length ?? 0), playerCount=computed(()=>state.value.total ?? Object.keys(state.value.players||{}).length), currentEvents=computed(()=>store.submissionEvents.filter(event=>String(event.question_id)===String(state.value.question?.id))), result=computed(()=>store.latestResult?.question?.id===state.value.question?.id?store.latestResult:null), secondsLeft=computed(()=>Math.max(0,Math.ceil((state.value.question_closes_at_ms-(now.value+store.timeOffsetMs))/1000))), canSubmit=computed(()=>canAnswer.value&&(state.value.question.type==='single_choice'?!!selectedOption.value:!!textAnswer.value.trim())), correctAnswer=computed(()=>result.value?.question.correct_option_id||(result.value?.question.accepted_answers||[]).join(' / ')), resultRows=computed(()=>result.value?Object.entries(result.value.results).map(([id,x])=>({id,name:state.value.players[id]?.name||id,...x})).sort((a,b)=>(a.rank||999)-(b.rank||999)):[]);
watch(()=>state.value.question?.id,()=>{store.latestResult=null;store.answerFeedback=null;textAnswer.value='';selectedOption.value=''});
function submit(){if(!canSubmit.value)return;store.submitAnswer(state.value.question.type==='single_choice'?selectedOption.value:textAnswer.value.trim());if(state.value.question.type!=='single_choice')textAnswer.value=''}
async function exit(){await store.leaveRoom();router.push('/newQuizGame')}
onMounted(async()=>{if(!store.room_id)await store.enterRoom(route.params.roomId);store.syncTime();timer=setInterval(()=>now.value=Date.now(),200)});onUnmounted(()=>clearInterval(timer));
</script>
<style scoped>
.game-page{min-height:100vh;padding:20px 300px 48px 28px;background:radial-gradient(circle at 20% 0,#646cba 0,#252b55 40%,#11162e 100%);color:#fff;font-family:Inter,"Microsoft YaHei",system-ui}.game-meta{display:flex;align-items:center;justify-content:space-between;max-width:1050px;margin:auto;color:#dce0fa}.timer{min-width:66px;padding:8px 14px;border-radius:20px;background:#ffffff18;text-align:center;font-weight:900}.quiz-shell,.final-card{max-width:1050px;margin:22px auto;padding:34px;border:1px solid #ffffff70;border-radius:32px;background:#fdfdfff5;color:#202644;box-shadow:0 30px 90px #070b20aa}.quiz-shell{display:grid;grid-template-columns:1fr auto;gap:25px;align-items:start}.prompt p{margin:0;color:#747b9c;font-weight:800}.prompt h1{margin:8px 0 0;font-size:clamp(24px,3vw,40px)}.prompt small{color:#6b7191}.cursor{color:#655ef3;animation:blink .8s steps(1) infinite}.stage{grid-column:1/-1;display:grid;place-items:center;min-height:330px;padding:20px;border:2px solid #e4e7f4;border-radius:23px;background:#f6f7fc}.options{width:min(760px,100%);display:grid;grid-template-columns:1fr 1fr;gap:14px}.options button{display:flex;align-items:center;gap:13px;min-height:76px;padding:14px;border:2px solid #dfe3f3;border-radius:15px;background:#fff;color:#242a4a;text-align:left;font-size:17px;cursor:pointer}.options button.selected{border-color:#645df4;background:#f0efff;box-shadow:0 0 0 3px #645df41b}.options button.correct{border-color:#29a66a;background:#ecfff5}.options button b,.hints li b{display:grid;place-items:center;flex:0 0 34px;height:34px;border-radius:50%;background:#6660ef;color:#fff}.hints{display:grid;width:min(760px,100%);gap:12px;padding:0;list-style:none}.hints li{display:flex;align-items:center;gap:14px;padding:14px;border-radius:14px;background:#fff;box-shadow:0 5px 18px #20264412}.text-stage{color:#8a90aa;font-size:20px}.answer-bar{grid-column:1/-1;display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center}.answer-bar label{font-size:20px;font-weight:900}.answer-bar input,.choice-value{min-height:50px;box-sizing:border-box;padding:13px 16px;border:2px solid #dfe3f3;border-radius:13px;background:#fff;font-size:17px}.choice-value{color:#7b819d}.primary{padding:14px 25px;border:0;border-radius:13px;background:linear-gradient(135deg,#655ef3,#5148d7);color:#fff;font-weight:900;cursor:pointer}.primary:disabled{opacity:.45;cursor:not-allowed}.feedback{grid-column:1/-1;margin:0;color:#c24747;font-weight:800}.feedback.success{color:#188657}.result{grid-column:1/-1;padding:20px;border-radius:16px;background:#ebfaf3}.result li,.final-card li{display:flex;justify-content:space-between;padding:10px}.final-card{max-width:700px;text-align:center}.final-card ol{padding:0;list-style:none}.final-card li{align-items:center;border-bottom:1px solid #eceefa}.place{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#eeeefe}.eyebrow{color:#6660ef;font-weight:900;letter-spacing:.2em}@keyframes blink{50%{opacity:0}}
@media(max-width:900px){.game-page{padding:15px 15px 110px}.quiz-shell{padding:22px;grid-template-columns:1fr}.prompt,.submission-live{grid-column:1}.stage{min-height:250px}.options{grid-template-columns:1fr}.answer-bar{grid-template-columns:1fr}.answer-bar label{font-size:17px}.game-meta{font-size:13px}}
</style>
