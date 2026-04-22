<template>
  <div class="pt-16 min-h-screen bg-slate-100">
    <div class="max-w-5xl mx-auto px-6 py-6">
      <!-- Page header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-slate-800">产品管理</h2>
          <p class="text-slate-500 text-sm mt-1">管理公司产品目录，用于自动回复询价邮件</p>
        </div>
        <button
          class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-all cursor-pointer"
          @click="openAddDialog"
        >
          <Plus class="w-4 h-4" />
          新增产品
        </button>
      </div>

      <!-- Product table -->
      <div class="card p-0 overflow-hidden">
        <el-table
          v-loading="loading"
          :data="products"
          style="width: 100%"
          row-class-name="hover:bg-slate-50 transition-colors"
        >
          <el-table-column label="产品名称" min-width="200">
            <template #default="{ row }">
              <span class="font-medium text-slate-800">{{ row.product_name }}</span>
            </template>
          </el-table-column>

          <el-table-column label="单价" width="140">
            <template #default="{ row }">
              <span class="text-slate-700">{{ row.currency }} {{ row.unit_price }}</span>
            </template>
          </el-table-column>

          <el-table-column label="最小订购量" width="120">
            <template #default="{ row }">
              <span class="text-slate-600">{{ row.min_order_quantity }}</span>
            </template>
          </el-table-column>

          <el-table-column label="交付周期（天）" width="140">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.delivery_lead_time_days }} 天</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <div class="flex gap-2">
                <el-button type="primary" link size="small" @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-button type="danger" link size="small" @click="handleDelete(row.product_name)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="!loading && products.length === 0" class="py-16 text-center text-slate-400">
          <Package class="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p>暂无产品，点击"新增产品"开始添加</p>
        </div>
      </div>
    </div>

    <!-- Add/Edit dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingProduct ? '编辑产品' : '新增产品'"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="120px" @submit.prevent>
        <el-form-item label="产品名称" required>
          <el-input
            v-model="form.product_name"
            placeholder="如：Sea Freight (Standard)"
            :disabled="!!editingProduct"
          />
        </el-form-item>
        <el-form-item label="单价" required>
          <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="币种" required>
          <el-select v-model="form.currency" style="width: 100%">
            <el-option label="USD" value="USD" />
            <el-option label="CNY" value="CNY" />
            <el-option label="EUR" value="EUR" />
            <el-option label="HKD" value="HKD" />
          </el-select>
        </el-form-item>
        <el-form-item label="最小订购量" required>
          <el-input-number v-model="form.min_order_quantity" :min="1" :precision="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="交付周期(天)" required>
          <el-input-number v-model="form.delivery_lead_time_days" :min="1" :precision="0" style="width: 100%" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Package } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { companyApi, type ProductRecord } from '../api/index'

const loading = ref(false)
const saving = ref(false)
const products = ref<ProductRecord[]>([])
const dialogVisible = ref(false)
const editingProduct = ref<ProductRecord | null>(null)

const defaultForm = (): ProductRecord => ({
  product_name: '',
  unit_price: 0,
  currency: 'USD',
  min_order_quantity: 1,
  delivery_lead_time_days: 7,
})

const form = ref<ProductRecord>(defaultForm())

async function loadProducts() {
  loading.value = true
  try {
    const res = await companyApi.listProducts()
    products.value = res.data.products || []
  } catch (e: any) {
    ElMessage.error('加载产品失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  editingProduct.value = null
  form.value = defaultForm()
  dialogVisible.value = true
}

function openEditDialog(product: ProductRecord) {
  editingProduct.value = product
  form.value = { ...product }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.product_name.trim()) {
    ElMessage.warning('请输入产品名称')
    return
  }

  saving.value = true
  try {
    if (editingProduct.value) {
      await companyApi.upsertProduct(editingProduct.value.product_name, form.value)
      ElMessage.success('产品已更新')
    } else {
      await companyApi.addProduct(form.value)
      ElMessage.success('产品已添加')
    }
    dialogVisible.value = false
    await loadProducts()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(productName: string) {
  try {
    await ElMessageBox.confirm(`确定要删除产品「${productName}」吗？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await companyApi.deleteProduct(productName)
    ElMessage.success('产品已删除')
    await loadProducts()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e?.response?.data?.error || e?.message || '未知错误'))
    }
  }
}

onMounted(loadProducts)
</script>
