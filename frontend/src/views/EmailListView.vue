<template>
  <div class="pt-16 min-h-screen bg-slate-100">
    <div class="max-w-7xl mx-auto px-6 py-6">
      <!-- Page header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-slate-800">邮件管理</h2>
          <p class="text-slate-500 text-sm mt-1">共 {{ emailStore.total }} 封邮件</p>
        </div>
        <button
          class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-all duration-150 hover:shadow-md cursor-pointer disabled:opacity-60"
          :disabled="emailStore.fetching"
          @click="emailStore.fetchNewEmails()"
        >
          <RefreshCw :class="['w-4 h-4', emailStore.fetching ? 'animate-spin' : '']" />
          {{ emailStore.fetching ? '正在拉取...' : '拉取新邮件' }}
        </button>
      </div>

      <!-- Stats strip -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div v-for="s in statCards" :key="s.label" class="stat-card">
          <div :class="['w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', s.bg]">
            <component :is="s.icon" :class="['w-5 h-5', s.color]" />
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-800">{{ s.value }}</p>
            <p class="text-xs text-slate-500">{{ s.label }}</p>
          </div>
        </div>
      </div>

      <!-- Filters toolbar -->
      <div class="card mb-5">
        <div class="flex flex-wrap items-center gap-3">
          <el-input
            v-model="searchText"
            placeholder="搜索发件人或主题..."
            clearable
            class="w-64"
            @change="applySearch"
            @clear="applySearch"
          >
            <template #prefix><Search class="w-4 h-4 text-slate-400" /></template>
          </el-input>

          <el-select
            v-model="statusFilter"
            placeholder="全部状态"
            clearable
            class="w-44"
            @change="applyFilters"
          >
            <el-option v-for="(label, val) in STATUS_LABELS" :key="val" :label="label" :value="val" />
          </el-select>

          <el-select
            v-model="categoryFilter"
            placeholder="全部分类"
            clearable
            class="w-44"
            @change="applyFilters"
          >
            <el-option v-for="(label, val) in CATEGORY_LABELS" :key="val" :label="label" :value="val" />
          </el-select>
        </div>
      </div>

      <!-- Email table -->
      <div class="card p-0 overflow-hidden">
        <el-table
          v-loading="emailStore.loading"
          :data="emailStore.emails"
          row-class-name="cursor-pointer hover:bg-slate-50 transition-colors"
          @row-click="(row: any) => router.push(`/emails/${row.id}`)"
          style="width: 100%"
        >
          <el-table-column label="发件人" min-width="160">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span class="text-blue-700 font-bold text-xs">{{ row.sender?.charAt(0)?.toUpperCase() }}</span>
                </div>
                <span class="text-slate-700 text-sm truncate">{{ row.sender }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="主题" min-width="200">
            <template #default="{ row }">
              <span class="text-slate-800 font-medium text-sm line-clamp-1">{{ row.subject || '(无主题)' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="分类" width="140">
            <template #default="{ row }">
              <el-tag
                size="small"
                :color="CATEGORY_COLORS[row.category] + '20'"
                style="border: none"
                class="font-medium text-xs"
                :style="`color: ${CATEGORY_COLORS[row.category]}`"
              >
                {{ CATEGORY_LABELS[row.category] || row.category }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="置信度" width="130">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <el-progress
                  :percentage="Math.round((row.confidence || 0) * 100)"
                  :color="row.confidence >= 0.75 ? '#10B981' : '#F59E0B'"
                  :stroke-width="6"
                  style="width: 70px"
                  :show-text="false"
                />
                <span class="text-xs text-slate-600">{{ Math.round((row.confidence || 0) * 100) }}%</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="130">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>

          <el-table-column label="接收时间" width="160">
            <template #default="{ row }">
              <span class="text-slate-500 text-xs">{{ formatDate(row.received_at || row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                link
                size="small"
                @click.stop="router.push(`/emails/${row.id}`)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="px-6 py-4 border-t border-slate-100">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="emailStore.filters.per_page"
            :total="emailStore.total"
            layout="prev, pager, next, total"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { RefreshCw, Search, Mail, Clock, CheckCircle, AlertTriangle } from 'lucide-vue-next'
import { useEmailStore } from '../stores/email'
import StatusBadge from '../components/StatusBadge.vue'
import { CATEGORY_LABELS, CATEGORY_COLORS, STATUS_LABELS } from '../types/index'

const router = useRouter()
const emailStore = useEmailStore()

const searchText = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const currentPage = ref(1)

const statCards = computed(() => {
  const s = emailStore.stats
  return [
    { label: '总邮件', value: s?.total ?? '-', icon: Mail, bg: 'bg-blue-50', color: 'text-blue-600' },
    { label: '自动处理', value: s ? (s.auto_sent + s.approved) : '-', icon: CheckCircle, bg: 'bg-green-50', color: 'text-green-600' },
    { label: '待人工审核', value: s?.pending_review ?? '-', icon: AlertTriangle, bg: 'bg-yellow-50', color: 'text-yellow-600' },
    { label: '发送失败', value: s?.send_failed ?? '-', icon: Clock, bg: 'bg-red-50', color: 'text-red-500' },
    { label: '已忽略', value: s?.ignored_no_reply ?? '-', icon: Clock, bg: 'bg-slate-100', color: 'text-slate-600' },


  ]
})

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function applySearch() {
  emailStore.setFilter('search', searchText.value)
  emailStore.loadEmails()
}

function applyFilters() {
  emailStore.setFilter('status', statusFilter.value)
  emailStore.setFilter('category', categoryFilter.value)
  emailStore.loadEmails()
}

function onPageChange(page: number) {
  emailStore.setFilter('page', page)
  emailStore.loadEmails()
}

onMounted(async () => {
  await Promise.all([emailStore.loadEmails(), emailStore.loadStats()])
})
</script>
