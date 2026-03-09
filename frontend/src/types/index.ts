export interface EmailRecord {
  id: number
  message_id: string
  subject: string
  sender: string
  received_at: string
  body: string
  category: string
  confidence: number
  reasoning: string
  status: 'auto_sent' | 'pending_review' | 'approved' | 'rejected'
  reply_text: string
  sent_at: string | null
  created_at: string
}

export interface EmailListResponse {
  total: number
  page: number
  per_page: number
  emails: EmailRecord[]
}

export interface StatsResponse {
  total: number
  auto_sent: number
  approved: number
  pending_review: number
  rejected: number
  auto_rate: number
  avg_confidence: number
  categories: { category: string; cnt: number }[]
  daily: { day: string; handled: number; pending: number }[]
}

export interface AuthUser {
  name: string
  email: string
  oid?: string
}

export const CATEGORY_LABELS: Record<string, string> = {
  pricing_inquiry: '询价/报价',
  order_cancellation: '取消订单/退款',
  order_tracking: '订单追踪',
  shipping_time: '运输时间查询',
  shipping_exception: '运输异常',
  billing_invoice: '账单/发票',
}

export const CATEGORY_COLORS: Record<string, string> = {
  pricing_inquiry: '#3B82F6',
  order_cancellation: '#EF4444',
  order_tracking: '#10B981',
  shipping_time: '#F59E0B',
  shipping_exception: '#F97316',
  billing_invoice: '#6366F1',
}

export const STATUS_LABELS: Record<string, string> = {
  auto_sent: '已自动发送',
  pending_review: '待人工审核',
  approved: '已审核发送',
  rejected: '已拒绝',
}
