import axios from 'axios'

const API_BASE = '/api'

export const api = {
  // Auth
  requestOTP: (email) => axios.post(`${API_BASE}/auth/otp/request`, { email }),
  verifyOTP: (email, otp) => axios.post(`${API_BASE}/auth/otp/verify`, { email, otp }),
  
  // User
  getCurrentUser: () => axios.get(`${API_BASE}/user/me`),
  logout: () => axios.post(`${API_BASE}/user/logout`),
  requestPremium: () => axios.post(`${API_BASE}/user/request-premium`),
  
  // Upload
  uploadFile: (formData) => axios.post(`${API_BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  listUploads: () => axios.get(`${API_BASE}/upload`),
  deleteUpload: (id) => axios.delete(`${API_BASE}/upload/${id}`),
  
  // PDF Splitting
  splitPdf: (uploadId, targetSizeMb = 6.0) => 
    axios.post(`${API_BASE}/upload/${uploadId}/split`, null, { params: { target_size_mb: targetSizeMb } }),
  getSplitParts: (uploadId) => axios.get(`${API_BASE}/upload/${uploadId}/split-parts`),
  renameSplitPart: (partId, customName) => 
    axios.put(`${API_BASE}/upload/split-parts/${partId}/rename`, { custom_name: customName }),
  previewSplitPart: (partId) => 
    axios.get(`${API_BASE}/upload/split-parts/${partId}/preview`, { responseType: 'blob' }),
  downloadSplitPart: (partId) => 
    axios.get(`${API_BASE}/upload/split-parts/${partId}/download`),
  
  // QnA
  generateQnA: (data) => axios.post(`${API_BASE}/qna/generate`, data),
  detectContentLanguage: (uploadId, partIds) => {
    const params = {}
    if (uploadId) params.upload_id = uploadId
    if (partIds && partIds.length > 0) params.part_ids = partIds.join(',')
    return axios.get(`${API_BASE}/qna/detect-language`, { params })
  },
  listQnASets: () => axios.get(`${API_BASE}/qna/sets`),
  getQnASet: (id) => axios.get(`${API_BASE}/qna/sets/${id}`),
  downloadQnASet: (id, format, outputFormat) => 
    axios.get(`${API_BASE}/qna/sets/${id}/download`, {
      params: { format, output_format: outputFormat },
      responseType: 'blob'
    }),
  deleteQnASet: (id) => axios.delete(`${API_BASE}/qna/sets/${id}`),
  
  // Admin
  listPremiumRequests: () => axios.get(`${API_BASE}/admin/premium-requests`),
  approvePremiumRequest: (id, notes) => 
    axios.post(`${API_BASE}/admin/premium-requests/${id}/approve`, { notes }),
  rejectPremiumRequest: (id) => 
    axios.post(`${API_BASE}/admin/premium-requests/${id}/reject`),
  listUsers: (period = 'all') => axios.get(`${API_BASE}/admin/users`, { params: { period } }),
  exportUsers: (period = 'all') => axios.get(`${API_BASE}/admin/users/export`, { params: { period }, responseType: 'blob' }),
  deleteUsers: (ids) => axios.delete(`${API_BASE}/admin/users`, { data: { ids } }),
  adjustQuota: (data) => axios.post(`${API_BASE}/admin/quota-adjust`, data),
  disableUser: (id) => axios.post(`${API_BASE}/admin/users/${id}/disable`),
  enableUser: (id) => axios.post(`${API_BASE}/admin/users/${id}/enable`),
  switchUserToFree: (id) => axios.post(`${API_BASE}/admin/users/${id}/switch-to-free`),
  switchUserToPremium: (id) => axios.post(`${API_BASE}/admin/users/${id}/switch-to-premium`),
  deleteUser: (id) => axios.delete(`${API_BASE}/admin/users/${id}`),
  getUsageLogs: (userId, period = 'all') => axios.get(`${API_BASE}/admin/usage-logs`, { params: { user_id: userId, period } }),
  exportUsageLogs: (period = 'all') => axios.get(`${API_BASE}/admin/usage-logs/export`, { params: { period }, responseType: 'blob' }),
  deleteUsageLogs: (ids) => axios.delete(`${API_BASE}/admin/usage-logs`, { data: { ids } }),
  getAuditLogs: () => axios.get(`${API_BASE}/admin/audit-logs`),
  listAllUploads: (period = 'all') => axios.get(`${API_BASE}/admin/uploads`, { params: { period } }),
  exportUploads: (period = 'all') => axios.get(`${API_BASE}/admin/uploads/export`, { params: { period }, responseType: 'blob' }),
  deleteUploads: (ids) => axios.delete(`${API_BASE}/admin/uploads`, { data: { ids } }),
  viewUpload: (id) => axios.get(`${API_BASE}/admin/uploads/${id}/view`, { responseType: 'blob' }),
  
  // User Profile
  getUserProfile: () => axios.get(`${API_BASE}/user/profile`),
  getGenerationStats: () => axios.get(`${API_BASE}/user/generation-stats`),
  
  // Reviews
  submitReview: (data) => axios.post(`${API_BASE}/reviews/submit`, data),
  getReviews: (period = 'all') => axios.get(`${API_BASE}/reviews/admin/reviews`, { params: { period } }),
  exportReviews: (period = 'all') => axios.get(`${API_BASE}/reviews/admin/reviews/export`, { params: { period }, responseType: 'blob' }),
  deleteReview: (id) => axios.delete(`${API_BASE}/reviews/${id}`),
  deleteReviewsBulk: (ids) => axios.delete(`${API_BASE}/reviews/admin/reviews/bulk`, { data: { ids } }),
  
  // AI Usage (Admin)
  getAIUsageLogs: (period = 'all') => axios.get(`${API_BASE}/admin/ai/usage`, { params: { period } }),
  exportAIUsageLogs: (period = 'all') => axios.get(`${API_BASE}/admin/ai/usage/export`, { params: { period }, responseType: 'blob' }),
  deleteAIUsageLogs: (ids) => axios.delete(`${API_BASE}/admin/ai/usage`, { data: { ids } }),
  getAIUsageStats: () => axios.get(`${API_BASE}/admin/ai/usage/stats`),
  updateAIThreshold: (threshold) => axios.post(`${API_BASE}/admin/ai/usage/threshold`, null, { params: { threshold } }),
  
  // Login Logs (Admin)
  getLoginLogs: (userId, period = 'all') => {
    const url = userId ? `${API_BASE}/admin/login-logs?user_id=${userId}` : `${API_BASE}/admin/login-logs`
    return axios.get(url, { params: { period } })
  },
  exportLoginLogs: (period = 'all') => {
    const url = `${API_BASE}/admin/login-logs/export`
    return axios.get(url, { params: { period }, responseType: 'blob' })
  },
  deleteLoginLogs: (ids) => axios.delete(`${API_BASE}/admin/login-logs`, { data: { ids } }),
}

export default api

