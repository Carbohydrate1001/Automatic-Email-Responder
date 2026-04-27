<template>
  <div class="card">
    <h4 class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
      匹配的数据库内容
    </h4>

    <!-- 订单信息 -->
    <div v-if="data.order" class="space-y-2">
      <div class="flex items-center gap-2 mb-3">
        <el-tag type="primary" size="small">订单信息</el-tag>
      </div>
      <div class="bg-slate-50 rounded-lg p-3 space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-slate-500">订单号:</span>
          <span class="font-mono font-semibold text-slate-800">{{ data.order.order_number }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">产品:</span>
          <span class="text-slate-700">{{ data.order.product_name }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">金额:</span>
          <span class="font-semibold text-slate-800">
            {{ data.order.currency }} {{ data.order.total_amount.toFixed(2) }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">订单状态:</span>
          <el-tag :type="getOrderStatusType(data.order.order_status)" size="small">
            {{ data.order.order_status }}
          </el-tag>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">物流状态:</span>
          <el-tag :type="getShippingStatusType(data.order.shipping_status)" size="small">
            {{ data.order.shipping_status }}
          </el-tag>
        </div>
        <div v-if="data.order.tracking_number" class="flex justify-between">
          <span class="text-slate-500">追踪号:</span>
          <span class="font-mono text-slate-700">{{ data.order.tracking_number }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">目的地:</span>
          <span class="text-slate-700">{{ data.order.destination }}</span>
        </div>
      </div>
    </div>

    <!-- 物流路线信息 -->
    <div v-if="data.logistics_route" class="space-y-2">
      <div class="flex items-center gap-2 mb-3">
        <el-tag type="success" size="small">物流路线</el-tag>
      </div>
      <div class="bg-slate-50 rounded-lg p-3 space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-slate-500">路线:</span>
          <span class="text-slate-700 font-medium">
            {{ data.logistics_route.origin }} → {{ data.logistics_route.destination }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">运输方式:</span>
          <span class="text-slate-700">
            {{ data.logistics_route.shipping_method === 'sea_freight' ? '海运' : '空运' }}
          </span>
        </div>
        <div v-if="data.logistics_route.container_type" class="flex justify-between">
          <span class="text-slate-500">集装箱:</span>
          <span class="text-slate-700">{{ data.logistics_route.container_type }}</span>
        </div>
        <div v-if="data.logistics_route.weight_range" class="flex justify-between">
          <span class="text-slate-500">重量范围:</span>
          <span class="text-slate-700">{{ data.logistics_route.weight_range }} kg</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">价格:</span>
          <span class="font-semibold text-slate-800">
            {{ data.logistics_route.currency }} {{ data.logistics_route.price }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">运输时效:</span>
          <span class="text-slate-700">{{ data.logistics_route.transit_days }} 天</span>
        </div>
      </div>
    </div>

    <!-- 无匹配数据 -->
    <div v-if="!data.order && !data.logistics_route" class="text-center py-4 text-slate-400 text-sm">
      未找到匹配的数据库内容
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MatchedData } from '../types/index'

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
