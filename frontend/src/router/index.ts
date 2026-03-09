import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/emails',
    name: 'EmailList',
    component: () => import('../views/EmailListView.vue'),
  },
  {
    path: '/emails/:id',
    name: 'EmailDetail',
    component: () => import('../views/EmailDetailView.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/',
    redirect: '/emails',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const authStore = useAuthStore()
  await authStore.checkAuth()

  if (!authStore.isLoggedIn) {
    return { name: 'Login' }
  }
  return true
})

export default router
