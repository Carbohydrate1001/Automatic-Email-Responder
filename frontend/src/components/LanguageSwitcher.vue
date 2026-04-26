<template>
  <div class="flex items-center gap-2">
    <button
      @click="switchLocale('zh-CN')"
      :class="[
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
        currentLocale === 'zh-CN'
          ? 'bg-blue-600 text-white shadow-sm'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
      ]"
    >
      中文
    </button>
    <button
      @click="switchLocale('en-US')"
      :class="[
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
        currentLocale === 'en-US'
          ? 'bg-blue-600 text-white shadow-sm'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
      ]"
    >
      English
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const currentLocale = computed(() => locale.value)

function switchLocale(newLocale: string) {
  locale.value = newLocale
  localStorage.setItem('locale', newLocale)
}
</script>
