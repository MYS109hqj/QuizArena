<!-- components/CardItem.vue -->
<template>
  <div class="card" :class="{
    flipped: flipped || isPreview,
    matched: matched,
    unmatched: unmatched,
    'can-upgrade': pendingUpgrade && (card.cardId === pendingUpgrade.card1Id || card.cardId === pendingUpgrade.card2Id)
  }" @click="handleClick">
    <div class="card-inner">
      <div class="card-front">
        <img :src="getLetterImage(cardIndex)" alt="Letter" />
      </div>

      <div class="card-back">
        <div v-if="(flipped || isPreview) && card.number !== null" class="card-number">
          {{ card.number }}
        </div>
        <button
          v-if="pendingUpgrade && (card.cardId === pendingUpgrade.card1Id || card.cardId === pendingUpgrade.card2Id)"
          class="upgrade-btn" @click.stop="handleUpgrade">
          升级
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue';
import { useMemorialBanquetStore } from '@/stores/memorialBanquetStore';

const props = defineProps({
  card: { type: Object, required: true },
  cardIndex: { type: Number, required: true },
  flipped: Boolean,
  matched: Boolean,
  unmatched: Boolean
});

const store = useMemorialBanquetStore();

const isMyTurn = computed(() => store.gameState?.current_player === store.player_id);
const isPreview = computed(() => store.gameState?.isPreview || false);
const pendingUpgrade = computed(() => store.pendingUpgrade);

const handleClick = () => {
  if (!isMyTurn.value || props.flipped) return;

  const rules = store.gameRules;

  if (rules.flipRestrictions.preventFlipDuringAnimation) {
    const anyCardFlipping = store.flippedCards.length >= 2 || store.unmatchedCards.length > 0;
    if (anyCardFlipping) {
      alert('牌未翻回，无法翻开新牌');
      return;
    }
  }

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

const handleUpgrade = () => {
  if (!pendingUpgrade.value) return;
  if (props.card.cardId !== pendingUpgrade.value.card1Id && props.card.cardId !== pendingUpgrade.value.card2Id) return;

  store.send({
    type: 'action',
    action: {
      type: 'upgrade_card',
      cardId: props.card.cardId
    }
  });
};

const getLetterImage = (index) => {
  const card = store.cards[index];
  if (!card || !card.cardId) {
    console.log(`⚠️ CardItem: 无效的card或cardId，index=${index}`);
    return new URL(`/assets/letters/A.png`, import.meta.url).href;
  }
  const letter = card.cardId.charAt(0);
  console.log(`🔍 CardItem: index=${index}, cardId=${card.cardId}, letter=${letter}`);
  const url = new URL(`/assets/letters/${letter}.png`, import.meta.url).href;
  console.log(`✅ CardItem: 图片URL=${url}`);
  return url;
};
</script>

<style scoped>
.card {
  width: 100%;
  height: 0;
  padding-bottom: 100%;
  /* 1:1 aspect ratio */
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
  box-sizing: border-box;
}

.card.can-upgrade .card-inner {
  border: 3px solid #f59e0b;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.6);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {

  0%,
  100% {
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.6);
  }

  50% {
    box-shadow: 0 0 30px rgba(245, 158, 11, 0.9);
  }
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
  background: linear-gradient(135deg, #4caf50 0%, #3a9d6a 100%);
}

.card-front img {
  width: 80%;
  height: 80%;
  object-fit: contain;
  max-width: 100%;
  max-height: 100%;
}

.card-back {
  background: white;
  transform: rotateY(180deg);
  padding: 0;
  box-sizing: border-box;
  position: relative;
}

.card-number {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
  color: #333;
  padding-bottom: 30px;
}

.upgrade-btn {
  position: absolute;
  bottom: 5px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: none;
  border-radius: 15px;
  font-size: 12px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
  transition: all 0.3s ease;
  z-index: 10;
}

.upgrade-btn:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.6);
}

.upgrade-btn:active {
  transform: translateX(-50%) translateY(0);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}
</style>