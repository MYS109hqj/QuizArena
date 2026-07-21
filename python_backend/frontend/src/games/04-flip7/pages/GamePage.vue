<template>
  <main class="table" :class="{ 'round-ending': game.state === 'round_ending' }">
    <header>
      <button @click="exit">← 退出</button><div><h1>FLIP 7</h1><p>第 {{ game.round }} 轮 · {{ modeName }}</p></div>
      <div class="deck"><b>{{ game.remaining_cards }}</b><small>牌库</small></div>
    </header>

    <section class="players">
      <article v-for="(player,id) in store.players" :key="id" class="player" :class="playerClass(id)">
        <div class="player-head"><strong>{{ player.name }}</strong><b>{{ state(id).score }} 分</b></div>
        <div class="round-line"><span>本轮 {{ state(id).round_score }} 分</span><span>{{ state(id).flip7_count }}/7</span></div>
        <div v-if="probability(id)" class="probability" :title="`${probability(id).bust_cards}/${probability(id).remaining_cards} 张会立即爆牌`">下一张爆牌概率 {{ formatProbability(probability(id).probability) }}</div>
        <div class="hand">
          <div v-for="card in state(id).hand" :key="card.id" class="card mini" :class="[card.type, { 'face-down': card.face_down }]">
            <b>{{ card.name }}</b><small>{{ cardLabel(card) }}</small>
          </div><em v-if="!state(id).hand?.length">尚未翻牌</em>
        </div>
        <div class="badges"><span v-if="state(id).second_chances">Second Chance</span><span v-if="state(id).must_hit">必须翻牌</span><span v-if="state(id).busted">爆牌</span><span v-else-if="state(id).stopped">已停牌</span></div>
      </article>
    </section>

    <section class="center">
      <div v-if="game.state === 'round_ending'" class="round-ending-banner">本轮结束 · 正在收牌…</div>
      <p class="turn">{{ turnText }}</p>
      <div v-if="store.lastCard" class="card hero" :class="store.lastCard.card.type">
        <b>{{ store.lastCard.card.name }}</b><small>{{ cardLabel(store.lastCard.card) }}</small>
        <span v-if="store.lastCard.bust">爆牌</span><span v-else-if="store.lastCard.flip7">FLIP 7!</span><span v-else-if="store.lastCard.used_sc">化险为夷</span>
      </div><div v-else class="card hero back">7</div>
      <div class="controls"><button class="hit" :disabled="!canDraw" @click="store.drawCard()">翻一张</button><button class="stay" :disabled="!canStop" @click="store.stopTurn()">停牌</button></div>
    </section>

    <section class="history"><h2>本轮翻牌</h2><div><span v-for="(item,i) in store.roundHistory" :key="i" class="history-card" :class="item.card.type">{{ item.card.name }}</span></div></section>

    <div v-if="myPending" class="overlay"><article class="modal"><h2>{{ effectTitle }}</h2><p>选择目标{{ needsCard ? '及卡牌' : '' }}</p>
      <template v-if="myPending.type === 'swap'">
        <div class="swap-board"><div v-for="id in myPending.targets" :key="id" class="target"><strong>{{ store.getPlayerName(id) }}</strong>
          <button v-for="c in state(id).hand" :key="c.id" class="swap-card" :class="{ selected: isSwapSelected(id,c.id) }" @click="toggleSwap(id,c)">{{ c.name }}<small>{{ cardLabel(c) }}</small></button>
        </div></div>
        <p>请选择两名不同玩家各一张正面朝上的牌。</p>
        <button class="confirm-swap" :disabled="!swapReady" @click="confirmSwap">交换所选卡牌</button>
      </template>
      <div v-else class="targets"><div v-for="id in myPending.targets" :key="id" class="target"><strong>{{ store.getPlayerName(id) }}</strong>
        <template v-if="needsCard"><button v-for="c in state(id).hand" :key="c.id" @click="choose(id,c.id)">{{ c.name }}</button><button v-if="!state(id).hand?.length" @click="choose(id,null)">选择玩家</button></template>
        <button v-else @click="choose(id,null)">选择</button>
      </div></div>
    </article></div>

    <div v-if="game.state==='finished'" class="overlay"><article class="modal final"><h2>游戏结束</h2><ol><li v-for="p in ranking" :key="p.id"><span>{{ p.name }}</span><b>{{ p.score }} 分</b></li></ol><button @click="exit">返回大厅</button></article></div>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue'; import { useRouter } from 'vue-router'; import { useFlip7Store } from '@/stores/flip7Store';
const store=useFlip7Store(), router=useRouter(), swapSelections=ref([]); const game=computed(()=>store.gameState);
const modeName=computed(()=>{const preset=game.value.rules.deck_preset||'base';const name={base:'基础版',vengeance:'复仇版',custom:'自定义牌组'}[preset];return game.value.rules.brutal_mode?`${name} · 残酷模式`:name;});
const forced=computed(()=>game.value.flip3_state?.active); const mine=computed(()=>game.value.current_player===store.player_id);
const canDraw=computed(()=>game.value.state==='player_turn'&&mine.value&&!game.value.pending_action);
const canStop=computed(()=>canDraw.value&&!forced.value&&!state(store.player_id).must_hit);
const myPending=computed(()=>game.value.pending_action?.player_id===store.player_id?game.value.pending_action:null);
const needsCard=computed(()=>['swap','steal','discard'].includes(myPending.value?.type));
const swapReady=computed(()=>swapSelections.value.length===2&&swapSelections.value[0].playerId!==swapSelections.value[1].playerId);
const effectTitle=computed(()=>({freeze:'Freeze：冻结玩家',flip3:'Flip 3：强制翻三张',flip4:'Flip 4：强制翻四张',just_one_more:'Just One More',transfer_sc:'转交 Second Chance',modifier:'选择修正牌目标',swap:'交换卡牌',steal:'偷取卡牌',discard:'弃掉卡牌',brutal_flip7:'Flip 7：自己加奖励，或令一名对手扣分'}[myPending.value?.type]||'选择目标'));
const turnText=computed(()=>{if(game.value.pending_action)return `${store.getPlayerName(game.value.pending_action.player_id)} 正在结算卡牌`;if(forced.value)return `${store.getPlayerName(game.value.current_player)} 还需翻 ${game.value.flip3_state.remaining} 张`;return mine.value?'轮到你：翻牌还是停牌？':`等待 ${store.getPlayerName(game.value.current_player)} 操作`;});
const ranking=computed(()=>Object.entries(game.value.player_states).map(([id,s])=>({id,name:store.getPlayerName(id),score:s.score})).sort((a,b)=>b.score-a.score));
function state(id){return game.value.player_states[id]||{score:0,round_score:0,flip7_count:0,hand:[]};}
function probability(id){return game.value.probabilities?.[id]||null;} function formatProbability(value){return `${(Number(value||0)*100).toFixed(1)}%`;}
function cardLabel(c){return c.type==='number'?'数字':c.type==='action'?'行动':'修正';}
function playerClass(id){const s=state(id);return{current:game.value.current_player===id,busted:s.busted,stopped:s.stopped};}
watch(()=>myPending.value?.card?.id,()=>{swapSelections.value=[];});
function choose(id,cardId){store.selectTarget(id,cardId);}
function isSwapSelected(playerId,cardId){return swapSelections.value.some(x=>x.playerId===playerId&&x.cardId===cardId);}
function toggleSwap(playerId,card){const found=swapSelections.value.findIndex(x=>x.playerId===playerId&&x.cardId===card.id);if(found>=0){swapSelections.value.splice(found,1);return;}if(swapSelections.value.length>=2)swapSelections.value.shift();swapSelections.value.push({playerId,cardId:card.id});}
function confirmSwap(){if(!swapReady.value)return;const [first,second]=swapSelections.value;store.selectTarget(first.playerId,first.cardId,null,second.playerId,second.cardId);}
function exit(){store.leaveRoom();router.push({name:'Flip7Lobby'});}
</script>

<style scoped>
.table{min-height:100vh;padding:24px;color:#f5f1e8;background:radial-gradient(circle at 50% 35%,#214f45,#0d2625 58%,#071515);font-family:system-ui}header{display:flex;align-items:center;justify-content:space-between}header h1{margin:0;color:#ffe04f;letter-spacing:.18em}header p{margin:4px 0}.deck{width:64px;height:84px;border:3px solid #ffe04f;border-radius:9px;display:grid;place-content:center;text-align:center}.deck b{font-size:24px}.deck small{display:block}.players{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:24px 0}.player{background:#ffffff12;border:2px solid #ffffff20;border-radius:16px;padding:15px}.player.current{border-color:#ffe04f;box-shadow:0 0 22px #ffe04f55}.player.busted{opacity:.72}.player-head,.round-line{display:flex;justify-content:space-between}.round-line{margin:8px 0;color:#c8d9d5}.hand{display:flex;flex-wrap:wrap;gap:7px;min-height:65px}.hand em{opacity:.45}.card{border-radius:9px;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 5px 12px #0005}.card.number{background:linear-gradient(145deg,#1570c8,#243b86)}.card.action{background:linear-gradient(145deg,#e17b17,#b22d25)}.card.modifier{background:linear-gradient(145deg,#8f3db4,#4c237d)}.mini{width:46px;height:62px;animation:dealFromDeck .55s cubic-bezier(.2,.8,.2,1)}.mini.face-down{filter:grayscale(1);background:linear-gradient(145deg,#777,#343434);transform:rotateY(180deg);color:#ddd}.mini b{font-size:12px}.mini small{font-size:8px}.badges span{display:inline-block;margin:8px 5px 0 0;padding:3px 7px;border-radius:20px;background:#ffe04f;color:#2c2510;font-size:11px}.center{text-align:center}.turn{font-size:20px;font-weight:700}.round-ending-banner{padding:12px;border-radius:12px;background:#ffe04f;color:#332800;font-weight:900}.hero{width:142px;height:190px;margin:16px auto;animation:dealFromDeck .55s ease-out}.hero b{font-size:30px}.hero span{margin-top:14px;font-weight:900;color:#ffe04f}.back{background:#351766;border:5px double #ffe04f;font-size:72px;color:#ffe04f}.controls{display:flex;justify-content:center;gap:18px}.controls button{padding:16px 38px;border:0;border-radius:12px;font-size:19px;font-weight:800}.hit{background:#ffe04f;color:#28200c}.stay{background:#e8eee9;color:#16312d}button:disabled{opacity:.35}.history{max-width:900px;margin:30px auto}.history>div{display:flex;flex-wrap:wrap;gap:6px}.history-card{padding:7px 10px;border-radius:7px;background:#ffffff20}.overlay{position:fixed;inset:0;background:#000c;display:grid;place-items:center;padding:20px;z-index:10}.modal{width:min(720px,90vw);max-height:80vh;overflow:auto;background:#f8f4ea;color:#24202a;border-radius:20px;padding:28px}.targets,.swap-board{display:grid;gap:12px}.target{display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:#e8e1d5;padding:12px;border-radius:10px}.target strong{min-width:110px}.target button,.modal>button,header button{border:0;border-radius:8px;padding:9px 14px}.swap-card{display:flex;flex-direction:column}.swap-card.selected{outline:3px solid #5b2e91;background:#ffe04f}.confirm-swap{margin-top:12px;background:#5b2e91;color:white}.round-ending .mini{animation:collectCards 4s ease-in forwards}.final li{display:flex;justify-content:space-between;padding:12px;border-bottom:1px solid #ddd}@keyframes dealFromDeck{from{opacity:0;transform:translate(38vw,-28vh) rotateY(100deg) scale(.5)}to{opacity:1;transform:translate(0,0) rotateY(0) scale(1)}}@keyframes collectCards{0%,55%{opacity:1}100%{opacity:0;transform:translate(40vw,-25vh) scale(.25) rotate(25deg)}}@media(max-width:600px){.table{padding:14px}.players{grid-template-columns:1fr}.hero{width:110px;height:148px}.controls button{padding:13px 25px}}
.round-ending .mini { animation-duration: 3s; }
</style>
