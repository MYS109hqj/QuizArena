<template>
  <div class="target-display">
    <div class="title-line">
      <h3>当前目标</h3>
      <button class="sequence-btn" @click="showSequence = true">查看目标顺序</button>
    </div>
    <div class="target-pattern" :class="{ pulse: isPulsing }">
      <img :src="getPatternImage(currentTargetPattern)"
        :alt="currentTargetPattern || '等待游戏开始'" class="target-img" />
      <span class="target-id">{{ currentTargetPattern || '等待游戏开始' }}</span>
    </div>

    <Teleport to="body">
      <div v-if="showSequence" class="sequence-overlay" @click.self="showSequence = false">
        <section class="sequence-modal">
          <header><h2>目标图案顺序</h2><button @click="showSequence = false">×</button></header>
          <p>展示当前目标、之前最多 3 个目标，以及之后最多 6 个目标。</p>
          <div v-for="player in targetPlayers" :key="player.id" class="player-sequence">
            <h3>{{ player.name }}<small v-if="player.id === myId">（我）</small></h3>
            <div class="pattern-list">
              <figure v-for="item in player.window" :key="item.index"
                :class="{ current: item.offset === 0, past: item.offset < 0 }">
                <img :src="getPatternImage(item.pattern_id)" :alt="`图案 ${item.pattern_id}`" />
                <figcaption>{{ positionLabel(item.offset) }}</figcaption>
              </figure>
              <em v-if="!player.window.length">等待游戏开始</em>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const store = useSamePatternHuntStore();
const isPulsing = ref(false);
const showSequence = ref(false);
const myId = computed(() => String(store.player_id));
const currentTargetPattern = computed(() =>
  store.gameState?.gameInfo?.[myId.value]?.next_pattern || null);
const targetPlayers = computed(() => Object.entries(store.gameState?.gameInfo || {}).map(([id, info]) => ({
  id: String(id), name: store.getPlayerName(id), window: info.target_window || []
})));

watch(currentTargetPattern, newValue => {
  if (newValue) {
    isPulsing.value = true;
    setTimeout(() => (isPulsing.value = false), 1000);
  }
});

const getPatternImage = patternId => patternId
  ? new URL(`/assets/patterns/${patternId}.svg`, import.meta.url).href
  : new URL('/assets/placeholder.svg', import.meta.url).href;
const positionLabel = offset => offset === 0 ? '当前' : offset < 0 ? `前 ${Math.abs(offset)}` : `后 ${offset}`;
</script>

<style scoped>
.target-display{text-align:center;margin:20px 0;padding:15px;background:white;border-radius:8px;box-shadow:0 2px 8px #0002}.title-line{display:flex;align-items:center;justify-content:center;gap:12px}.title-line h3{margin:0}.sequence-btn{border:0;border-radius:8px;padding:7px 11px;background:#226b4b;color:#fff;cursor:pointer}.target-pattern{display:inline-flex;align-items:center;gap:15px;margin-top:10px}.target-img{width:60px;height:60px;object-fit:contain;border:2px solid #27ae60;border-radius:4px;padding:5px}.target-id{font-size:1.2em;font-weight:bold;color:#333}.pulse{animation:pulse 1s ease-in-out}.sequence-overlay{position:fixed;inset:0;z-index:2000;background:#000a;display:grid;place-items:center;padding:18px}.sequence-modal{width:min(900px,94vw);max-height:86vh;overflow:auto;background:#f8fbf8;color:#243128;border-radius:16px;padding:22px;text-align:left}.sequence-modal>header{display:flex;justify-content:space-between;align-items:center}.sequence-modal>header h2{margin:0}.sequence-modal>header button{border:0;background:transparent;font-size:30px;cursor:pointer}.sequence-modal>p{color:#657269}.player-sequence{border-top:1px solid #d8e2db;padding-top:12px;margin-top:12px}.player-sequence h3{margin:0 0 10px}.player-sequence small{color:#23754e}.pattern-list{display:flex;gap:9px;overflow-x:auto;padding:4px}.pattern-list figure{flex:0 0 76px;margin:0;padding:7px;border:2px solid transparent;border-radius:9px;text-align:center;background:#fff}.pattern-list figure.current{border-color:#e39d13;background:#fff4cf}.pattern-list figure.past{opacity:.48}.pattern-list img{width:58px;height:58px;object-fit:contain}.pattern-list figcaption{font-size:12px;margin-top:3px}@keyframes pulse{50%{transform:scale(1.05)}}
</style>
