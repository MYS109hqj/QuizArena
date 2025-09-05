<template>
    <div class="form-group mode-update">
      <label for="mode-selection">选择模式:</label>
      <select id="mode-selection" v-model="selectedMode">
        <option value="none">无模式</option>
        <option value="scoring">计分模式</option>
        <option value="survival">生存模式</option>
      </select>
      <!-- <button @click="updateMode" class="update-button">更新房间模式</button> -->
    </div>
  </template>
  
  <script>
  import { ref, watch } from 'vue';
  
  export default {
    props: {
      currentMode: String,
      updateModeCallback: Function,
    },
    setup(props) {
      const selectedMode = ref(props.currentMode);
  
      watch(selectedMode, (newMode) => {
        if (newMode !== props.currentMode) {
          props.updateModeCallback(newMode);
        }
      });

      const updateLocalValues = () => {
        selectedMode.value = props.currentMode;
      };

      watch(() => props.currentMode, updateLocalValues);
  
      return {
        selectedMode,
        updateMode: () => {
          props.updateModeCallback(selectedMode.value);
        },
      };
    },
  };
  </script>
  
  <style scoped>
  .mode-update {
    display: flex;
    align-items: center; /* 垂直居中对齐 */
  }
  .update-button {
    margin-left: 10px; /* 按钮与选择框之间的间距 */
  }
  </style>
  