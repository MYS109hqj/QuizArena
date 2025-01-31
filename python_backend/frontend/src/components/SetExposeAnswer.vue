<template>
    <div class="form-group">
      <label for="expose-answer">玩家能否看到彼此答案？</label>
      <select id="expose-answer" v-model="exposeAnswer" @change="updateExposeAnswer">
        <option :value="true">是</option>
        <option :value="false">否</option>
      </select>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      initialExposeAnswer: {
        type: Boolean,
        required: true
      },
      setExposeAnswerCallback: {
        type: Function,
        required: true
      }
    },
    data() {
      return {
        exposeAnswer: this.initialExposeAnswer // 初始化 exposeAnswer
      };
    },
    watch: {
      // 监听父组件传递的 initialExposeAnswer，同步更新子组件的 exposeAnswer
      initialExposeAnswer(newVal) {
        this.exposeAnswer = newVal;
      },
      // 监听子组件的 exposeAnswer，确保父组件和子组件的值保持同步
      exposeAnswer(newVal) {
        this.setExposeAnswerCallback(newVal);
      }
    },
    methods: {
      updateExposeAnswer() {
        // 当值变化时更新
        this.setExposeAnswerCallback(this.exposeAnswer);
      }
    }
  };
  </script>