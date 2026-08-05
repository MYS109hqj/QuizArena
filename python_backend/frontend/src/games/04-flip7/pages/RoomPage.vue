<template>
  <main class="room">
    <Transition name="toast"><div v-if="store.notice" class="toast" :class="store.notice.kind">{{store.notice.message}}</div></Transition>
    <header><button @click="leave">← 返回大厅</button><h1>Flip 7 房间</h1><code>{{ route.params.roomId }}</code></header>
    <section class="panel summary">
      <span>房主：{{ store.room?.owner?.name || '等待同步' }}</span>
      <span>玩家：{{ Object.keys(store.players).length }}/{{ store.room?.max_players || 18 }}</span>
      <span :title="deckTooltip">牌组：{{ presetName }}</span>
    </section>

    <section v-if="settings.deck_preset==='custom'" class="panel deck-viewer">
      <button @click="showDeck=!showDeck">{{showDeck?'收起牌组组成':'查看牌组组成'}}</button>
      <div v-if="showDeck">
        <h2>{{settings.deck_spec.name}}</h2>
        <p>数字牌：0 至 {{settings.deck_spec.number_max}}，数字 N 有 N 张。</p>
        <p>特殊数字：{{enabledSpecials||'无'}}</p>
        <p>功能牌：{{enabledCards(settings.deck_spec.actions,actionOptions)||'无'}}</p>
        <p>修正牌：{{enabledCards(settings.deck_spec.modifiers,modifierOptions)||'无'}}</p>
      </div>
    </section>

    <section v-if="isOwner && !isPlaying" class="panel settings">
      <h2>游戏设置</h2>
      <label><span>牌组预设</span><select v-model="settings.deck_preset" @change="presetChanged"><option value="base">官方基础版</option><option value="vengeance">官方复仇版</option><option value="custom">自定义牌组</option></select></label>
      <label :class="{disabled:settings.deck_preset==='base'}"><span>残酷模式（可选）</span><input v-model="settings.brutal_mode" type="checkbox" :disabled="settings.deck_preset==='base'" @change="saveRules"></label>
      <label><span>获胜分数</span><input v-model.number="settings.win_score" type="number" min="1" @change="saveRules"></label>
      <label><span>Flip 7 奖励</span><input v-model.number="settings.flip7_bonus" type="number" min="0" @change="saveRules"></label>
      <label><span>实时爆牌概率</span><input v-model="settings.probability_enabled" type="checkbox" @change="saveRules"></label>
      <label :class="{disabled:!settings.probability_enabled}"><span>概率可见范围</span><select v-model="settings.probability_visibility" :disabled="!settings.probability_enabled" @change="saveRules"><option value="all">所有玩家</option><option value="current">仅当前玩家</option><option value="self">仅查看自己</option></select></label>
      <label><span>随机种子（可选）</span><input v-model="settings.random_seed" type="number" placeholder="留空则随机" @change="saveRules"></label>

      <fieldset v-if="settings.deck_preset==='custom'" class="custom-deck">
        <legend>自定义牌组</legend>
        <label><span>牌组名称</span><input v-model="settings.deck_spec.name" maxlength="40" @change="saveRules"></label>
        <label><span>最大数字 N（数字 N 有 N 张）</span><input v-model.number="settings.deck_spec.number_max" type="number" min="1" max="30" @change="saveRules"></label>
        <div class="card-grid"><label v-for="item in specialOptions" :key="item.key"><span>{{item.label}}</span><input v-model="settings.deck_spec.special_numbers[item.key]" type="checkbox" @change="saveRules"></label></div>
        <h3>功能牌数量</h3><div class="card-grid"><label v-for="item in actionOptions" :key="item.key"><span>{{item.label}}</span><input v-model.number="settings.deck_spec.actions[item.key]" type="number" min="0" max="100" @change="saveRules"></label></div>
        <h3>修正牌数量</h3><div class="card-grid"><label v-for="item in modifierOptions" :key="item.key"><span>{{item.label}}</span><input v-model.number="settings.deck_spec.modifiers[item.key]" type="number" min="0" max="100" @change="saveRules"></label></div>
      </fieldset>
    </section>

    <section v-if="isOwner&&!isPlaying" class="panel bot-settings">
      <h2>添加策略机器人</h2>
      <select v-model="bot.strategy"><option value="random">随机策略</option><option value="score_threshold">分数阈值策略</option><option value="risk_threshold">爆牌概率阈值策略</option></select>
      <label v-if="bot.strategy==='score_threshold'">达到该轮分数后停牌 <input v-model.number="bot.threshold" type="number" min="0"></label>
      <label v-if="bot.strategy==='risk_threshold'">概率阈值 <input v-model.number="bot.threshold" type="number" min="0" max="1" step="0.05"></label>
      <button class="primary" @click="addBot">添加机器人</button>
    </section>

    <section class="players"><article v-for="(player,id) in store.players" :key="id" class="player"><div class="avatar">{{player.is_bot?'🤖':player.name?.[0]?.toUpperCase()||'P'}}</div><strong>{{store.getPlayerName(id)}}</strong><small v-if="String(id)===String(store.room?.owner?.id)">房主</small><button v-if="isOwner&&!isPlaying&&player.is_bot" @click="store.removeBot(id)">移除</button><button v-if="!isPlaying&&String(id)===String(store.player_id)&&!isOwner" @click="store.toggleReady()">{{player.ready?'取消准备':'准备'}}</button></article></section>
    <section class="actions"><button v-if="isPlaying" class="primary" @click="goGame">进入游戏</button><button v-else-if="isOwner" class="primary" :disabled="!canStart" @click="store.startGame()">开始游戏</button><button @click="showRules=true">查看规则</button></section>
    <div v-if="showRules" class="overlay" @click.self="showRules=false"><article class="rules"><button class="close" @click="showRules=false">×</button><h2>Flip 7 规则</h2><p>玩家依次各翻一张牌；爆牌、冻结或停牌的玩家会被跳过。所有玩家均不可行动，或有人集齐七种数字时，本大轮结束。</p><p>实时概率永远表示该玩家继续翻下一张牌时直接爆牌的概率，不展开 Flip 3/Flip 4，也不考虑 Second Chance。</p><p>自定义牌组固定遵守 0-N、数字 N 投放 N 张；功能牌和修正牌可以任意混合，并可独立开启残酷模式。</p></article></div>
  </main>
</template>

<script setup>
import {computed,onMounted,reactive,ref,watch} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {useFlip7Store} from '@/stores/flip7Store';
import {isWebSocketActive} from '@/ws/flip7Socket';
const store=useFlip7Store(),route=useRoute(),router=useRouter(),showRules=ref(false),showDeck=ref(false);
const blankCustom=()=>({preset:'custom',name:'自定义牌组',number_max:12,special_numbers:{zero:false,unlucky_7:false,lucky_13:false},actions:{flip_3:0,flip_4:0,freeze:0,second_chance:0,just_one_more:0,swap:0,steal:0,discard:0},modifiers:{times_2:0,divide_2:0,plus_2:0,plus_4:0,plus_6:0,plus_8:0,plus_10:0,minus_2:0,minus_4:0,minus_6:0,minus_8:0,minus_10:0}});
const settings=reactive({deck_preset:'base',deck_spec:blankCustom(),vengeance_mode:false,brutal_mode:false,win_score:200,flip7_bonus:15,probability_enabled:false,probability_visibility:'all',random_seed:null});
const bot=reactive({strategy:'random',threshold:20});
watch(()=>bot.strategy,value=>{bot.threshold=value==='risk_threshold'?.25:20;});
const specialOptions=[['zero','Zero'],['unlucky_7','Unlucky 7'],['lucky_13','Lucky 13']].map(([key,label])=>({key,label}));
const actionOptions=[['flip_3','Flip 3'],['flip_4','Flip 4'],['freeze','Freeze'],['second_chance','Second Chance'],['just_one_more','Just One More'],['swap','Swap'],['steal','Steal'],['discard','Discard']].map(([key,label])=>({key,label}));
const modifierOptions=[['times_2','×2'],['divide_2','÷2'],['plus_2','+2'],['plus_4','+4'],['plus_6','+6'],['plus_8','+8'],['plus_10','+10'],['minus_2','-2'],['minus_4','-4'],['minus_6','-6'],['minus_8','-8'],['minus_10','-10']].map(([key,label])=>({key,label}));
const isOwner=computed(()=>String(store.room?.owner?.id)===String(store.player_id)),isPlaying=computed(()=>store.gameStatus==='playing');
const canStart=computed(()=>{const p=Object.values(store.players);return p.length>=2&&p.every(x=>x.ready);});
const presetName=computed(()=>({base:'官方基础版',vengeance:'官方复仇版',custom:'自定义牌组'}[settings.deck_preset]));
const deckTooltip=computed(()=>settings.deck_preset==='custom'?`${settings.deck_spec.name}；数字 0-${settings.deck_spec.number_max}；功能牌 ${Object.values(settings.deck_spec.actions).reduce((a,b)=>a+Number(b||0),0)} 张；修正牌 ${Object.values(settings.deck_spec.modifiers).reduce((a,b)=>a+Number(b||0),0)} 张`:presetName.value);
const enabledSpecials=computed(()=>specialOptions.filter(x=>settings.deck_spec.special_numbers[x.key]).map(x=>x.label).join('、'));
function enabledCards(counts,options){return options.filter(x=>Number(counts[x.key]||0)>0).map(x=>`${x.label}×${counts[x.key]}`).join('、');}
watch(()=>store.gameState.rules,rules=>{if(!rules)return;Object.assign(settings,rules);const d=rules.deck_spec||{};const blank=blankCustom();settings.deck_spec={...blank,...d,special_numbers:{...blank.special_numbers,...(d.special_numbers||{})},actions:{...blank.actions,...(d.actions||{})},modifiers:{...blank.modifiers,...(d.modifiers||{})}};},{deep:true,immediate:true});
watch(isPlaying,value=>{if(value)goGame();});
onMounted(()=>{store.initStore();if(!isWebSocketActive())store.enterRoom(route.params.roomId);});
function presetChanged(){if(settings.deck_preset==='base')settings.brutal_mode=false;if(settings.deck_preset==='custom')settings.deck_spec=blankCustom();saveRules();}
function saveRules(){if(settings.deck_preset==='base')settings.brutal_mode=false;store.updateRules(JSON.parse(JSON.stringify(settings)));}
function addBot(){store.addBot({...bot,threshold:bot.strategy==='risk_threshold'?Math.min(1,Math.max(0,Number(bot.threshold))):Number(bot.threshold)});}
function goGame(){router.push({name:'Flip7Game',params:{roomId:route.params.roomId}});} function leave(){store.leaveRoom();router.push({name:'Flip7Lobby'});}
</script>

<style scoped>
.room{min-height:100vh;padding:32px;color:#f7f4ea;background:radial-gradient(circle at top,#4a2470,#171025 65%);font-family:system-ui}header,.summary,.actions{display:flex;align-items:center;justify-content:space-between;gap:16px}button,input,select{font:inherit}button{border:0;border-radius:10px;padding:10px 18px;cursor:pointer}.primary{background:#ffd84d;color:#291747;font-weight:800}.primary:disabled{opacity:.4}.panel,.player{background:#ffffff14;border:1px solid #ffffff25;border-radius:18px;padding:20px;margin:20px 0}.settings{display:grid;grid-template-columns:repeat(2,minmax(220px,1fr));gap:14px}.settings h2,.custom-deck{grid-column:1/-1}.settings label{display:flex;justify-content:space-between;gap:12px;background:#ffffff10;padding:14px;border-radius:12px}.custom-deck{border:1px solid #ffffff30;border-radius:14px;padding:16px}.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px}.disabled{opacity:.45}.players{display:flex;flex-wrap:wrap;gap:16px}.player{margin:0;min-width:150px;display:grid;gap:9px;justify-items:center}.avatar{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;background:#ffd84d;color:#31184c;font-size:24px;font-weight:900}.overlay{position:fixed;inset:0;background:#000b;display:grid;place-items:center;padding:20px}.rules{position:relative;max-width:720px;background:#fff;color:#292131;border-radius:20px;padding:32px;line-height:1.7}.close{position:absolute;right:15px;top:12px;font-size:24px}@media(max-width:650px){.settings{grid-template-columns:1fr}.summary{align-items:flex-start;flex-direction:column}}
.toast{position:fixed;z-index:1200;top:22px;left:50%;transform:translateX(-50%);padding:13px 22px;border-radius:12px;background:#fff;color:#261b31;box-shadow:0 10px 35px #0008}.toast.error{background:#ffdddd;color:#8b1722}.toast-enter-active,.toast-leave-active{transition:.25s}.toast-enter-from,.toast-leave-to{opacity:0;transform:translate(-50%,-15px)}.deck-viewer{line-height:1.7}
.bot-settings{display:flex;align-items:center;gap:15px;flex-wrap:wrap}.bot-settings h2{width:100%}.bot-settings label{display:flex;gap:10px;align-items:center}
</style>
