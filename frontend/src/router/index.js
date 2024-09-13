import { createRouter, createWebHistory } from 'vue-router';
import EnterPage from '../components/EnterPage.vue';
import AnswerPage from '../components/AnswerPage.vue';
import QuestionPage from '../components/QuestionPage.vue';  // 添加提问端的组件

const routes = [
  {
    path: '/enter',
    name: 'EnterPage',
    component: EnterPage
  },
  {
    path: '/answer/:roomId',
    name: 'AnswerPage',
    component: AnswerPage,
    props: route => ({
      roomId: route.params.roomId,
      name: route.query.name,
      avatarUrl: route.query.avatarUrl
    })
  },
  {
    path: '/question/:roomId',
    name: 'QuestionPage',
    component: QuestionPage,
    props: route => ({
      roomId: route.params.roomId
    })
  },
  {
    path: '/',
    redirect: '/enter',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
