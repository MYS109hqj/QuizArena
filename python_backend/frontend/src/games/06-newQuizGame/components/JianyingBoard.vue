<template><canvas ref="canvas" class="board" aria-label="鉴影提示题板"></canvas></template>
<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
const props = defineProps({ board: { type: Object, required: true } });
const canvas = ref(null); let timer = null, frame = 0;
function draw(cells = []) {
  const el = canvas.value, board = props.board;
  if (!el || !board?.columns) return;
  const maxWidth = Math.min(720, window.innerWidth - 80), cell = Math.max(3, Math.floor(maxWidth / board.columns));
  const dpr = window.devicePixelRatio || 1, width = cell * board.columns, height = cell * board.rows;
  el.style.width = `${width}px`; el.style.height = `${height}px`; el.width = width*dpr; el.height = height*dpr;
  const context = el.getContext('2d'); context.setTransform(dpr,0,0,dpr,0,0);
  context.fillStyle='#f8f4e8'; context.fillRect(0,0,width,height); context.fillStyle='#17211b';
  cells.forEach(({x,y}) => context.fillRect(x*cell+1,y*cell+1,cell-1.2,cell-1.2));
  context.strokeStyle='rgba(23,33,27,.11)'; context.lineWidth=1; context.beginPath();
  for(let x=0;x<=board.columns;x++){context.moveTo(x*cell+.5,0);context.lineTo(x*cell+.5,height)}
  for(let y=0;y<=board.rows;y++){context.moveTo(0,y*cell+.5);context.lineTo(width,y*cell+.5)} context.stroke();
}
function play(){ clearTimeout(timer); const board=props.board, groups=board?.groups||[]; if(!groups.length)return;
  const visible=board.preset?.visible_ms||620, blank=board.preset?.blank_ms||160;
  const tick=()=>{ draw(groups[frame%groups.length]); frame++; timer=setTimeout(()=>{draw([]);timer=setTimeout(tick,blank)},visible) }; tick();
}
watch(()=>props.board,()=>nextTick(play),{immediate:true}); onBeforeUnmount(()=>clearTimeout(timer));
</script>
<style scoped>.board{display:block;max-width:100%;margin:18px auto;border:2px solid #d8cfb9;border-radius:8px;background:#f8f4e8}</style>
