import { defineStore } from 'pinia'
import { ref } from 'vue'
import { emailApi } from '../api/index'
import type { EmailRecord, EmailListResponse, StatsResponse } from '../types/index'
import { ElMessage } from 'element-plus'

export const useEmailStore = defineStore('email', () => {
  const emails = ref<EmailRecord[]>([])
  const currentEmail = ref<EmailRecord | null>(null)
  const total = ref(0)
  const stats = ref<StatsResponse | null>(null)
  const loading = ref(false)
  const fetching = ref(false)

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
      ElMessage.error('加载邮件失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
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
      ElMessage.error('加载邮件详情失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
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
      ElMessage.success(`已处理 ${res.data.processed} 封新邮件，跳过 ${res.data.skipped} 封重复邮件`)
      await loadEmails()
      await loadStats()
    } catch (e: any) {
      ElMessage.error('拉取邮件失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
    } finally {
      fetching.value = false
    }
  }

  async function approveEmail(id: number, replyText?: string) {
    try {
      await emailApi.approveEmail(id, replyText)
      ElMessage.success('已审核通过并发送回复')
    } catch (e: any) {
      ElMessage.error('发送失败：' + (e?.response?.data?.error || e?.response?.data?.detail || e?.message || '未知错误'))
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
    ElMessage.success('已拒绝该邮件')
    if (currentEmail.value?.id === id) {
      await loadEmail(id)
    }
    await loadEmails()
  }

  function setFilter(key: string, value: string | number) {
    (filters.value as Record<string, string | number>)[key] = value
    filters.value.page = 1
  }

  return {
    emails, currentEmail, total, stats, loading, fetching, filters,
    loadEmails, loadEmail, loadStats, fetchNewEmails, approveEmail, rejectEmail, setFilter,
  }
})
