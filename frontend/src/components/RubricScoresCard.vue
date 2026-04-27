<template>
  <div class="card">
    <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
      {{ title }}
    </h4>

    <!-- 总分展示 -->
    <div class="flex items-center gap-4 mb-4 pb-4 border-b border-slate-100">
      <el-progress
        type="circle"
        :percentage="Math.round((scores.weighted_score / 3.0) * 100)"
        :color="getScoreColor(scores.weighted_score)"
        :width="70"
        :stroke-width="6"
      />
      <div>
        <p class="text-2xl font-bold text-slate-800">
          {{ scores.weighted_score.toFixed(2) }}<span class="text-sm text-slate-400">/3.0</span>
        </p>
        <p class="text-xs text-slate-500 mt-1">加权总分</p>
      </div>
    </div>

    <!-- 各维度评分 -->
    <el-collapse accordion>
      <el-collapse-item
        v-for="(data, dimension) in scores.scores"
        :key="dimension"
        :name="dimension"
      >
        <template #title>
          <div class="flex items-center justify-between w-full pr-4">
            <span class="text-sm font-medium text-slate-700">
              {{ RUBRIC_DIMENSION_LABELS[dimension] || dimension }}
            </span>
            <el-tag
              :type="getScoreTagType(data.score)"
              size="small"
              class="ml-2"
            >
              {{ data.score }}/3
            </el-tag>
          </div>
        </template>
        <div class="text-sm text-slate-600 leading-relaxed px-4 py-2 bg-slate-50 rounded">
          {{ data.reasoning }}
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 自动发送建议 -->
    <div
      v-if="scores.auto_send_recommended !== undefined"
      class="mt-4 pt-4 border-t border-slate-100"
    >
      <div class="flex items-center gap-2">
        <el-tag
          :type="scores.auto_send_recommended ? 'success' : 'warning'"
          size="small"
        >
          {{ scores.auto_send_recommended ? '建议自动发送' : '建议人工审核' }}
        </el-tag>
        <span class="text-xs text-slate-400">
          (阈值: {{ scores.thresholds_applied?.auto_send_minimum || 2.5 }}/3.0)
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RUBRIC_DIMENSION_LABELS } from '../types/index'

interface Props {
  title: string
  scores: {
    scores: Record<string, { score: number; reasoning: string }>
    weighted_score: number
    auto_send_recommended?: boolean
    thresholds_applied?: { auto_send_minimum: number }
  }
}

defineProps<Props>()

function getScoreColor(score: number): string {
  if (score >= 2.5) return '#10B981'
  if (score >= 2.0) return '#F59E0B'
  return '#EF4444'
}

function getScoreTagType(score: number): 'success' | 'warning' | 'danger' {
  if (score >= 2.5) return 'success'
  if (score >= 2.0) return 'warning'
  return 'danger'
}
</script>
