<!-- components/CardsGrid.vue -->
<template>
  <div class="cards-container" :class="{ locked: isLocked }" :style="gridStyle">
    <CardItem v-for="(card, index) in cards" :key="card.cardId" :card="card" :card-index="index"
      :flipped="isCardFlipped(card.cardId)" :matched="isCardMatched(card.cardId)"
      :unmatched="isCardUnmatched(card.cardId)" />
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';
import { useMemorialBanquetStore } from '@/stores/memorialBanquetStore';
import CardItem from './CardItem.vue';

const props = defineProps({
  cards: { type: Array, default: () => [] },
  flippedCards: { type: Array, default: () => [] },
  matchedCards: { type: Array, default: () => [] },
  unmatchedCards: { type: Array, default: () => [] },
  isLocked: Boolean
});

const store = useMemorialBanquetStore();

const isCardMatched = (cardId) => props.matchedCards.includes(cardId);
const isCardUnmatched = (cardId) => props.unmatchedCards.includes(cardId);

const isCardFlipped = (cardId) => {
  if (store.gameState?.isPreview) {
    return true;
  }
  return props.flippedCards.includes(cardId);
};

const gridLayout = computed(() => {
  const cardCount = props.cards.length;
  if (cardCount === 12) {
    return { columns: 4, rows: 3 };
  } else if (cardCount === 18) {
    return { columns: 6, rows: 3 };
  } else if (cardCount === 24) {
    return { columns: 6, rows: 4 };
  }
  return { columns: 4, rows: 3 };
});

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${gridLayout.value.columns}, 1fr)`,
  gridTemplateRows: `repeat(${gridLayout.value.rows}, 1fr)`,
  width: gridLayout.value.columns === 6 ? 'min(700px, 90vw)' : 'min(600px, 90vw)',
  height: gridLayout.value.rows === 4 ? 'min(600px, 67.5vw)' : 'min(450px, 67.5vw)'
}));
</script>

<style scoped>
.cards-container {
  display: grid;
  gap: 8px;
  padding: 12px;
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
    max-width: min(500px, 90vw);
    /* 小屏幕上减小最大宽度 */
    gap: 6px;
    padding: 8px;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1600px) {
  .cards-container {
    max-width: min(700px, 90vw);
    /* 大屏幕上增加最大宽度 */
    gap: 12px;
  }
}
</style>