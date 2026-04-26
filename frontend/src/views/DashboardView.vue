<template>
  <div class="pt-16 min-h-screen bg-slate-100">
    <div class="max-w-full sm:max-w-[640px] md:max-w-[768px] lg:max-w-[1024px] xl:max-w-[1400px] 2xl:max-w-[1600px] mx-auto px-4 md:px-6 xl:px-8 2xl:px-12 py-6">
      <!-- Header -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-slate-800">{{ t('dashboard.title') }}</h2>
        <p class="text-slate-500 text-sm mt-1">{{ t('dashboard.subtitle') }}</p>
      </div>

      <div v-if="!stats" class="flex justify-center py-20">
        <el-icon class="text-blue-500 text-3xl is-loading"><Loading /></el-icon>
      </div>

      <template v-else>
        <!-- Top 4 stat cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
          <div
            v-for="card in statCards"
            :key="card.label"
            class="bg-white rounded-xl shadow-sm border border-slate-100 p-5 hover:shadow-md transition-shadow duration-200"
          >
            <div class="flex items-center justify-between mb-3">
              <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', card.bg]">
                <component :is="card.icon" :class="['w-5 h-5', card.color]" />
              </div>
              <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', card.trendBg, card.trendColor]">
                {{ card.trend }}
              </span>
            </div>
            <p class="text-3xl font-bold text-slate-800">{{ card.value }}</p>
            <p class="text-sm text-slate-500 mt-1">{{ card.label }}</p>
          </div>
        </div>

        <!-- Charts row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Category pie chart -->
          <div class="card">
            <h4 class="font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <PieChart class="w-4 h-4 text-blue-500" />
              {{ t('dashboard.categoryDistribution') }}
            </h4>
            <v-chart :option="pieOption" style="height: 280px" autoresize />
          </div>

          <!-- Daily line chart -->
          <div class="card">
            <h4 class="font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-green-500" />
              {{ t('dashboard.last7Days') }}
            </h4>
            <v-chart :option="lineOption" style="height: 280px" autoresize />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Mail, CheckCircle, AlertTriangle, Activity, PieChart, TrendingUp } from 'lucide-vue-next'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart as EPieChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { useEmailStore } from '../stores/email'
import { CATEGORY_COLORS } from '../types/index'
import { useI18n } from 'vue-i18n'
import { useTranslatedLabels } from '../composables/useTranslatedLabels'

use([CanvasRenderer, EPieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const { t } = useI18n()
const { categoryLabels } = useTranslatedLabels()
const emailStore = useEmailStore()
const stats = computed(() => emailStore.stats)

const statCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    {
      label: t('dashboard.totalEmails'), value: s.total,
      icon: Mail, bg: 'bg-blue-50', color: 'text-blue-600',
      trend: t('common.all'), trendBg: 'bg-blue-50', trendColor: 'text-blue-600',
    },
    {
      label: t('dashboard.autoRate'), value: s.auto_rate + '%',
      icon: CheckCircle, bg: 'bg-green-50', color: 'text-green-600',
      trend: t('common.efficient'), trendBg: 'bg-green-50', trendColor: 'text-green-600',
    },
    {
      label: t('dashboard.pendingReview'), value: s.pending_review,
      icon: AlertTriangle, bg: 'bg-yellow-50', color: 'text-yellow-600',
      trend: t('common.pending'), trendBg: 'bg-yellow-50', trendColor: 'text-yellow-600',
    },
    {
      label: t('dashboard.avgConfidence'), value: s.avg_confidence + '%',
      icon: Activity, bg: 'bg-indigo-50', color: 'text-indigo-600',
      trend: t('common.aiAccuracy'), trendBg: 'bg-indigo-50', trendColor: 'text-indigo-600',
    },
  ]
})

const pieOption = computed(() => {
  const s = stats.value
  if (!s) return {}
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      data: s.categories.map(c => ({
        name: categoryLabels.value[c.category as keyof typeof categoryLabels.value] || c.category,
        value: c.cnt,
        itemStyle: { color: CATEGORY_COLORS[c.category] || '#94a3b8' },
      })),
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' } },
    }],
  }
})

const lineOption = computed(() => {
  const s = stats.value
  if (!s) return {}
  const days = s.daily.map(d => d.day.slice(5))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: [t('dashboard.handled'), t('dashboard.pending')], bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: days, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: t('dashboard.handled'), type: 'line', smooth: true,
        data: s.daily.map(d => d.handled),
        itemStyle: { color: '#10B981' },
        areaStyle: { color: 'rgba(16,185,129,0.08)' },
        lineStyle: { width: 2.5 },
      },
      {
        name: t('dashboard.pending'), type: 'line', smooth: true,
        data: s.daily.map(d => d.pending),
        itemStyle: { color: '#F59E0B' },
        areaStyle: { color: 'rgba(245,158,11,0.08)' },
        lineStyle: { width: 2.5 },
      },
    ],
  }
})

onMounted(() => emailStore.loadStats())
</script>
