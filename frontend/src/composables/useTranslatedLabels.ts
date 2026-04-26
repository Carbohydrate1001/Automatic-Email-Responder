import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

export function useTranslatedLabels() {
  const { t } = useI18n()

  const categoryLabels = computed(() => ({
    pricing_inquiry: t('category.pricing_inquiry'),
    order_cancellation: t('category.order_cancellation'),
    order_tracking: t('category.order_tracking'),
    shipping_time: t('category.shipping_time'),
    shipping_exception: t('category.shipping_exception'),
    billing_invoice: t('category.billing_invoice'),
    non_business: t('category.non_business'),
  }))

  const statusLabels = computed(() => ({
    auto_sent: t('status.auto_sent'),
    pending_review: t('status.pending_review'),
    approved: t('status.approved'),
    rejected: t('status.rejected'),
    send_failed: t('status.send_failed'),
    ignored_no_reply: t('status.ignored_no_reply'),
  }))

  return {
    categoryLabels,
    statusLabels,
  }
}
