<template>
  <div class="card">
    <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
      {{ t('matchedData.title') }}
    </h4>

    <!-- 订单信息 -->
    <div v-if="data.order" class="space-y-2">
      <div class="flex items-center gap-2 mb-3">
        <el-tag type="primary" size="small">{{ t('matchedData.orderInfo') }}</el-tag>
      </div>
      <div class="bg-slate-50 rounded-lg p-3 space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.orderNumber') }}:</span>
          <span class="font-mono font-semibold text-slate-800">{{ data.order.order_number }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.product') }}:</span>
          <span class="text-slate-700">{{ data.order.product_name }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.amount') }}:</span>
          <span class="font-semibold text-slate-800">
            {{ data.order.currency }} {{ data.order.total_amount.toFixed(2) }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.orderStatus') }}:</span>
          <el-tag :type="getOrderStatusType(data.order.order_status)" size="small">
            {{ data.order.order_status }}
          </el-tag>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.shippingStatus') }}:</span>
          <el-tag :type="getShippingStatusType(data.order.shipping_status)" size="small">
            {{ data.order.shipping_status }}
          </el-tag>
        </div>
        <div v-if="data.order.tracking_number" class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.trackingNumber') }}:</span>
          <span class="font-mono text-slate-700">{{ data.order.tracking_number }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.destination') }}:</span>
          <span class="text-slate-700">{{ data.order.destination }}</span>
        </div>
      </div>
    </div>

    <!-- 物流路线信息 -->
    <div v-if="data.logistics_route" class="space-y-2">
      <div class="flex items-center gap-2 mb-3">
        <el-tag type="success" size="small">{{ t('matchedData.logisticsRoute') }}</el-tag>
      </div>
      <div class="bg-slate-50 rounded-lg p-3 space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.route') }}:</span>
          <span class="text-slate-700 font-medium">
            {{ data.logistics_route.origin }} → {{ data.logistics_route.destination }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.shippingMethod') }}:</span>
          <span class="text-slate-700">
            {{ data.logistics_route.shipping_method === 'sea_freight' ? t('matchedData.seaFreight') : t('matchedData.airFreight') }}
          </span>
        </div>
        <div v-if="data.logistics_route.container_type" class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.container') }}:</span>
          <span class="text-slate-700">{{ data.logistics_route.container_type }}</span>
        </div>
        <div v-if="data.logistics_route.weight_range" class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.weightRange') }}:</span>
          <span class="text-slate-700">{{ data.logistics_route.weight_range }} kg</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.price') }}:</span>
          <span class="font-semibold text-slate-800">
            {{ data.logistics_route.currency }} {{ data.logistics_route.price }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">{{ t('matchedData.transitTime') }}:</span>
          <span class="text-slate-700">{{ data.logistics_route.transit_days }} {{ t('matchedData.days') }}</span>
        </div>
      </div>
    </div>

    <!-- 无匹配数据 -->
    <div v-if="!data.order && !data.logistics_route" class="text-center py-4 text-slate-400 text-sm">
      {{ t('matchedData.noMatchedData') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { MatchedData } from '../types/index'

const { t } = useI18n()

interface Props {
  data: MatchedData
}

defineProps<Props>()

function getOrderStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, any> = {
    confirmed: 'success',
    pending: 'warning',
    cancelled: 'danger',
    completed: 'info',
  }
  return map[status] || 'info'
}

function getShippingStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, any> = {
    delivered: 'success',
    in_transit: 'info',
    not_shipped: 'warning',
    exception: 'danger',
  }
  return map[status] || 'info'
}
</script>
