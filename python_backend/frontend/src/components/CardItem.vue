<!-- components/CardItem.vue -->
<template>
  <div 
    class="card"
    :class="{ 
      flipped: flipped,
      matched: matched,
      unmatched: unmatched
    }"
    @click="handleClick"
  >
    <div class="card-inner">
      <!-- 正面：始终显示对应字母 -->
      <div class="card-front">
        <img :src="getLetterImage(cardIndex)" alt="Letter" />
      </div>

      <!-- 背面：只有 flipped 且有 patternId 时才显示图案 -->
      <div class="card-back">
        <img 
          v-if="flipped && card.patternId"
          :src="getPatternImage(card.patternId)" 
          :alt="card.patternId" 
          class="card-img" 
        />
        <!-- 可选：无 patternId 时显示占位图 -->
        <img 
          v-else-if="flipped" 
          :src="getPatternImage(null)" 
          alt="loading" 
          class="card-img placeholder"
        />
        <!-- 未翻面时，背面内容为空或透明，不渲染任何图像 -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';
import { useSamePatternHuntStore } from '@/stores/samePatternHuntStore';

const props = defineProps({
  card: { type: Object, required: true },
  cardIndex: { type: Number, required: true },
  flipped: Boolean,
  matched: Boolean,
  unmatched: Boolean
});

const store = useSamePatternHuntStore();

// 是否是自己的回合
const isMyTurn = computed(() => store.gameState?.current_player === store.player_id);

// 点击处理
const handleClick = () => {
  if (!isMyTurn.value || props.flipped) return;
  
  // 检查前端规则限制
  const rules = store.gameRules;
  
  // 检查牌未翻回限制
  if (rules.flipRestrictions.preventFlipDuringAnimation) {
    const anyCardFlipping = store.flippedCards.length > 0 || store.unmatchedCards.length > 0;
    if (anyCardFlipping) {
      alert('牌未翻回，无法翻开新牌');
      return;
    }
  }
  
  // 检查行动锁定限制（后端会处理，这里只是前端提示）
  if (rules.flipRestrictions.actionLockEnabled && store.gameState?.state === 'locked') {
    alert('有行动正在进行，暂不能进行下一次翻牌');
    return;
  }

  store.send({
    type: 'action',
    action: {
      type: 'flip',
      cardId: props.card.cardId
    }
  });
};

// 字母顺序 A-P
const letterOrder = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'];

// 获取字母图片（根据 cardIndex）
const getLetterImage = (index) => {
  const letter = letterOrder[index];
  return new URL(`/assets/letters/${letter}.png`, import.meta.url).href;
};

// 获取图案图片（支持 null fallback）
const getPatternImage = (patternId) => {
  if (!patternId) {
    return new URL('/assets/placeholder.svg', import.meta.url).href;
  }
  return new URL(`/assets/patterns/${patternId}.svg`, import.meta.url).href;
};
</script>

<style scoped>
.card {
  width: 100%;
  height: 0;
  padding-bottom: 100%; /* 1:1 aspect ratio */
  position: relative;
  cursor: pointer;
}

.card-inner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
  transform: rotateY(0deg);
}

.card.flipped .card-inner {
  transform: rotateY(180deg);
}

.card.matched .card-inner {
  border: 2px solid #4ade80;
  box-shadow: 0 0 15px rgba(77, 239, 132, 0.5);
}

.card.unmatched .card-inner {
  border: 2px solid #ef4444;
}

.card-front,
.card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  overflow: hidden;
}

.card-front {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-back {
  background: white;
  transform: rotateY(180deg);
  padding: 8px;
}

.card-img {
  width: 80%;
  height: 80%;
  object-fit: contain;
}

.placeholder {
  opacity: 0.4;
}
</style>