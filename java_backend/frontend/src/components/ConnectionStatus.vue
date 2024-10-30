<!-- ConnectionStatus.vue -->
<template>
    <div :class="{'status-indicator': true, 'connected': isConnected, 'disconnected': !isConnected}">
      <span v-if="isConnected">🟢 Connected</span>
      <span v-else>🔴 Disconnected</span>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      isConnected: {
        type: Boolean,
        required: true,
      }
    }
  };
  </script>
  
  <style scoped>
  .status-indicator {
    display: flex;
    align-items: center;
    font-size: 18px;
  }
  .connected {
    color: green;
  }
  .disconnected {
    color: red;
  }
  </style>
  