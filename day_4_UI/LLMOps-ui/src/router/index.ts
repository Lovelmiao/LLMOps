import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '@/views/layout/DefaultLayout.vue'
import BlankLayout from '@/views/layout/BlankLayout.vue'
import { isLogin } from '@/utils/auth.ts'
import HomeView from '@/views/home/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          redirect: '/home',
        },
        {
          path: 'home',
          name: 'home',
          component: HomeView,
        },
        {
          path: 'user/settings',
          name: 'user-settings',
          component: () => import('@/views/auth/UserSettingsView.vue'),
        },
        {
          path: 'sessions/:session_id',
          name: 'session-detail',
          component: () => import('@/views/space/apps/DetailView.vue'),
        },
        {
          path: 'space/apps/:app_id',
          redirect: (to) => `/sessions/${to.params.app_id}`,
        },
        {
          path: 'space/apps',
          name: 'space-apps-list',
          component: () => import('@/views/space/apps/ListView.vue'),
        },
      ],
    },
    {
      path: '/',
      component: BlankLayout,
      children: [
        {
          path: 'auth/login',
          name: 'auth-login',
          component: () => import('@/views/auth/LoginView.vue'),
        },
      ],
    },
  ],

  //   routes: [
  //     {
  //       path: '/',
  //       name: 'home',
  //       component: HomeView,
  //     },
  //     {
  //       path: '/about',
  //       name: 'about',
  //       // route level code-splitting
  //       // this generates a separate chunk (About.[hash].js) for this route
  //       // which is lazy-loaded when the route is visited.
  //       component: () => import('../views/AboutView.vue'),
  //     },
  //   ],
})
router.beforeEach(async (to, from) => {
  if (!isLogin() && to.name != 'auth-login') {
    return { path: '/auth/login' }
  }
  if (isLogin() && to.name === 'auth-login') {
    return { path: '/home' }
  }
})
export default router
