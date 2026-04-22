<template>
  <header class="fixed top-0 left-0 right-0 z-50 h-16 bg-[#1E3A5F] shadow-lg flex items-center px-6">
    <!-- Logo -->
    <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/emails')">
      <div class="w-9 h-9 bg-blue-500 rounded-lg flex items-center justify-center shadow-md">
        <Mail class="w-5 h-5 text-white" />
      </div>
      <span class="text-white font-semibold text-lg tracking-wide">智能客服邮件系统</span>
    </div>

    <!-- Nav -->
    <nav class="ml-10 flex items-center gap-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150"
        :class="isActive(item.path)
          ? 'bg-blue-600 text-white shadow-sm'
          : 'text-blue-200 hover:bg-white/10 hover:text-white'"
      >
        <component :is="item.icon" class="w-4 h-4" />
        {{ item.label }}
      </router-link>
    </nav>

    <div class="ml-auto flex items-center gap-3">
      <!-- User info -->
      <div v-if="authStore.user" class="flex items-center gap-2 text-blue-100">
        <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
          {{ authStore.user.name?.charAt(0)?.toUpperCase() || 'U' }}
        </div>
        <span class="text-sm hidden md:block">{{ authStore.user.name }}</span>
      </div>

      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-blue-200 hover:bg-white/10 hover:text-white transition-all duration-150 cursor-pointer"
        @click="authStore.logout()"
      >
        <LogOut class="w-4 h-4" />
        <span class="hidden md:block">退出</span>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { Mail, LayoutDashboard, LogOut, Inbox, Package } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const navItems = [
  { path: '/emails', label: '邮件管理', icon: Inbox },
  { path: '/dashboard', label: '数据看板', icon: LayoutDashboard },
  { path: '/products', label: '产品管理', icon: Package },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}
</script>
