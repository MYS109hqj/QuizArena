<!-- components/CardsGrid.vue -->
<template>
  <div class="cards-container" :class="{ locked: isLocked }">
    <CardItem
      v-for="(card, index) in cards"
      :key="card.cardId"
      :card="card"
      :card-index="index"
      :flipped="flippedCards.includes(card.cardId)"
      :matched="isCardMatched(card.cardId)"
      :unmatched="isCardUnmatched(card.cardId)"
    />
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import CardItem from './CardItem.vue';

const props = defineProps({
  cards: { type: Array, default: () => [] },
  flippedCards: { type: Array, default: () => [] },
  matchedCards: { type: Array, default: () => [] },
  unmatchedCards: { type: Array, default: () => [] },
  isLocked: Boolean
});

const isCardMatched = (cardId) => props.matchedCards.includes(cardId);
const isCardUnmatched = (cardId) => props.unmatchedCards.includes(cardId);
</script>

<style scoped>
.cards-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 固定4×4布局 */
  gap: 8px;
  padding: 12px;
  width: min(600px, 90vw); /* 限制最大宽度 */
  height: min(600px, 90vw); /* 保持正方形 */
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  perspective: 1000px;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

.cards-container.locked {
  pointer-events: none;
  opacity: 0.8;
}

/* 小屏幕优化 */
@media (max-width: 768px) {
  .cards-container {
    max-width: min(500px, 90vw); /* 小屏幕上减小最大宽度 */
    gap: 6px;
    padding: 8px;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1600px) {
  .cards-container {
    max-width: min(700px, 90vw); /* 大屏幕上增加最大宽度 */
    gap: 12px;
  }
}
</style>