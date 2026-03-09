<template>
  <el-tag
    :type="tagType"
    :color="tagColor"
    class="font-medium"
    style="border: none"
  >
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { STATUS_LABELS } from '../types/index'

const props = defineProps<{ status: string }>()

const tagType = computed(() => {
  const map: Record<string, string> = {
    auto_sent: 'success',
    pending_review: 'warning',
    approved: '',
    rejected: 'danger',
    send_failed: 'danger',
    ignored_no_reply: 'info',
  }


  return map[props.status] || 'info'
})

const tagColor = computed(() => {
  const map: Record<string, string> = {
    auto_sent: '#dcfce7',
    pending_review: '#fef9c3',
    approved: '#dbeafe',
    rejected: '#fee2e2',
    send_failed: '#fee2e2',
    ignored_no_reply: '#e2e8f0',
  }


  return map[props.status] || '#f1f5f9'
})

const label = computed(() => STATUS_LABELS[props.status] || props.status)
</script>
