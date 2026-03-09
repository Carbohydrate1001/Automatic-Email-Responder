import axios from 'axios'
import router from '../router/index'

const api = axios.create({
  baseURL: 'http://localhost:5005',
  withCredentials: true,
  timeout: 30000,
})

// Response interceptor: redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      router.push('/login')
    }
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

// --- Auth APIs ---
export const authApi = {
  getStatus: () => api.get('/auth/status'),
  getMe: () => api.get('/auth/me'),
  login: () => { window.location.href = 'http://localhost:5005/auth/login' },
  logout: () => { window.location.href = 'http://localhost:5005/auth/logout' },
}

// --- Email APIs ---
export const emailApi = {
  fetchEmails: (top = 10) => api.post('/api/fetch', { top }),

  listEmails: (params: {
    page?: number
    per_page?: number
    status?: string
    category?: string
    search?: string
  }) => api.get('/api/emails', { params }),

  getEmail: (id: number) => api.get(`/api/emails/${id}`),

  approveEmail: (id: number, replyText?: string) =>
    api.post(`/api/emails/${id}/approve`, replyText ? { reply_text: replyText } : {}),

  rejectEmail: (id: number) => api.post(`/api/emails/${id}/reject`),

  getStats: () => api.get('/api/stats'),
}

export default api
