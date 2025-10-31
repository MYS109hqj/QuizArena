import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '../stores/userStore';

// 新增页面
import HomePage from '../views/HomePage.vue';
import LoginPage from '../views/LoginPage.vue';
import UserSettingsPage from '../views/UserSettingsPage.vue';
import GameRecordsPage from '../views/GameRecordsPage.vue';

// 00-quiz 游戏相关页面
import EnterPage_Quiz from '../games/00-quiz/views/EnterPage.vue';
import AnswerPage_Quiz from '../games/00-quiz/views/AnswerPage.vue';
import QuestionPage_Quiz from '../games/00-quiz/views/QuestionPage.vue';
import TestPage_Quiz from '../games/00-quiz/views/testPage.vue';

// 01-samePatternHunt 游戏相关页面
import GameLobby from '../games/01-samePatternHunt/pages/GameLobby.vue';
import RoomPage from '../games/01-samePatternHunt/pages/RoomPage.vue';
import GamePage from '../games/01-samePatternHunt/pages/GamePage.vue';
import ResultPage from '../games/01-samePatternHunt/pages/ResultPage.vue';

const routes = [
  // 主页路由
  {
    path: '/',
    name: 'HomePage',
    component: HomePage
  },
  // 登录/注册页面
  {
    path: '/login',
    name: 'LoginPage',
    component: LoginPage
  },
  // 用户设置页面
  {
    path: '/settings',
    name: 'UserSettingsPage',
    component: UserSettingsPage
  },
  // 游戏记录页面
  {
    path: '/records',
    name: 'GameRecordsPage',
    component: GameRecordsPage
  },
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
      { path: '', name: 'SPHLobby', component: GameLobby },
      { path: 'room/:roomId', name: 'SPHRoom', component: RoomPage },
      { path: 'game/:roomId', name: 'SPHGame', component: GamePage },
      { path: 'result/:roomId', name: 'SPHResult', component: ResultPage },
    ]
  }
];

// SPH路由守卫函数
const requireAuth = (to, from, next) => {
  const userStore = useUserStore();
  if (!userStore.isLoggedIn) {
    next('/login');
  } else {
    next();
  }
};

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// 全局路由守卫 - 为SPH相关路由添加登录验证
router.beforeEach((to, from, next) => {
  // 检查是否为SPH相关路由
  const isSPHRoute = to.path.startsWith('/samePatternHunt');
  
  if (isSPHRoute) {
    const userStore = useUserStore();
    if (!userStore.isLoggedIn) {
      // 保存目标路由，登录后可以重定向回来
      sessionStorage.setItem('redirectAfterLogin', to.fullPath);
      next('/login');
      return;
    }
  }
  
  next();
});

export default router;
