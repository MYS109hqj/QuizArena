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
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  perspective: 1000px;
}

.cards-container.locked {
  pointer-events: none;
  opacity: 0.8;
}
</style>