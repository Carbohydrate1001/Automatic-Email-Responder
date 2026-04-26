<template>
  <div class="pt-16 min-h-screen bg-slate-100">
    <div class="max-w-full sm:max-w-[640px] md:max-w-[768px] lg:max-w-[1024px] xl:max-w-[1400px] 2xl:max-w-[1600px] mx-auto px-4 md:px-6 xl:px-8 2xl:px-12 py-6">
      <!-- Page header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-slate-800">{{ t('emailList.title') }}</h2>
          <p class="text-slate-500 text-sm mt-1">{{ t('emailList.totalCount', { count: emailStore.total }) }}</p>
        </div>
        <button
          class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-all duration-150 hover:shadow-md cursor-pointer disabled:opacity-60"
          :disabled="emailStore.fetching"
          @click="emailStore.fetchNewEmails()"
        >
          <RefreshCw :class="['w-4 h-4', emailStore.fetching ? 'animate-spin' : '']" />
          {{ emailStore.fetching ? t('emailList.fetching') : t('emailList.fetchNew') }}
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
            :placeholder="t('emailList.searchPlaceholder')"
            clearable
            class="w-64"
            @change="applySearch"
            @clear="applySearch"
          >
            <template #prefix><Search class="w-4 h-4 text-slate-400" /></template>
          </el-input>

          <el-select
            v-model="statusFilter"
            :placeholder="t('emailList.allStatus')"
            clearable
            class="w-44"
            @change="applyFilters"
          >
            <el-option v-for="(label, val) in statusLabels" :key="val" :label="label" :value="val" />
          </el-select>

          <el-select
            v-model="categoryFilter"
            :placeholder="t('emailList.allCategories')"
            clearable
            class="w-44"
            @change="applyFilters"
          >
            <el-option v-for="(label, val) in categoryLabels" :key="val" :label="label" :value="val" />
          </el-select>

          <div class="ml-auto">
            <el-button type="primary" @click="emailStore.exportToCSV()">
              <Download class="w-4 h-4 mr-1" />
              {{ t('emailList.exportCSV') }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Bulk actions toolbar -->
      <div v-if="emailStore.selectedIds.length > 0" class="card mb-5 bg-blue-50 border-blue-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="text-sm font-medium text-slate-700">
              {{ t('emailList.selected', { count: emailStore.selectedIds.length }) }}
            </span>
            <el-button size="small" @click="emailStore.clearSelection()">{{ t('emailList.clearSelection') }}</el-button>
          </div>

          <div class="flex items-center gap-2">
            <el-button
              type="success"
              size="small"
              :loading="emailStore.bulkActionLoading"
              :disabled="!canBulkApprove"
              @click="handleBulkApprove"
            >
              <CheckCircle class="w-4 h-4 mr-1" />
              {{ t('emailList.bulkApprove') }}
            </el-button>

            <el-button
              type="warning"
              size="small"
              :loading="emailStore.bulkActionLoading"
              :disabled="!canBulkReject"
              @click="handleBulkReject"
            >
              <XCircle class="w-4 h-4 mr-1" />
              {{ t('emailList.bulkReject') }}
            </el-button>

            <el-button
              type="danger"
              size="small"
              :loading="emailStore.bulkActionLoading"
              @click="handleBulkDelete"
            >
              <Trash2 class="w-4 h-4 mr-1" />
              {{ t('emailList.bulkDelete') }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Email table -->
      <div class="card p-0 overflow-hidden">
        <el-table
          v-loading="emailStore.loading"
          :data="emailStore.emails"
          row-key="id"
          row-class-name="cursor-pointer hover:bg-slate-50 transition-colors"
          @selection-change="handleSelectionChange"
          @row-click="(row: any) => router.push(`/emails/${row.id}`)"
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />

          <el-table-column :label="t('emailList.sender')" min-width="200" sortable prop="sender">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span class="text-blue-700 font-bold text-xs">{{ row.sender?.charAt(0)?.toUpperCase() }}</span>
                </div>
                <span class="text-slate-700 text-sm truncate">{{ row.sender }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column :label="t('emailList.subject')" min-width="300" sortable prop="subject">
            <template #default="{ row }">
              <span class="text-slate-800 font-medium text-sm line-clamp-1">{{ row.subject || t('emailList.noSubject') }}</span>
            </template>
          </el-table-column>

          <el-table-column :label="t('emailList.category')" width="140">
            <template #default="{ row }">
              <el-tag
                size="small"
                :color="CATEGORY_COLORS[row.category] + '20'"
                style="border: none"
                class="font-medium text-xs"
                :style="`color: ${CATEGORY_COLORS[row.category]}`"
              >
                {{ categoryLabels[row.category as keyof typeof categoryLabels] || row.category }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column :label="t('emailList.confidence')" width="140" sortable prop="confidence">
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

          <el-table-column :label="t('emailList.status')" width="130">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>

          <el-table-column :label="t('emailList.receivedTime')" width="180" sortable prop="received_at">
            <template #default="{ row }">
              <span class="text-slate-500 text-xs">{{ formatDate(row.received_at || row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column :label="t('emailList.actions')" width="140" fixed="right">
            <template #default="{ row }">
              <div class="flex items-center gap-1">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click.stop="router.push(`/emails/${row.id}`)"
                >
                  {{ t('emailList.view') }}
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  @click.stop="handleDeleteSingle(row.id)"
                >
                  {{ t('common.delete') }}
                </el-button>
              </div>
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
import { RefreshCw, Search, Mail, Clock, CheckCircle, AlertTriangle, XCircle, Trash2, Download } from 'lucide-vue-next'
import { useEmailStore } from '../stores/email'
import StatusBadge from '../components/StatusBadge.vue'
import { CATEGORY_COLORS } from '../types/index'
import type { EmailRecord } from '../types/index'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useTranslatedLabels } from '../composables/useTranslatedLabels'

const { t } = useI18n()
const { categoryLabels, statusLabels } = useTranslatedLabels()
const router = useRouter()
const emailStore = useEmailStore()

const searchText = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const currentPage = ref(1)

const statCards = computed(() => {
  const s = emailStore.stats
  return [
    { label: t('dashboard.totalEmails'), value: s?.total ?? '-', icon: Mail, bg: 'bg-blue-50', color: 'text-blue-600' },
    { label: t('dashboard.autoProcessed'), value: s ? (s.auto_sent + s.approved) : '-', icon: CheckCircle, bg: 'bg-green-50', color: 'text-green-600' },
    { label: t('dashboard.pendingReview'), value: s?.pending_review ?? '-', icon: AlertTriangle, bg: 'bg-yellow-50', color: 'text-yellow-600' },
    { label: t('dashboard.sendFailed'), value: s?.send_failed ?? '-', icon: Clock, bg: 'bg-red-50', color: 'text-red-500' },
    { label: t('dashboard.ignored'), value: s?.ignored_no_reply ?? '-', icon: Clock, bg: 'bg-slate-100', color: 'text-slate-600' },


  ]
})

const canBulkApprove = computed(() => {
  return emailStore.emails
    .filter(e => emailStore.selectedIds.includes(e.id))
    .every(e => e.status === 'pending_review' || e.status === 'send_failed')
})

const canBulkReject = computed(() => {
  return emailStore.emails
    .filter(e => emailStore.selectedIds.includes(e.id))
    .every(e => e.status === 'pending_review' || e.status === 'send_failed')
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

function handleSelectionChange(selection: EmailRecord[]) {
  emailStore.selectedIds = selection.map(e => e.id)
}

async function handleBulkApprove() {
  await ElMessageBox.confirm(
    t('dialogs.bulkApproveMessage', { count: emailStore.selectedIds.length }),
    t('dialogs.bulkApproveTitle'),
    { type: 'warning' }
  )
  await emailStore.bulkApprove([...emailStore.selectedIds])
}

async function handleBulkReject() {
  await ElMessageBox.confirm(
    t('dialogs.bulkRejectMessage', { count: emailStore.selectedIds.length }),
    t('dialogs.bulkRejectTitle'),
    { type: 'warning' }
  )
  await emailStore.bulkReject([...emailStore.selectedIds])
}

async function handleBulkDelete() {
  await ElMessageBox.confirm(
    t('dialogs.bulkDeleteMessage', { count: emailStore.selectedIds.length }),
    t('dialogs.bulkDeleteTitle'),
    { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') }
  )
  await emailStore.bulkDelete([...emailStore.selectedIds])
}

async function handleDeleteSingle(id: number) {
  await ElMessageBox.confirm(t('dialogs.deleteMessage'), t('dialogs.deleteTitle'), {
    type: 'warning',
    confirmButtonText: t('common.delete'),
    cancelButtonText: t('common.cancel')
  })
  await emailStore.deleteEmail(id)
}

onMounted(async () => {
  await Promise.all([emailStore.loadEmails(), emailStore.loadStats()])
})
</script>
