import { createRouter, createWebHistory } from 'vue-router';

// 00-quiz 游戏相关页面
import EnterPage_Quiz from '../games/00-quiz/views/EnterPage.vue';
import AnswerPage_Quiz from '../games/00-quiz/views/AnswerPage.vue';
import QuestionPage_Quiz from '../games/00-quiz/views/QuestionPage.vue';
import TestPage_Quiz from '../games/00-quiz/views/testPage.vue';

// 01-samePatternHunt 游戏相关页面（如有）
import EnterPage_SamePattern from '../games/01-samePatternHunt/pages/EnterPage.vue';
// 其它页面...

const routes = [
  {
    path: '/quiz',
    children: [
      {
        path: 'enter',
        name: 'QuizEnterPage',
        component: EnterPage_Quiz
      },
      {
        path: 'answer/:roomId',
        name: 'QuizAnswerPage',
        component: AnswerPage_Quiz,
        props: route => ({
          roomId: route.params.roomId,
          name: route.query.name,
          avatarUrl: route.query.avatarUrl
        })
      },
      {
        path: 'question/:roomId',
        name: 'QuizQuestionPage',
        component: QuestionPage_Quiz,
        props: route => ({
          roomId: route.params.roomId
        })
      },
      {
        path: 'test',
        name: 'QuizTestPage',
        component: TestPage_Quiz
      }
    ]
  },
  {
    path: '/samePatternHunt',
    children: [
      {
        path: 'enter',
        name: 'SamePatternEnterPage',
        component: EnterPage_SamePattern
      }
      // 其它 samePatternHunt 游戏页面...
    ]
  },
  {
    path: '/',
    redirect: '/quiz/enter'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
