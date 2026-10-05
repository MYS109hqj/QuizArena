<template>
  <section class="submission-live" aria-live="polite">
    <TransitionGroup name="toast" tag="div" class="toast-stack">
      <article v-for="event in visibleEvents" :key="event.event_id" class="toast">
        <span class="pulse"></span>
        <div><b>{{ event.message || '有玩家提交了答案' }}</b><small>{{ event.submitted }} / {{ event.total }} 已完成作答</small></div>
      </article>
    </TransitionGroup>
    <div class="progress"><span :style="{ width: progress + '%' }"></span></div>
  </section>
</template>
<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
const props = defineProps({ events: { type: Array, default: () => [] }, submitted: Number, total: Number });
const now = ref(Date.now()); const timer = setInterval(() => (now.value = Date.now()), 300);
const visibleEvents = computed(() => props.events.filter(event => now.value - event.received_at < 3200).slice(-3));
const progress = computed(() => props.total ? Math.min(100, (props.submitted || 0) / props.total * 100) : 0);
watch(() => props.events.length, () => (now.value = Date.now()));
onBeforeUnmount(() => clearInterval(timer));
</script>
<style scoped>
.submission-live{width:min(310px,38vw)}.toast-stack{display:grid;gap:8px;min-height:62px}.toast{display:flex;align-items:center;gap:11px;padding:12px 15px;border:1px solid #dfe4ff;border-radius:18px;background:#fffffff0;color:#252b4b;box-shadow:0 12px 35px #303b7424}.toast div{display:grid}.toast small{margin-top:3px;color:#737a9b}.pulse{width:10px;height:10px;border-radius:50%;background:#6a63ff;box-shadow:0 0 0 6px #6a63ff24}.progress{height:5px;margin-top:8px;overflow:hidden;border-radius:9px;background:#e8eafb}.progress span{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#6a63ff,#3ccda2);transition:width .25s}.toast-enter-active,.toast-leave-active{transition:.28s}.toast-enter-from{opacity:0;transform:translateY(-12px) scale(.96)}.toast-leave-to{opacity:0;transform:translateX(20px)}
@media(max-width:720px){.submission-live{width:100%}.toast-stack{min-height:0}.toast{padding:9px 12px}}
</style>
