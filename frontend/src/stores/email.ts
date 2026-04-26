import { defineStore } from 'pinia'
import { ref } from 'vue'
import { emailApi } from '../api/index'
import type { EmailRecord, EmailListResponse, StatsResponse } from '../types/index'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

export const useEmailStore = defineStore('email', () => {
  const { t } = useI18n()
  const emails = ref<EmailRecord[]>([])
  const currentEmail = ref<EmailRecord | null>(null)
  const total = ref(0)
  const stats = ref<StatsResponse | null>(null)
  const loading = ref(false)
  const fetching = ref(false)
  const selectedIds = ref<number[]>([])
  const bulkActionLoading = ref(false)

  const filters = ref({
    page: 1,
    per_page: 20,
    status: '',
    category: '',
    search: '',
  })

  async function loadEmails() {
    loading.value = true
    try {
      const res = await emailApi.listEmails(filters.value)
      const data: EmailListResponse = res.data
      emails.value = data.emails
      total.value = data.total
    } catch (e: any) {
      ElMessage.error(t('messages.loadError', { error: e?.response?.data?.error || e?.message || t('common.error') }))
    } finally {
      loading.value = false
    }
  }

  async function loadEmail(id: number) {
    loading.value = true
    try {
      const res = await emailApi.getEmail(id)
      currentEmail.value = res.data
    } catch (e: any) {
      ElMessage.error(t('messages.loadError', { error: e?.response?.data?.error || e?.message || t('common.error') }))
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    try {
      const res = await emailApi.getStats()
      stats.value = res.data
    } catch (e: any) {
      console.warn('加载统计失败', e)
    }
  }

  async function fetchNewEmails(top = 10) {
    fetching.value = true
    try {
      const res = await emailApi.fetchEmails(top)
      ElMessage.success(t('messages.fetchSuccess', { processed: res.data.processed, skipped: res.data.skipped }))
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error(t('messages.fetchError', { error: e?.response?.data?.error || e?.message || t('common.error') }))
    } finally {
      fetching.value = false
    }
  }

  async function approveEmail(id: number, replyText?: string) {
    try {
      await emailApi.approveEmail(id, replyText)
      ElMessage.success(t('messages.approveSuccess'))
    } catch (e: any) {
      ElMessage.error(t('messages.approveError', { error: e?.response?.data?.error || e?.response?.data?.detail || e?.message || t('common.error') }))
      throw e
    } finally {
      if (currentEmail.value?.id === id) {
        await loadEmail(id)
      }
      await loadEmails()
      await loadStats()
    }
  }


  async function rejectEmail(id: number) {
    await emailApi.rejectEmail(id)
    ElMessage.success(t('messages.rejectSuccess'))
    if (currentEmail.value?.id === id) {
      await loadEmail(id)
    }
    await loadEmails()
  }

  async function deleteEmail(id: number) {
    try {
      await emailApi.deleteEmail(id)
      ElMessage.success(t('messages.deleteSuccess'))
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error(t('messages.deleteError', { error: e?.response?.data?.error || e?.message }))
      throw e
    }
  }

  async function bulkDelete(ids: number[]) {
    bulkActionLoading.value = true
    try {
      const res = await emailApi.bulkDeleteEmails(ids)
      ElMessage.success(t('messages.bulkDeleteSuccess', { count: res.data.deleted_count }))
      selectedIds.value = []
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error(t('messages.bulkDeleteError', { error: e?.response?.data?.error || e?.message }))
    } finally {
      bulkActionLoading.value = false
    }
  }

  async function bulkApprove(ids: number[]) {
    bulkActionLoading.value = true
    try {
      const res = await emailApi.bulkApproveEmails(ids)
      ElMessage.success(t('messages.bulkApproveSuccess', { count: res.data.approved_count }))
      if (res.data.failed_count > 0) {
        ElMessage.warning(t('messages.bulkApproveWarning', { count: res.data.failed_count }))
      }
      selectedIds.value = []
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error(t('messages.bulkApproveError', { error: e?.response?.data?.error || e?.message }))
    } finally {
      bulkActionLoading.value = false
    }
  }

  async function bulkReject(ids: number[]) {
    bulkActionLoading.value = true
    try {
      const res = await emailApi.bulkRejectEmails(ids)
      ElMessage.success(t('messages.bulkRejectSuccess', { count: res.data.rejected_count }))
      selectedIds.value = []
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error(t('messages.bulkRejectError', { error: e?.response?.data?.error || e?.message }))
    } finally {
      bulkActionLoading.value = false
    }
  }

  async function exportToCSV() {
    try {
      const res = await emailApi.exportEmails(filters.value)
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `emails_export_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success(t('messages.exportSuccess'))
    } catch (e: any) {
      ElMessage.error(t('messages.exportError', { error: e?.response?.data?.error || e?.message }))
    }
  }

  function toggleSelection(id: number) {
    const index = selectedIds.value.indexOf(id)
    if (index > -1) {
      selectedIds.value.splice(index, 1)
    } else {
      selectedIds.value.push(id)
    }
  }

  function selectAll() {
    selectedIds.value = emails.value.map(e => e.id)
  }

  function clearSelection() {
    selectedIds.value = []
  }

  function setFilter(key: string, value: string | number) {
    (filters.value as Record<string, string | number>)[key] = value
    filters.value.page = 1
  }

  return {
    emails, currentEmail, total, stats, loading, fetching, filters,
    selectedIds, bulkActionLoading,
    loadEmails, loadEmail, loadStats, fetchNewEmails,
    approveEmail, rejectEmail, deleteEmail,
    bulkDelete, bulkApprove, bulkReject, exportToCSV,
    toggleSelection, selectAll, clearSelection, setFilter,
  }
})
