<template>
  <div class="pt-16 min-h-screen bg-slate-100">
    <div class="max-w-7xl mx-auto px-6 py-6">
      <!-- Breadcrumb -->
      <el-breadcrumb separator="/" class="mb-5">
        <el-breadcrumb-item :to="{ path: '/emails' }">邮件管理</el-breadcrumb-item>
        <el-breadcrumb-item>邮件详情</el-breadcrumb-item>
      </el-breadcrumb>

      <div v-if="emailStore.loading" class="flex justify-center py-20">
        <el-icon class="text-blue-500 text-3xl is-loading"><Loading /></el-icon>
      </div>

      <div v-else-if="email" class="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <!-- Left: Original email (3/5) -->
        <div class="lg:col-span-3 flex flex-col gap-5">
          <!-- Email meta -->
          <div class="card">
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span class="text-blue-700 font-bold">{{ email.sender?.charAt(0)?.toUpperCase() }}</span>
                </div>
                <div>
                  <p class="font-semibold text-slate-800">{{ email.sender }}</p>
                  <p class="text-xs text-slate-400 mt-0.5">{{ formatDate(email.received_at) }}</p>
                </div>
              </div>
              <StatusBadge :status="email.status" />
            </div>
            <h3 class="text-lg font-bold text-slate-800 mb-1">{{ email.subject || '(无主题)' }}</h3>
          </div>

          <!-- Email body -->
          <div class="card flex-1">
            <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">原始邮件内容</h4>
            <div
              class="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap bg-slate-50 rounded-lg p-4 min-h-40 max-h-96 overflow-y-auto border border-slate-100"
              v-html="sanitizeBody(email.body)"
            />
          </div>
        </div>

        <!-- Right: Classification + Reply (2/5) -->
        <div class="lg:col-span-2 flex flex-col gap-5">
          <!-- Classification card -->
          <div class="card">
            <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">AI 分类结果</h4>

            <div class="flex items-center gap-4 mb-4">
              <el-progress
                type="circle"
                :percentage="Math.round((email.confidence || 0) * 100)"
                :color="email.confidence >= 0.75 ? '#10B981' : '#F59E0B'"
                :width="80"
                :stroke-width="8"
              />
              <div>
                <el-tag
                  size="large"
                  :color="CATEGORY_COLORS[email.category] + '20'"
                  style="border: none"
                  :style="`color: ${CATEGORY_COLORS[email.category]}`"
                  class="font-semibold"
                >
                  {{ CATEGORY_LABELS[email.category] || email.category }}
                </el-tag>
                <p class="text-xs text-slate-400 mt-2">
                  {{ email.status === 'ignored_no_reply' ? '✓ 非业务邮件，已自动忽略无需回复' : (email.status === 'send_failed' ? '✕ 发送失败，可编辑后重试' : (email.confidence >= 0.75 ? '✓ 高置信度，已自动处理' : '⚠ 低置信度，需人工审核')) }}

                </p>
              </div>
            </div>

            <div v-if="email.reasoning" class="bg-slate-50 rounded-lg p-3 border border-slate-100">
              <p class="text-xs text-slate-500 font-medium mb-1">分类依据</p>
              <p class="text-sm text-slate-600 leading-relaxed">{{ email.reasoning }}</p>
            </div>
          </div>

          <!-- Reply draft card -->
          <div class="card flex-1 flex flex-col">
            <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">AI 回复草稿</h4>

            <el-input
              v-model="editableReply"
              type="textarea"
              :autosize="{ minRows: 6, maxRows: 14 }"
              :disabled="email.status === 'auto_sent' || email.status === 'approved' || email.status === 'rejected' || email.status === 'ignored_no_reply'"
              placeholder="AI 生成的回复草稿..."
              class="mb-4 flex-1"
            />

            <!-- Action buttons -->
            <div v-if="email.status === 'pending_review' || email.status === 'send_failed'" class="flex gap-3">

              <button
                class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-700 text-white font-medium rounded-xl transition-colors cursor-pointer disabled:opacity-60"
                :disabled="approving"
                @click="handleApprove"
              >
                <CheckCircle class="w-4 h-4" />
                {{ approving ? '发送中...' : '审核通过并发送' }}
              </button>
              <button
                class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-500 hover:bg-red-600 text-white font-medium rounded-xl transition-colors cursor-pointer disabled:opacity-60"
                :disabled="rejecting"
                @click="handleReject"
              >
                <XCircle class="w-4 h-4" />
                {{ rejecting ? '处理中...' : '拒绝' }}
              </button>
            </div>

            <div v-else class="flex items-center gap-2 text-sm py-2">
              <CheckCircle v-if="email.status === 'auto_sent' || email.status === 'approved'" class="w-4 h-4 text-green-500" />
              <XCircle v-else class="w-4 h-4 text-red-400" />
              <span class="text-slate-500">{{ STATUS_LABELS[email.status] }}</span>
              <span v-if="email.sent_at" class="text-slate-400 text-xs ml-auto">{{ formatDate(email.sent_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-20 text-slate-400">
        <Mail class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>邮件不存在</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle, XCircle, Mail } from 'lucide-vue-next'
import { useEmailStore } from '../stores/email'
import StatusBadge from '../components/StatusBadge.vue'
import { CATEGORY_LABELS, CATEGORY_COLORS, STATUS_LABELS } from '../types/index'

const route = useRoute()
const emailStore = useEmailStore()
const approving = ref(false)
const rejecting = ref(false)

const email = computed(() => emailStore.currentEmail)
const editableReply = ref('')

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function sanitizeBody(body: string) {
  // Strip HTML tags to plain text preview
  return body?.replace(/<[^>]*>/g, '') || '(无内容)'
}

async function handleApprove() {
  if (!email.value) return
  approving.value = true
  try {
    await emailStore.approveEmail(email.value.id, editableReply.value)
  } finally {
    approving.value = false
  }
}


async function handleReject() {
  if (!email.value) return
  rejecting.value = true
  await emailStore.rejectEmail(email.value.id)
  rejecting.value = false
}

onMounted(async () => {
  const id = parseInt(route.params.id as string)
  await emailStore.loadEmail(id)
  editableReply.value = emailStore.currentEmail?.reply_text || ''
})
</script>
