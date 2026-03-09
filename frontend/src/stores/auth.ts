import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/index'
import type { AuthUser } from '../types/index'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const loading = ref(false)
  const checked = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  async function checkAuth() {
    if (checked.value) return
    loading.value = true
    const res = await authApi.getStatus()
    if (res.data.authenticated) {
      user.value = res.data.user
    } else {
      user.value = null
    }
    checked.value = true
    loading.value = false
  }

  function login() {
    authApi.login()
  }

  function logout() {
    user.value = null
    checked.value = false
    authApi.logout()
  }

  return { user, loading, checked, isLoggedIn, checkAuth, login, logout }
})
