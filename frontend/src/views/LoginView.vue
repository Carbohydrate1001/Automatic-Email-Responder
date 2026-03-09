<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f2027] via-[#1E3A5F] to-[#2563EB] relative overflow-hidden">
    <!-- Decorative circles -->
    <div class="absolute top-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full -translate-x-1/2 -translate-y-1/2 blur-3xl" />
    <div class="absolute bottom-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full translate-x-1/3 translate-y-1/3 blur-3xl" />
    <div class="absolute top-1/3 right-1/4 w-64 h-64 bg-cyan-500/5 rounded-full blur-2xl" />

    <!-- Login card -->
    <div class="relative z-10 w-full max-w-md mx-4">
      <div class="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-10">
        <!-- Logo area -->
        <div class="flex flex-col items-center mb-8">
          <div class="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-700 rounded-2xl flex items-center justify-center shadow-xl mb-4">
            <Mail class="w-10 h-10 text-white" />
          </div>
          <h1 class="text-2xl font-bold text-white tracking-wide">智能客服邮件系统</h1>
          <p class="text-blue-200 text-sm mt-2 text-center leading-relaxed">
            Automated Customer Service Email Reply System
          </p>
        </div>

        <!-- Feature list -->
        <div class="mb-8 space-y-3">
          <div v-for="f in features" :key="f.text" class="flex items-center gap-3 text-blue-100 text-sm">
            <div class="w-6 h-6 bg-blue-500/30 rounded-full flex items-center justify-center flex-shrink-0">
              <component :is="f.icon" class="w-3.5 h-3.5 text-blue-300" />
            </div>
            <span>{{ f.text }}</span>
          </div>
        </div>

        <!-- Login button -->
        <button
          class="w-full flex items-center justify-center gap-3 py-3.5 px-6 bg-white hover:bg-blue-50 text-[#1E3A5F] font-semibold rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-[1.02] cursor-pointer"
          @click="handleLogin"
        >
          <font-awesome-icon icon="fa-brands fa-windows" class="text-xl text-blue-600" />
          <span>使用 Microsoft 账号登录</span>
        </button>

        <p class="text-center text-blue-300/60 text-xs mt-6">
          通过 Microsoft Azure AD 安全认证 · Powered by GPT-4o-mini
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Mail, Zap, Eye, Shield } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const features = [
  { icon: Zap, text: 'AI 自动识别邮件意图，支持 6 种业务类型' },
  { icon: Eye, text: '智能生成回复草稿，高置信度自动发送' },
  { icon: Shield, text: '低置信度邮件转人工审核，确保准确性' },
]

function handleLogin() {
  authStore.login()
}
</script>
