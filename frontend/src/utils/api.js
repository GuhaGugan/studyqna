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
  listUsers: () => axios.get(`${API_BASE}/admin/users`),
  adjustQuota: (data) => axios.post(`${API_BASE}/admin/quota-adjust`, data),
  disableUser: (id) => axios.post(`${API_BASE}/admin/users/${id}/disable`),
  enableUser: (id) => axios.post(`${API_BASE}/admin/users/${id}/enable`),
  switchUserToFree: (id) => axios.post(`${API_BASE}/admin/users/${id}/switch-to-free`),
  switchUserToPremium: (id) => axios.post(`${API_BASE}/admin/users/${id}/switch-to-premium`),
  deleteUser: (id) => axios.delete(`${API_BASE}/admin/users/${id}`),
  getUsageLogs: (userId) => axios.get(`${API_BASE}/admin/usage-logs`, { params: { user_id: userId } }),
  exportUsageLogs: (period = 'all') => axios.get(`${API_BASE}/admin/usage-logs/export`, {
    params: { period },
    responseType: 'blob'
  }),
  getAuditLogs: () => axios.get(`${API_BASE}/admin/audit-logs`),
  listAllUploads: () => axios.get(`${API_BASE}/admin/uploads`),
  viewUpload: (id) => axios.get(`${API_BASE}/admin/uploads/${id}/view`, { responseType: 'blob' }),
  
  // User Profile
  getUserProfile: () => axios.get(`${API_BASE}/user/profile`),
  getGenerationStats: () => axios.get(`${API_BASE}/user/generation-stats`),
  
  // Reviews
  submitReview: (data) => axios.post(`${API_BASE}/reviews/submit`, data),
  getReviews: () => axios.get(`${API_BASE}/reviews/admin/reviews`),
  deleteReview: (id) => axios.delete(`${API_BASE}/reviews/${id}`),
  
  // AI Usage (Admin)
  getAIUsageLogs: () => axios.get(`${API_BASE}/admin/ai/usage`),
  getAIUsageStats: () => axios.get(`${API_BASE}/admin/ai/usage/stats`),
  updateAIThreshold: (threshold) => axios.post(`${API_BASE}/admin/ai/usage/threshold`, null, { params: { threshold } }),
  
  // Login Logs (Admin)
  getLoginLogs: (userId) => {
    const url = userId ? `${API_BASE}/admin/login-logs?user_id=${userId}` : `${API_BASE}/admin/login-logs`
    return axios.get(url)
  },
  exportLoginLogs: (period = 'all') => {
    const url = `${API_BASE}/admin/login-logs/export`
    return axios.get(url, { params: { period }, responseType: 'blob' })
  },
}

export default api

