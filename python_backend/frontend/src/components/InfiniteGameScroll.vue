<template>
  <div class="scroll-wrapper">
    <div class="scroll-container" ref="containerRef" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
      
      <div class="scroll-track" :style="trackStyle">
        <!-- 原始列表 -->
        <div v-for="(imgUrl, index) in imageList" :key="'original-' + index" class="scroll-item">
          <img :src="imgUrl" alt="Game Icon" />
        </div>
        
        <!-- 克隆列表 -->
        <div v-for="(imgUrl, index) in imageList" :key="'clone-' + index" class="scroll-item" aria-hidden="true">
          <img :src="imgUrl" alt="Game Icon" />
        </div>
      </div>

      <div class="right-mask"></div>

      <div class="logo-text">
        记忆&知识竞技场
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const gameFiles = [
  'maze01.png',
  'maze02.png',
  'SPH01.png',
  'SPH02.png'
];

const imageList = gameFiles.map(file => {
  return new URL(`../../assets/games/${file}`, import.meta.url).href;
});

const scrollDuration = 15;
const direction = 'left';

const containerRef = ref(null);
const totalItems = gameFiles.length;

// 每个项目的总宽度 = width(100px) + gap(20px)
const itemTotalWidth = 120;

const trackStyle = computed(() => {
  const animationName = direction === 'left' ? 'scroll-left' : 'scroll-right';
  const moveDistance = -(itemTotalWidth * totalItems);
  
  return {
    animation: `${animationName} ${scrollDuration}s linear infinite`,
    // 使用 CSS 变量传递移动距离，避免在 keyframes 中写死
    '--move-distance': `${moveDistance}px`
  };
});

const handleMouseEnter = () => {
  const track = containerRef.value?.querySelector('.scroll-track');
  if (track) track.style.animationPlayState = 'paused';
};

const handleMouseLeave = () => {
  const track = containerRef.value?.querySelector('.scroll-track');
  if (track) track.style.animationPlayState = 'running';
};

// 可选：动态计算实际宽度（更精确）
onMounted(() => {
  if (containerRef.value) {
    const track = containerRef.value.querySelector('.scroll-track');
    const item = track?.querySelector('.scroll-item');
    if (item) {
      const rect = item.getBoundingClientRect();
      const gap = 20; // 与 CSS 中的 gap 一致
      // 可以在这里更新 itemTotalWidth
    }
  }
});
</script>

<!-- 注意：这里使用 non-scoped 来确保 @keyframes 名称不被哈希 -->
<style>
/* 全局动画，不受 scoped 影响 */
@keyframes scroll-left {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(var(--move-distance, -480px));
  }
}

@keyframes scroll-right {
  0% {
    transform: translateX(var(--move-distance, -480px));
  }
  100% {
    transform: translateX(0);
  }
}
</style>

<style scoped>
.scroll-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 40px 0;
  background: linear-gradient(135deg, rgba(230, 255, 230, 0.5) 0%, rgba(178, 247, 178, 0.5) 70%, rgba(248, 251, 248, 0.5) 100%);
}

.scroll-container {
  position: relative;
  width: 800px;
  height: 140px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
  display: flex;
  align-items: center;
}

.scroll-track {
  display: flex;
  gap: 20px;
  padding-left: 20px;
  will-change: transform;
  flex-shrink: 0;
}

.scroll-item {
  flex-shrink: 0;
  width: 100px;
  height: 100px;
  background: rgba(249, 249, 249, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.scroll-item:hover {
  transform: scale(1.05);
  border-color: #3a9d6a;
  box-shadow: 0 4px 12px rgba(58, 157, 106, 0.2);
}

.scroll-item img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.right-mask {
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 100%;
  background: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.92) 85%);
  z-index: 2;
  pointer-events: none;
}

.logo-text {
  position: absolute;
  top: 50%;
  right: 40px;
  transform: translateY(-50%);
  z-index: 3;
  font-size: 22px;
  font-weight: 800;
  color: #3a9d6a;
  letter-spacing: 1px;
  user-select: none;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>