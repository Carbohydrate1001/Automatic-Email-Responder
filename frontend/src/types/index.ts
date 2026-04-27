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
  status: 'auto_sent' | 'pending_review' | 'approved' | 'rejected' | 'send_failed' | 'ignored_no_reply'

  reply_text: string

  sent_at: string | null
  created_at: string

  // Rubric评分
  classification_rubric_scores?: {
    scores: Record<string, {
      score: number
      reasoning: string
    }>
    weighted_score: number
    confidence: number
    rubric_version?: string
  }

  auto_send_rubric_scores?: {
    scores: Record<string, {
      score: number
      reasoning: string
    }>
    weighted_score: number
    auto_send_recommended: boolean
    thresholds_applied?: {
      auto_send_minimum: number
      require_all_above: number
    }
  }
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
  send_failed: number
  ignored_no_reply: number
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
  non_business: '非业务邮件（无需回复）',
}


export const CATEGORY_COLORS: Record<string, string> = {
  pricing_inquiry: '#3B82F6',
  order_cancellation: '#EF4444',
  order_tracking: '#10B981',
  shipping_time: '#F59E0B',
  shipping_exception: '#F97316',
  billing_invoice: '#6366F1',
  non_business: '#64748B',
}


export const STATUS_LABELS: Record<string, string> = {
  auto_sent: '已自动发送',
  pending_review: '待人工审核',
  approved: '已审核发送',
  rejected: '已拒绝',
  send_failed: '发送失败（可重试）',
  ignored_no_reply: '已忽略（无需回复）',
}

// 匹配数据接口
export interface MatchedData {
  order?: {
    order_number: string
    customer_email: string
    product_name: string
    quantity: number
    total_amount: number
    currency: string
    order_status: string
    shipping_status: string
    tracking_number?: string
    destination: string
  }
  logistics_route?: {
    origin: string
    destination: string
    shipping_method: string
    container_type?: string
    weight_range?: string
    price: number
    currency: string
    transit_days: number
  }
}


