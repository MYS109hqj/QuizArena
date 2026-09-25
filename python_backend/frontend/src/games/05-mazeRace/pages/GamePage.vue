<template>
  <main class="page">
    <header>
      <button @click="exit">退出</button>
      <div>
        <small>{{ isOrienteering ? '定向越野' : '经典竞速' }}</small>
        <h1>记忆的迷宫</h1>
      </div>
      <b>{{ statusText }}</b>
    </header>
    <button
      class="roster-tab"
      :class="{ open: sidebarOpen }"
      @click="sidebarOpen = !sidebarOpen"
    >
      {{ sidebarOpen ? '收起 ‹' : '玩家 ›' }}
    </button>
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <h2>探险队</h2>
      <article
        v-for="(player, id) in store.players"
        :key="id"
        :class="[
          'player-card',
          sideClass(id),
          {
            me: same(id, store.player_id),
            active: same(id, state.current_player),
          },
        ]"
      >
        <img v-if="player.avatar" :src="player.avatar" /><span
          v-else
          class="avatar"
          >{{ player.name?.[0] || '?' }}</span
        >
        <div class="player-info">
          <b>{{ player.name }}</b
          ><small>{{ state.steps[id] || 0 }} 步</small>
          <div v-if="isOrienteering" class="token-status">
            <span
              v-for="corner in statusTargets(id)"
              :key="corner"
              :class="[
                'mini-token',
                { done: hasVisited(id, corner), final: visitedCount(id) >= 3 },
              ]"
              :title="cornerName(corner)"
              >{{ tokenLabel(corner) }}</span
            ><small>{{
              visitedCount(id) >= 3 ? '返回起点' : `${visitedCount(id)}/3`
            }}</small>
          </div>
        </div>
      </article>
    </aside>
    <p v-if="isTurnMode" class="turn-status" :class="{ mine: isMyTurn }">
      {{
        isMyTurn
          ? `你的回合 · 还可移动 ${remainingTurnSteps} 步`
          : `等待 ${currentPlayerName} 行动`
      }}
    </p>
    <section class="board-wrap">
      <section class="board" :class="{ hit: collision }">
        <div
          v-for="index in 64"
          :key="index - 1"
          :class="['cell', { adjacent: isAdjacent(index - 1) }]"
          :style="cellStyle(index - 1)"
          @click="moveToCell(index - 1)"
        >
          <i
            v-if="isCheckpoint(index - 1)"
            :class="[
              'checkpoint-token',
              'fixed-target',
              {
                visited: isVisited(index - 1),
                home: isHome(index - 1),
                respawn: isRespawn(index - 1),
              },
            ]"
            ><span>{{ tokenLabel(index - 1) }}</span></i
          ><i
            v-else-if="myTarget === index - 1"
            class="checkpoint-token fixed-target"
            ><span>◆</span></i
          >
          <span
            v-for="(id, n) in occupants(index - 1)"
            :key="id"
            :class="[
              'player',
              sideClass(id),
              {
                crowded: occupants(index - 1).length > 1,
                'on-checkpoint': hasCellToken(index - 1),
              },
            ]"
            :style="
              occupantStyle(
                n,
                occupants(index - 1).length,
                hasCellToken(index - 1)
              )
            "
            >{{ same(id, store.player_id) ? '我' : playerNumber(id) }}</span
          >
        </div>
      </section>
    </section>
    <section class="controls">
      <button :disabled="!canMove" @click="move('up')">↑</button>
      <div>
        <button :disabled="!canMove" @click="move('left')">←</button
        ><button :disabled="!canMove" @click="move('down')">↓</button
        ><button :disabled="!canMove" @click="move('right')">→</button>
      </div>
      <small>支持 WASD 与方向键。到达目标角后，该角将成为新的复活点。</small>
    </section>
    <div v-if="state.state === 'finished' && !showFinalBoard" class="overlay">
      <section>
        <p>探索结束</p>
        <h2>{{ isWinner ? '你完成了路线！' : `${winnerName} 获胜` }}</h2>
        <p>你的步数：{{ state.steps[store.player_id] || 0 }}</p>
        <button class="primary" @click="showFinalBoard = true">
          查看完整迷宫</button
        ><button @click="exit">返回大厅</button>
      </section>
    </div>
  </main>
</template>
<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMazeRaceStore } from '@/stores/mazeRaceStore';
const store = useMazeRaceStore(),
  route = useRoute(),
  router = useRouter(),
  collision = ref(false),
  showFinalBoard = ref(false),
  sidebarOpen = ref(true);
let collisionTimer;
const state = computed(() => store.gameState),
  isOrienteering = computed(
    () => state.value.rules?.game_mode === 'orienteering'
  ),
  reveal = computed(
    () => state.value.state === 'finished' && showFinalBoard.value
  ),
  visibleWalls = computed(
    () =>
      new Set((state.value.visible_walls || []).map(([c, w]) => `${c}:${w}`))
  ),
  myTarget = computed(() => state.value.targets[store.player_id]),
  isWinner = computed(() => same(state.value.winner, store.player_id)),
  isTurnMode = computed(() => state.value.rules?.movement_mode === 'turns'),
  isMyTurn = computed(() => same(state.value.current_player, store.player_id)),
  canMove = computed(
    () =>
      state.value.state === 'playing' && (!isTurnMode.value || isMyTurn.value)
  ),
  remainingTurnSteps = computed(() =>
    Math.max(
      0,
      (state.value.rules?.steps_per_turn || 3) - state.value.turn_steps
    )
  ),
  currentPlayerName = computed(
    () => store.players[state.value.current_player]?.name || '其他玩家'
  ),
  winnerName = computed(
    () => store.players[state.value.winner]?.name || '其他玩家'
  ),
  statusText = computed(() =>
    state.value.state === 'finished'
      ? isWinner.value
        ? '胜利'
        : '已结束'
      : '墙体隐藏中'
  );
watch(
  () => store.rejectedMove,
  (h) => {
    if (!h) return;
    collision.value = false;
    requestAnimationFrame(() => (collision.value = true));
    clearTimeout(collisionTimer);
    collisionTimer = setTimeout(() => (collision.value = false), 280);
  }
);
const same = (a, b) => String(a) === String(b);
function ids() {
  return Object.keys(store.players);
}
function sideClass(id) {
  return `side-${Math.max(0, ids().indexOf(String(id))) % 4}`;
}
function playerNumber(id) {
  return ids().indexOf(String(id)) + 1;
}
function occupants(c) {
  return Object.entries(state.value.positions)
    .filter(([, p]) => p === c)
    .map(([id]) => id);
}
function visitedCount(id) {
  return (state.value.visited_checkpoints?.[id] || []).length;
}
function hasVisited(id, c) {
  return (state.value.visited_checkpoints?.[id] || []).includes(c);
}
function isCheckpoint(c) {
  return isOrienteering.value && state.value.checkpoints.includes(c);
}
function hasCellToken(c) {
  return isCheckpoint(c) || myTarget.value === c;
}
function isVisited(c) {
  return hasVisited(store.player_id, c);
}
function isHome(c) {
  return state.value.home_positions?.[store.player_id] === c;
}
function isRespawn(c) {
  return state.value.start_positions?.[store.player_id] === c;
}
function foreignCorners(id) {
  const home = state.value.home_positions?.[id];
  return (state.value.checkpoints || []).filter((c) => c !== home);
}
function statusTargets(id) {
  return visitedCount(id) >= 3
    ? [state.value.home_positions?.[id]]
    : foreignCorners(id);
}
function tokenLabel(c) {
  return { 0: 'A', 7: 'B', 63: 'C', 56: 'D' }[c] || '?';
}
function cornerName(c) {
  return `${tokenLabel(c)} 目标点`;
}
function occupantStyle(n, total, onCheckpoint) {
  if (total <= 1 && !onCheckpoint) return {};
  // Target tokens stay centered in their four fixed corner cells. Only players move.
  const spots = onCheckpoint
      ? [
          ['15%', '15%'],
          ['85%', '15%'],
          ['15%', '85%'],
          ['85%', '85%'],
        ]
      : [
          ['27%', '27%'],
          ['73%', '27%'],
          ['27%', '73%'],
          ['73%', '73%'],
        ],
    spot = spots[n] || spots[0];
  return { left: spot[0], top: spot[1], transform: 'translate(-50%,-50%)' };
}
function wallKind(c, w) {
  const r = Math.floor(c / 8),
    col = c % 8,
    outer =
      (w === 0 && r === 0) ||
      (w === 1 && col === 0) ||
      (w === 2 && col === 7) ||
      (w === 3 && r === 7);
  if (outer) return 'outer';
  if (visibleWalls.value.has(`${c}:${w}`)) return 'remembered';
  if (reveal.value && state.value.walls[c]?.[w]) return 'revealed';
  return 'grid';
}
function cellStyle(c) {
  const s = {};
  ['Top', 'Left', 'Right', 'Bottom'].forEach((side, w) => {
    const k = wallKind(c, w),
      width =
        k === 'outer'
          ? '8px'
          : k === 'remembered'
            ? '6px'
            : k === 'revealed'
              ? '3px'
              : '1px',
      color = k === 'grid' ? '#ffffff52' : '#fffffff5';
    s[`border${side}`] = `${width} solid ${color}`;
  });
  return s;
}
function move(d) {
  if (canMove.value) store.move(d);
}
function directionToCell(cell) {
  const current = state.value.positions?.[store.player_id];
  if (!Number.isInteger(current)) return null;
  const row = Math.floor(current / 8),
    col = current % 8,
    nextRow = Math.floor(cell / 8),
    nextCol = cell % 8;
  if (nextRow === row - 1 && nextCol === col) return 'up';
  if (nextRow === row + 1 && nextCol === col) return 'down';
  if (nextRow === row && nextCol === col - 1) return 'left';
  if (nextRow === row && nextCol === col + 1) return 'right';
  return null;
}
function isAdjacent(cell) {
  return canMove.value && Boolean(directionToCell(cell));
}
function moveToCell(cell) {
  const direction = directionToCell(cell);
  if (direction) move(direction);
}
function keydown(e) {
  const d = {
    ArrowUp: 'up',
    w: 'up',
    W: 'up',
    ArrowLeft: 'left',
    a: 'left',
    A: 'left',
    ArrowDown: 'down',
    s: 'down',
    S: 'down',
    ArrowRight: 'right',
    d: 'right',
    D: 'right',
  }[e.key];
  if (d) {
    e.preventDefault();
    move(d);
  }
}
onMounted(async () => {
  if (!store.room_id) await store.enterRoom(route.params.roomId);
  window.addEventListener('keydown', keydown);
});
onUnmounted(() => {
  clearTimeout(collisionTimer);
  window.removeEventListener('keydown', keydown);
});
async function exit() {
  await store.leaveRoom();
  router.push({ name: 'MazeRaceLobby' });
}
</script>
<style scoped>
.page {
  min-height: 100vh;
  padding: 16px;
  color: #fff;
  font-family: system-ui;
  overflow: hidden auto;
  background-color: #39762f;
  background-image: radial-gradient(
      ellipse at 20% 10%,
      #b4d85a33 0 2px,
      transparent 3px
    ),
    radial-gradient(ellipse at 75% 60%, #173f1d55 0 2px, transparent 4px),
    repeating-linear-gradient(
      112deg,
      #3e7e31 0 3px,
      #468837 4px 7px,
      #33702b 8px 11px
    );
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 900px;
  margin: auto;
  text-shadow: 0 2px 8px #173718;
}
header div {
  text-align: center;
}
header h1,
header small {
  margin: 0;
}
button {
  border: 0;
  border-radius: 11px;
  padding: 10px 16px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.35;
}
.board-wrap {
  --board-size: min(70vh, 88vw);
  width: var(--board-size);
  height: var(--board-size);
  margin: 12px auto;
  padding: 5px;
  box-sizing: border-box;
  filter: drop-shadow(2px 1px 0 #fff8) drop-shadow(-2px -1px 0 #fff4);
}
.board {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  grid-template-rows: repeat(8, minmax(0, 1fr));
  background: #34702fd9;
  box-shadow: 0 18px 50px #123d1dcc;
}
.board.hit {
  animation: collision 0.25s linear;
}
.cell {
  position: relative;
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  overflow: visible;
}
.cell.adjacent {
  cursor: pointer;
  background: #fff2;
}
.cell.adjacent:hover {
  background: #fff5;
  box-shadow: inset 0 0 0 3px #fff9;
}
.checkpoint-token {
  position: absolute;
  z-index: 1;
  left: 50%;
  top: 50%;
  width: 56%;
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #f1e7c2;
  border: clamp(2px, 0.3vw, 4px) dashed #d16337;
  box-shadow: 0 2px 7px #183715aa;
  color: #a83b20;
  font-style: normal;
  font-weight: 1000;
  font-size: clamp(9px, 1.35vw, 16px);
}
.checkpoint-token span {
  position: absolute;
}
.checkpoint-token.fixed-target {
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.checkpoint-token.visited {
  background: #d8efb2;
  border-color: #4c8b3b;
  color: #2f6e31;
}
.checkpoint-token.home {
  outline: 2px solid #fff;
}
.checkpoint-token.respawn {
  box-shadow:
    0 0 0 3px #ffe66b,
    0 2px 7px #183715aa;
}
.side-0 {
  --player-color: #ffd400;
}
.side-1 {
  --player-color: #ff563f;
}
.side-2 {
  --player-color: #21b9f2;
}
.side-3 {
  --player-color: #bd66f5;
}
.player {
  position: absolute;
  z-index: 3;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  box-sizing: border-box;
  width: 58%;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: clamp(2px, 0.35vw, 4px) solid var(--player-color);
  border-radius: 50%;
  background: #f8fff5;
  font-size: clamp(8px, 1.5vw, 14px);
  font-weight: 900;
  color: #16251a;
  box-shadow: 0 3px 9px #102b18aa;
}
.player.crowded {
  width: 40%;
  font-size: clamp(7px, 1.1vw, 11px);
}
.player.on-checkpoint {
  width: 24%;
  font-size: clamp(6px, 0.9vw, 10px);
}
.turn-status {
  text-align: center;
  margin: 7px;
}
.turn-status.mine {
  color: #fff28c;
  font-weight: 900;
}
.sidebar {
  position: fixed;
  z-index: 8;
  left: 0;
  top: 88px;
  width: 245px;
  box-sizing: border-box;
  padding: 18px;
  transform: translateX(-105%);
  transition: 0.25s;
  background: #143b20ef;
  border-radius: 0 20px 20px 0;
  box-shadow: 10px 15px 35px #0a2915aa;
}
.sidebar.open {
  transform: none;
}
.roster-tab {
  position: fixed;
  z-index: 9;
  left: 0;
  top: 42%;
  border-radius: 0 12px 12px 0;
}
.roster-tab.open {
  left: 245px;
}
.player-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin: 7px 0;
  border: 2px solid var(--player-color);
  border-radius: 13px;
  background: #ffffff12;
}
.player-card.me {
  box-shadow: 0 0 0 2px #fff;
}
.player-card.active {
  background: #ffffff25;
}
.player-card img,
.avatar {
  box-sizing: border-box;
  width: 43px;
  height: 43px;
  border: 3px solid var(--player-color);
  border-radius: 50%;
  object-fit: cover;
  display: grid;
  place-items: center;
  background: #f8fff5;
  color: #17331d;
  font-weight: 900;
}
.player-info {
  display: grid;
  gap: 3px;
}
.player-info > b {
  color: var(--player-color);
}
.player-info > small {
  color: #c8dcbc;
}
.token-status {
  display: flex;
  align-items: center;
  gap: 4px;
}
.mini-token {
  width: 20px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px dashed #e7a077;
  background: #6c402f;
  color: #ffd9c4;
  font-size: 10px;
  font-weight: 900;
  opacity: 0.55;
}
.mini-token.done {
  opacity: 1;
  background: #d8efb2;
  color: #2e6d31;
  border-color: #68a656;
}
.mini-token.final {
  opacity: 1;
  background: #ffe78b;
  color: #704c00;
  border: 2px solid #fff;
}
.controls {
  text-align: center;
}
.controls button {
  font-size: 20px;
  margin: 3px;
  min-width: 48px;
}
.controls small {
  display: block;
}
.overlay {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: #082112cc;
  display: grid;
  place-items: center;
}
.overlay section {
  background: #f5ffe7;
  color: #214326;
  padding: 34px;
  border-radius: 24px;
  text-align: center;
}
.overlay button {
  margin: 5px;
}
.primary {
  background: #ccec83;
  font-weight: 900;
}
@keyframes collision {
  25% {
    transform: translateX(-7px);
  }
  50% {
    transform: translateX(7px);
  }
  75% {
    transform: translateX(-4px);
  }
}
@media (max-width: 700px) {
  header h1 {
    font-size: 19px;
  }
  .board-wrap {
    --board-size: min(64vh, 92vw);
  }
  .roster-tab.open {
    left: 0;
    top: 70px;
  }
}
</style>
