<template>
  <aside :class="['drawer', { collapsed }]">
    <button class="toggle" :aria-label="collapsed ? '展开玩家状态' : '收起玩家状态'" @click="collapsed=!collapsed">{{ collapsed ? '‹' : '›' }}</button>
    <template v-if="!collapsed">
      <header><div><b>玩家状态</b><small>{{ submittedCount }}/{{ total }} 已完成</small></div></header>
      <div class="players">
        <article v-for="(player,id) in players" :key="id">
          <img v-if="player.avatar" :src="player.avatar" alt="" /><span v-else class="avatar">{{ player.name?.slice(0,1) }}</span>
          <div><b>{{ player.name }}</b><small>{{ isSubmitted(id) ? '已完成作答' : '作答中' }}</small></div>
          <strong>{{ scores[id] || 0 }}</strong>
        </article>
      </div>
    </template>
    <span v-else class="count">{{ submittedCount }}/{{ total }}</span>
  </aside>
</template>
<script setup>
import { computed, ref } from 'vue';
const props=defineProps({players:{type:Object,default:()=>({})},scores:{type:Object,default:()=>({})},submittedIds:{type:Array,default:()=>[]}});
const collapsed=ref(false), submittedSet=computed(()=>new Set(props.submittedIds.map(String))), total=computed(()=>Object.keys(props.players).length), submittedCount=computed(()=>submittedSet.value.size);
function isSubmitted(id){return submittedSet.value.has(String(id))}
</script>
<style scoped>
.drawer{position:fixed;z-index:20;right:0;top:50%;width:260px;padding:20px 16px;transform:translateY(-50%);border:1px solid #ffffff30;border-right:0;border-radius:24px 0 0 24px;background:#161b35e8;color:#fff;box-shadow:-18px 20px 55px #0b102b33;backdrop-filter:blur(16px);transition:width .2s}.drawer.collapsed{width:58px;padding:20px 8px}.toggle{position:absolute;left:-19px;top:50%;width:38px;height:64px;transform:translateY(-50%);border:0;border-radius:20px 0 0 20px;background:#fff;color:#4f4add;font-size:27px;cursor:pointer}.drawer header div{display:flex;justify-content:space-between;align-items:end}.drawer small{color:#b9c0df}.players{display:grid;gap:10px;margin-top:16px}.players article{display:grid;grid-template-columns:36px 1fr auto;gap:9px;align-items:center;padding:9px;border-radius:13px;background:#ffffff0d}.players article div{display:grid}.avatar,.players img{width:36px;height:36px;display:grid;place-items:center;border-radius:50%;background:#6a63ff;object-fit:cover}.count{display:block;text-align:center;font-weight:900;writing-mode:vertical-rl}
@media(max-width:900px){.drawer{top:auto;bottom:0;left:0;right:0;width:auto;transform:none;border-radius:22px 22px 0 0;border:1px solid #ffffff30;padding:14px 22px}.drawer.collapsed{left:auto;width:74px;padding:10px}.toggle{left:50%;top:-18px;width:64px;height:36px;transform:translateX(-50%) rotate(90deg);border-radius:20px 20px 0 0}.players{grid-template-columns:repeat(auto-fit,minmax(180px,1fr));max-height:28vh;overflow:auto}.count{writing-mode:horizontal-tb}}
</style>
