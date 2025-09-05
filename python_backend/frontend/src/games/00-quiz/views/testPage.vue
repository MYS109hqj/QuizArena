<template>
  <div class="question-input-container">
    <h2>题目设定</h2>

    <!-- 题目类型选择 -->
    <div class="form-group">
      <label for="question-type">选择题目类型:</label>
      <select id="question-type" v-model="questionType" @change="resetFields">
        <option value="qa">问答题</option>
        <option value="mcq">选择题</option>
        <option value="hints">多提示题</option>
        <option value="fill">填空题</option>
      </select>
    </div>

    <!-- 粘贴完整题目文本 -->
    <div class="form-group">
      <label for="full-question">输入完整题目:</label>
      <textarea id="full-question" v-model="fullQuestionText" placeholder="粘贴完整题目..." @blur="autoFillFields"></textarea>
    </div>

    <!-- 题干输入 -->
    <div class="form-group">
      <label for="question-input">题目:</label>
      <input id="question-input" v-model="question" placeholder="输入题目" />
    </div>

    <!-- 选择题选项输入 -->
    <div v-if="questionType === 'mcq'" class="form-group">
      <label>输入选项:</label>
      <input v-model="options[0]" placeholder="选项 A" />
      <input v-model="options[1]" placeholder="选项 B" />
      <input v-model="options[2]" placeholder="选项 C" />
      <input v-model="options[3]" placeholder="选项 D" />
    </div>

    <!-- 多提示题输入 -->
    <div v-if="questionType === 'hints'" class="form-group">
      <label for="basic-hint">基本提示:</label>
      <input id="basic-hint" v-model="basicHint" placeholder="输入基本提示" />
      <label>追加提示:</label>
      <input v-model="additionalHints[0]" placeholder="追加提示 1" />
      <input v-model="additionalHints[1]" placeholder="追加提示 2" />
      <input v-model="additionalHints[2]" placeholder="追加提示 3" />
      <input v-model="additionalHints[3]" placeholder="追加提示 4" />
    </div>

    <!-- 填空题输入 -->
    <div v-if="questionType === 'fill'" class="form-group">
      <label for="fill-answer">填空答案:</label>
      <input id="fill-answer" v-model="answer" placeholder="输入正确答案" />
    </div>

    <!-- 问答题/解析输入 -->
    <div class="form-group">
      <label for="answer-input">答案:</label>
      <input id="answer-input" v-model="answer" placeholder="输入答案" />
    </div>

    <div class="form-group">
      <label for="explanation-input">解析:</label>
      <textarea id="explanation-input" v-model="explanation" placeholder="输入解析"></textarea>
    </div>

    <!-- 发送问题按钮 -->
    <button @click="sendQuestion" class="primary-button">发送题目</button>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  setup() {
    const question = ref('');
    const questionType = ref('qa');
    const options = ref(['', '', '', '']);
    const basicHint = ref('');
    const additionalHints = ref(['', '', '', '']);
    const answer = ref('');
    const explanation = ref('');
    const fullQuestionText = ref('');

    const resetFields = () => {
      question.value = '';
      options.value = ['', '', '', ''];
      basicHint.value = '';
      additionalHints.value = ['', '', '', ''];
      answer.value = '';
      explanation.value = '';
      fullQuestionText.value = '';
    };

    // 自动解析用户粘贴的题目文本
    const autoFillFields = () => {
      const text = fullQuestionText.value.trim();
      if (!text) return;

      let lines = text.split('\n').map(line => line.trim()).filter(line => line);

      // 选择题解析
      if (questionType.value === 'mcq') {
        question.value = lines[0];
        options.value = lines.slice(1, 5);
        const answerLine = lines.find(line => line.startsWith('答案：'));
        if (answerLine) {
          answer.value = answerLine.replace('答案：', '').trim();
        }
        const explanationLine = lines.find(line => line.startsWith('解析：'));
        if (explanationLine) {
          explanation.value = explanationLine.replace('解析：', '').trim();
        }
      }

      // 填空题解析
      if (questionType.value === 'fill') {
        question.value = lines[0];
        const answerLine = lines.find(line => line.startsWith('答案：'));
        if (answerLine) {
          answer.value = answerLine.replace('答案：', '').trim();
        }
        const explanationLine = lines.find(line => line.startsWith('解析：'));
        if (explanationLine) {
          explanation.value = explanationLine.replace('解析：', '').trim();
        }
      }

      // 问答题解析
      if (questionType.value === 'qa') {
        question.value = lines[0];
        const answerLine = lines.find(line => line.startsWith('答案：'));
        if (answerLine) {
          answer.value = answerLine.replace('答案：', '').trim();
        }
        const explanationLine = lines.find(line => line.startsWith('解析：'));
        if (explanationLine) {
          explanation.value = explanationLine.replace('解析：', '').trim();
        }
      }

      // 多提示题解析
      if (questionType.value === 'hints') {
        question.value = lines[0];
        basicHint.value = lines[1] || '';
        additionalHints.value = lines.slice(2, 6);

        // 处理正确答案和解析
        const answerLine = lines.find(line => line.startsWith('答案：'));
        if (answerLine) {
          correct_answer.value = answerLine.replace('答案：', '').trim();
        }
        const explanationLine = lines.find(line => line.startsWith('解析：'));
        if (explanationLine) {
          explanation.value = explanationLine.replace('解析：', '').trim();
        }
      }
    };

    const sendQuestion = () => {
      const questionData = {
        type: questionType.value,
        content: {
          question: question.value,
          options: questionType.value === 'mcq' ? options.value : null,
          answer: answer.value,
          explanation: explanation.value,
          basicHint: questionType.value === 'hints' ? basicHint.value : null,
          additionalHints: questionType.value === 'hints' ? additionalHints.value : null
        }
      };
      console.log('发送题目:', questionData);
    };

    return {
      question,
      questionType,
      options,
      basicHint,
      additionalHints,
      answer,
      explanation,
      fullQuestionText,
      resetFields,
      autoFillFields,
      sendQuestion
    };
  }
};
</script>

<style scoped>
.question-input-container {
  width: 60%;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

input, select {
  width: 100%;
  padding: 10px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box;
}

.primary-button {
  width: 100%;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1em;
  cursor: pointer;
}

.primary-button:hover {
  background-color: #45a049;
}
</style>
