import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'

const AdminDashboard = () => {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState('requests')
  const [premiumRequests, setPremiumRequests] = useState([])
  const [creditRequests, setCreditRequests] = useState([])

  const [activeTab, setActiveTab] = useState('users')

  const [users, setUsers] = useState([])
  const [premiumRequests, setPremiumRequests] = useState([])
  const [uploads, setUploads] = useState([])
  const [reviews, setReviews] = useState([])
  const [usageLogs, setUsageLogs] = useState([])
  const [loginLogs, setLoginLogs] = useState([])
  const [aiUsageLogs, setAiUsageLogs] = useState([])
  const [aiUsageStats, setAiUsageStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [usageFilterPeriod, setUsageFilterPeriod] = useState('all')
  const [loginFilterPeriod, setLoginFilterPeriod] = useState('all')
  const [usersFilterPeriod, setUsersFilterPeriod] = useState('all')
  const [uploadsFilterPeriod, setUploadsFilterPeriod] = useState('all')
  const [reviewsFilterPeriod, setReviewsFilterPeriod] = useState('all')
  const [aiUsageFilterPeriod, setAiUsageFilterPeriod] = useState('all')
  const [selectedLoginLogIds, setSelectedLoginLogIds] = useState([])
  const [selectedUsageLogIds, setSelectedUsageLogIds] = useState([])
  const [selectedUserIds, setSelectedUserIds] = useState([])
  const [selectedUploadIds, setSelectedUploadIds] = useState([])
  const [selectedReviewIds, setSelectedReviewIds] = useState([])
  const [selectedAIUsageIds, setSelectedAIUsageIds] = useState([])
  const tabNavRef = useRef(null)

  useEffect(() => {

    if (activeTab === 'requests') fetchPremiumRequests()
    if (activeTab === 'credit-requests') fetchCreditRequests()


    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'uploads') fetchUploads(uploadsFilterPeriod)
    if (activeTab === 'reviews') fetchReviews(reviewsFilterPeriod)
    if (activeTab === 'ai-usage') {
      fetchAIUsageLogs(aiUsageFilterPeriod)
      fetchAIUsageStats()
    }
    if (activeTab === 'logs') fetchUsageLogs()
    if (activeTab === 'login-logs') fetchLoginLogs()
  }, [activeTab])


  const fetchPremiumRequests = async () => {
    setLoading(true)
    try {
      const response = await api.listPremiumRequests()
      setPremiumRequests(response.data)
    } catch (error) {
      toast.error('Failed to load premium requests')
    } finally {
      setLoading(false)
    }
  }


  const fetchCreditRequests = async () => {
    setLoading(true)
    try {
      const response = await api.listCreditRequests()
      console.log('Credit requests response:', response.data)
      setCreditRequests(response.data || [])
    } catch (error) {
      console.error('Error fetching credit requests:', error)
      toast.error('Failed to load credit requests')
      setCreditRequests([])
    } finally {
      setLoading(false)
    }
  }

  const fetchUsers = async (period = usersFilterPeriod) => {
    setLoading(true)
    try {

  const fetchUsers = async (period = usersFilterPeriod) => {
    setLoading(true)
    try {

      const response = await api.listUsers(period)
      setUsers(response.data)
      setSelectedUserIds([])
    } catch (error) {
      toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const fetchUploads = async (period = uploadsFilterPeriod) => {
    setLoading(true)
    try {
      const response = await api.listAllUploads(period)
      setUploads(response.data)
      setSelectedUploadIds([])
    } catch (error) {
      toast.error('Failed to load uploads')
    } finally {
      setLoading(false)
    }
  }

  const fetchReviews = async (period = reviewsFilterPeriod) => {
    setLoading(true)
    try {
      const response = await api.getReviews(period)
      setReviews(response.data)
      setSelectedReviewIds([])
    } catch (error) {
      toast.error('Failed to load reviews')
    } finally {
      setLoading(false)
    }
  }

  const fetchAIUsageLogs = async (period = aiUsageFilterPeriod) => {
    setLoading(true)
    try {
      const response = await api.getAIUsageLogs(period)
      setAiUsageLogs(response.data)
      setSelectedAIUsageIds([])
    } catch (error) {
      toast.error('Failed to load AI usage logs')
    } finally {
      setLoading(false)
    }
  }

  const fetchAIUsageStats = async () => {
    try {
      const response = await api.getAIUsageStats()
      setAiUsageStats(response.data)
      
      // Show alert if threshold reached
      if (response.data.is_threshold_reached) {
        toast.error(
          `⚠️ AI API Usage Threshold Reached! ${response.data.current_month_tokens.toLocaleString()}/${response.data.threshold.toLocaleString()} tokens (${response.data.threshold_percentage.toFixed(1)}%)`,
          { duration: 10000 }
        )
      } else if (response.data.threshold_percentage >= 80) {
        toast.error(
          `⚠️ AI Usage Warning: ${response.data.threshold_percentage.toFixed(1)}% of threshold used. Please recharge soon.`,
          { duration: 8000 }
        )
      }
    } catch (error) {
      toast.error('Failed to load AI usage stats')
    }
  }

  const fetchUsageLogs = async (period = usageFilterPeriod) => {
    setLoading(true)
    try {
      const response = await api.getUsageLogs(null, period)
      setUsageLogs(response.data)
      setSelectedUsageLogIds([])
    } catch (error) {
      toast.error('Failed to load usage logs')
    } finally {
      setLoading(false)
    }
  }

  const fetchLoginLogs = async (period = loginFilterPeriod) => {
    setLoading(true)
    try {
      const response = await api.getLoginLogs(null, period)
      setLoginLogs(response.data)
      setSelectedLoginLogIds([])
    } catch (error) {
      toast.error('Failed to load login logs')
    } finally {
      setLoading(false)
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    try {
      // Refresh all sections based on current tab
      await Promise.all([
        fetchPremiumRequests(),
        fetchCreditRequests(),
        fetchUsers(),
        fetchUploads(),
        fetchReviews(),
        fetchAIUsageLogs(),
        fetchAIUsageStats(),
        fetchUsageLogs(),
        fetchLoginLogs()
      ])
      toast.success('✅ All data refreshed!', { duration: 2000 })
    } catch (error) {
      toast.error('Some data failed to refresh')
    } finally {
      setLoading(false)
    }
  }

  const handleExportUsers = async () => {
    try {
      const response = await api.exportUsers(usersFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `users_${usersFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Users exported')
    } catch (error) {
      toast.error('Failed to export users')
    }
  }

  const handleDeleteUsers = async () => {
    if (selectedUserIds.length === 0) {
      toast.error('Select at least one user to delete')
      return
    }
    const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected user(s)? This cannot be undone.'
    if (!window.confirm(warnExport)) return
    if (!window.confirm(`Confirm delete ${selectedUserIds.length} selected user(s)?`)) return
    try {
      await api.deleteUsers(selectedUserIds)
      toast.success('Selected users deleted')
      fetchUsers(usersFilterPeriod)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete users')
    }
  }

  const handleDeleteUploads = async () => {
    if (selectedUploadIds.length === 0) {
      toast.error('Select at least one upload to delete')
      return
    }
    const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected upload(s)? This cannot be undone.'
    if (!window.confirm(warnExport)) return
    if (!window.confirm(`Confirm delete ${selectedUploadIds.length} selected upload(s)?`)) return
    try {
      await api.deleteUploads(selectedUploadIds)
      toast.success('Selected uploads deleted')
      fetchUploads(uploadsFilterPeriod)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete uploads')
    }
  }

  const handleDeleteReviews = async () => {
    if (selectedReviewIds.length === 0) {
      toast.error('Select at least one review to delete')
      return
    }
    const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected review(s)? This cannot be undone.'
    if (!window.confirm(warnExport)) return
    if (!window.confirm(`Confirm delete ${selectedReviewIds.length} selected review(s)?`)) return
    try {
      await api.deleteReviewsBulk(selectedReviewIds)
      toast.success('Selected reviews deleted')
      fetchReviews(reviewsFilterPeriod)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete reviews')
    }
  }

  const handleDeleteAIUsage = async () => {
    if (selectedAIUsageIds.length === 0) {
      toast.error('Select at least one log to delete')
      return
    }
    const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected log(s)? This cannot be undone.'
    if (!window.confirm(warnExport)) return
    if (!window.confirm(`Confirm delete ${selectedAIUsageIds.length} selected log(s)?`)) return
    try {
      await api.deleteAIUsageLogs(selectedAIUsageIds)
      toast.success('Selected AI usage logs deleted')
      fetchAIUsageLogs(aiUsageFilterPeriod)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete logs')
    }
  }

  const handleExportUploads = async () => {
    try {
      const response = await api.exportUploads(uploadsFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `uploads_${uploadsFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Uploads exported')
    } catch (error) {
      toast.error('Failed to export uploads')
    }
  }

  const handleExportReviews = async () => {
    try {
      const response = await api.exportReviews(reviewsFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `reviews_${reviewsFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Reviews exported')
    } catch (error) {
      toast.error('Failed to export reviews')
    }
  }

  const handleExportAIUsage = async () => {
    try {
      const response = await api.exportAIUsageLogs(aiUsageFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai_usage_${aiUsageFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('AI usage exported')
    } catch (error) {
      toast.error('Failed to export AI usage logs')
    }
  }

  const handleExportLoginLogs = async () => {
    try {
      const response = await api.exportLoginLogs(loginFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `login_logs_${loginFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Login logs exported')
    } catch (error) {
      toast.error('Failed to export login logs')
    }
  }

  // Derived totals for AI usage based on current filter
  const filteredAIUsageTotals = (() => {
    let totalTokens = 0
    let promptTokens = 0
    let completionTokens = 0
    let count = 0
    aiUsageLogs.forEach((log) => {
      totalTokens += log.total_tokens || 0
      promptTokens += log.prompt_tokens || 0
      completionTokens += log.completion_tokens || 0
      count += 1
    })
    return { totalTokens, promptTokens, completionTokens, count }

    // Calculate cost (GPT-4o-mini pricing: $0.00015/1K input, $0.0006/1K output)
    const cost = (promptTokens / 1000 * 0.00015) + (completionTokens / 1000 * 0.0006)
    return { totalTokens, promptTokens, completionTokens, count, cost }

  })()

  const handleExportUsageLogs = async () => {
    try {
      const response = await api.exportUsageLogs(usageFilterPeriod)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `usage_logs_${usageFilterPeriod}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Usage logs exported')
    } catch (error) {
      toast.error('Failed to export usage logs')
    }
  }

  const handleViewUpload = async (uploadId) => {
    try {
      const upload = uploads.find(u => u.id === uploadId)
      if (!upload) {
        toast.error('Upload not found')
        return
      }

      const response = await api.viewUpload(uploadId)
      // Ensure correct MIME type for blob
      const mimeType = upload.file_type === 'pdf' 
        ? 'application/pdf' 
        : response.headers['content-type'] || 'image/jpeg'
      const blob = new Blob([response.data], { type: mimeType })
      const url = window.URL.createObjectURL(blob)
      
      // Check if it's a PDF or image
      if (upload.file_type === 'pdf') {
        // Open PDF in new window with proper viewer using iframe
        const newWindow = window.open('', '_blank')
        if (newWindow) {
          newWindow.document.write(`
            <!DOCTYPE html>
            <html>
              <head>
                <title>PDF Preview - ${upload.file_name}</title>
                <style>
                  * { margin: 0; padding: 0; box-sizing: border-box; }
                  body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f5;
                  }
                  .header {
                    background: white;
                    padding: 12px 20px;
                    border-bottom: 1px solid #e5e5e5;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  }
                  .header h1 {
                    font-size: 16px;
                    font-weight: 600;
                    color: #333;
                  }
                  .close-btn {
                    background: #ef4444;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background 0.2s;
                  }
                  .close-btn:hover {
                    background: #dc2626;
                  }
                  iframe { 
                    width: 100%; 
                    height: calc(100vh - 50px); 
                    border: none; 
                    display: block;
                  }
                </style>
              </head>
              <body>
                <div class="header">
                  <h1>📄 ${upload.file_name}</h1>
                  <button class="close-btn" onclick="window.close()">Close</button>
                </div>
                <embed 
                  src="${url}#toolbar=1&navpanes=1&scrollbar=1&zoom=page-width" 
                  type="application/pdf" 
                  style="width: 100%; height: calc(100vh - 50px);"
                  id="pdfEmbed"
                />
                <iframe 
                  src="${url}#toolbar=1&navpanes=1&scrollbar=1" 
                  type="application/pdf"
                  style="width: 100%; height: calc(100vh - 50px); display: none;"
                  id="pdfIframe"
                ></iframe>
                <script>
                  // Try embed first, fallback to iframe, then download
                  const embed = document.getElementById('pdfEmbed');
                  const iframe = document.getElementById('pdfIframe');
                  
                  // Check if embed works after a short delay
                  setTimeout(() => {
                    // If embed doesn't seem to work, try iframe
                    if (embed && embed.offsetHeight === 0) {
                      embed.style.display = 'none';
                      iframe.style.display = 'block';
                    }
                  }, 500);
                  
                  // Final fallback - show download option
                  embed.onerror = function() {
                    document.body.innerHTML = 
                      '<div style="padding: 40px; text-align: center; background: white; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">' +
                      '<h2 style="margin-bottom: 20px; color: #333;">PDF Preview Not Available</h2>' +
                      '<p style="margin: 20px 0; color: #666;">Your browser may not support PDF viewing in this format.</p>' +
                      '<a href="${url}" download="${upload.file_name}" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 10px; font-weight: 500;">Download PDF</a>' +
                      '</div>';
                  };
                  
                  iframe.onerror = function() {
                    document.body.innerHTML = 
                      '<div style="padding: 40px; text-align: center; background: white; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">' +
                      '<h2 style="margin-bottom: 20px; color: #333;">PDF Preview Not Available</h2>' +
                      '<p style="margin: 20px 0; color: #666;">Please download the PDF to view it.</p>' +
                      '<a href="${url}" download="${upload.file_name}" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 10px; font-weight: 500;">Download PDF</a>' +
                      '</div>';
                  };
                </script>
              </body>
            </html>
          `)
          newWindow.document.close()
        }
      } else {
        // For images, open in new window with proper styling
        const newWindow = window.open('', '_blank')
        if (newWindow) {
          newWindow.document.write(`
            <!DOCTYPE html>
            <html>
              <head>
                <title>Image Preview - ${upload.file_name}</title>
                <style>
                  * { margin: 0; padding: 0; box-sizing: border-box; }
                  body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #1a1a1a;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    padding: 20px;
                  }
                  .container {
                    text-align: center;
                    max-width: 100%;
                  }
                  .header {
                    color: white;
                    margin-bottom: 20px;
                  }
                  .header h2 {
                    font-size: 18px;
                    font-weight: 500;
                  }
                  img {
                    max-width: 100%;
                    max-height: 90vh;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                  }
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h2>🖼️ ${upload.file_name}</h2>
                  </div>
                  <img src="${url}" alt="${upload.file_name}" />
                </div>
              </body>
            </html>
          `)
          newWindow.document.close()
        }
      }
    } catch (error) {
      toast.error('Failed to preview file')
    }
  }

  const handleQuotaAdjust = async (userId, questionsLimit, questionsUsed) => {
    try {
      await api.adjustQuota({
        user_id: userId,
        questions_limit: questionsLimit,
        questions_used: questionsUsed
      })
      toast.success('Quota adjusted successfully')
      fetchUsers(usersFilterPeriod)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to adjust quota')
    }
  }


  const handleApproveCreditRequest = async (requestId, notes = '') => {
    try {
      await api.approveCreditRequest(requestId, { notes })
      toast.success('Credit request approved successfully')
      fetchCreditRequests()
    } catch (error) {
      console.error('Approve credit request error:', error)
      toast.error(error.response?.data?.detail || 'Failed to approve credit request')
    }
  }

  const handleRejectCreditRequest = async (requestId, notes = '') => {
    try {
      await api.rejectCreditRequest(requestId, notes)
      toast.success('Credit request rejected')
      fetchCreditRequests()
    } catch (error) {
      console.error('Reject credit request error:', error)
      toast.error(error.response?.data?.detail || 'Failed to reject credit request')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
              <p className="text-sm text-slate-600">{user?.email}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right hidden md:block">
                <div className="text-xs text-slate-600 font-medium">
                  {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </div>
                <div className="text-xs text-slate-500">
                  {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
              <button
                onClick={logout}
                className="px-3 py-2 bg-white/80 border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-blue-200 hover:text-slate-900 transition"
                title="Logout from admin dashboard"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        {/* Mobile: grid buttons */}
        <div className="md:hidden grid grid-cols-2 gap-2 mb-4">

            {['requests', 'credit-requests', 'users', 'uploads', 'reviews', 'ai-usage', 'logs', 'login-logs'].map((tab) => (

            {['users', 'requests', 'uploads', 'reviews', 'ai-usage', 'logs', 'login-logs'].map((tab) => (

            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full px-3 py-3 text-base font-semibold rounded-xl border transition ${
                activeTab === tab
                  ? 'bg-blue-600 text-white shadow'
                  : 'bg-white text-slate-700 border-slate-200'
              }`}
            >

              {tab === 'requests' ? 'Premium Requests' : 
               tab === 'credit-requests' ? 'Credit Requests' :
               tab === 'ai-usage' ? 'AI Usage' : 

              {tab === 'ai-usage' ? 'AI Usage' : 

               tab === 'login-logs' ? 'Login Logs' : tab}
            </button>
          ))}
          <button
            onClick={refreshAll}
            disabled={loading}
            className="w-full px-3 py-3 text-sm font-semibold rounded-xl border bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            title="Refresh all data"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            Refresh
          </button>
        </div>

        {/* Desktop: pill tabs */}
        <div className="hidden md:flex w-full mb-6 justify-start px-2 items-center gap-2">
          <div className="pill-tabs shadow-sm min-w-max">

            {['requests', 'credit-requests', 'users', 'uploads', 'reviews', 'ai-usage', 'logs', 'login-logs'].map((tab) => (

            {['users', 'requests', 'uploads', 'reviews', 'ai-usage', 'logs', 'login-logs'].map((tab) => (

              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pill-tab capitalize text-base font-semibold ${activeTab === tab ? 'active' : ''}`}
              >
                {tab === 'ai-usage' ? 'AI Usage' : 
                 tab === 'login-logs' ? 'Login Logs' : tab}
              </button>
            ))}
          </div>
          <button
            onClick={refreshAll}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2 text-sm shadow-sm"
            title="Refresh all data (all sections)"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            Refresh
          </button>
        </div>

        {/* Tab Content */}
        <div className="glass-card hover-lift p-4 md:p-6 mt-4 w-full">

          {activeTab === 'requests' && (
            <div>
              <div className="mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Premium Requests</h2>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : premiumRequests.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No pending requests</div>
              ) : (
                <div className="space-y-4">
                  {premiumRequests.map((request) => (
                    <div
                      key={request.id}
                      className="border rounded-lg p-4 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold text-lg text-gray-900">{request.user_email}</p>
                        <p className="text-base text-gray-500 mt-1">
                          Requested: {new Date(request.requested_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprove(request.id)}
                          className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-base font-semibold shadow-sm hover:shadow transition-all"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReject(request.id)}
                          className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-base font-semibold shadow-sm hover:shadow transition-all"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'credit-requests' && (
            <div>
              <div className="mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Credit Requests</h2>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : creditRequests.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No credit requests</div>
              ) : (
                <div className="space-y-4">
                  {creditRequests.map((request) => (
                    <div
                      key={request.id}
                      className="border rounded-lg p-4"
                    >
                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div className="flex-1">
                          <p className="font-semibold text-lg text-gray-900">{request.user_email}</p>
                          <p className="text-base text-gray-500 mt-1">
                            Requested: {new Date(request.requested_at).toLocaleString()}
                          </p>
                          <p className="text-base text-gray-700 mt-2">
                            <span className="font-medium">Credits Requested:</span> {request.requested_credits}
                          </p>
                          {request.user_notes && (
                            <p className="text-sm text-gray-600 mt-2">
                              <span className="font-medium">Reason:</span> {request.user_notes}
                            </p>
                          )}
                          <p className="text-sm mt-2">
                            <span className={`px-2 py-1 rounded ${
                              request.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              request.status === 'approved' ? 'bg-green-100 text-green-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                            </span>
                          </p>
                          {request.reviewed_at && (
                            <p className="text-xs text-gray-500 mt-1">
                              Reviewed: {new Date(request.reviewed_at).toLocaleString()}
                            </p>
                          )}
                          {request.notes && (
                            <p className="text-sm text-gray-600 mt-2">
                              <span className="font-medium">Admin Notes:</span> {request.notes}
                            </p>
                          )}
                        </div>
                        {request.status === 'pending' && (
                          <div className="flex gap-2">
                            <button
                              onClick={async () => {
                                const notes = prompt('Enter approval notes (optional):')
                                // If user clicks Cancel, notes will be null, but we still want to approve
                                // If user clicks OK with empty string, we want to approve with no notes
                                // Only if user explicitly cancels should we not proceed
                                if (notes !== null) {
                                  await handleApproveCreditRequest(request.id, notes || '')
                                }
                              }}
                              className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-base font-semibold shadow-sm hover:shadow transition-all"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => {
                                const notes = prompt('Enter rejection reason (optional):')
                                if (notes !== null) {
                                  handleRejectCreditRequest(request.id, notes)
                                }
                              }}
                              className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-base font-semibold shadow-sm hover:shadow transition-all"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Users</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={usersFilterPeriod}
                    onChange={(e) => {
                      const val = e.target.value
                      setUsersFilterPeriod(val)
                      fetchUsers(val)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportUsers}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleDeleteUsers}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                          <input
                            type="checkbox"
                            checked={selectedUserIds.length > 0 && selectedUserIds.length === users.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedUserIds(users.map((u) => u.id))
                              } else {
                                setSelectedUserIds([])
                              }
                            }}
                          />
                        </th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Email</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Status</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Total Questions</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Questions Limit</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Remaining</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Daily Questions</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((u) => (
                        <tr key={u.id}>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                            <input
                              type="checkbox"
                              checked={selectedUserIds.includes(u.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedUserIds((prev) => [...prev, u.id])
                                } else {
                                  setSelectedUserIds((prev) => prev.filter((id) => id !== u.id))
                                }
                              }}
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{u.email}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1.5 rounded-full text-sm font-semibold ${
                              u.premium_status === 'approved' ? 'bg-green-100 text-green-800' : 
                              u.premium_status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {u.premium_status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-lg font-semibold text-gray-900">
                              {u.questions_used || 0}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-3">
                              <span className="text-lg font-semibold text-gray-900 min-w-[3rem] text-center">
                                {u.questions_limit || 700}
                              </span>
                              <div className="flex flex-col gap-1">
                                <button
                                  onClick={() => handleQuotaAdjust(u.id, (u.questions_limit || 700) + 10, null)}
                                  className="w-8 h-8 flex items-center justify-center bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 shadow-md hover:shadow-lg transition-all duration-200 active:scale-95"
                                  title="Increase questions limit by 10"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleQuotaAdjust(u.id, Math.max(0, (u.questions_limit || 700) - 10), null)}
                                  className="w-8 h-8 flex items-center justify-center bg-gradient-to-br from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all duration-200 active:scale-95"
                                  title="Decrease questions limit by 10"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M20 12H4" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-lg font-semibold text-gray-900">
                              {Math.max(0, (u.questions_limit || 700) - (u.questions_used || 0))}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span className="text-base font-semibold text-gray-900">
                                  {u.daily_questions_used || 0} / {u.daily_questions_limit || 50}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-600">
                                  Remaining: {u.daily_questions_remaining || 0}
                                </span>
                                <button
                                  onClick={async () => {
                                    if (window.confirm(`Reset daily question count for ${u.email}?`)) {
                                      try {
                                        await api.resetDailyQuestions(u.id)
                                        toast.success('Daily question count reset')
                                        fetchUsers()
                                      } catch (error) {
                                        toast.error(error.response?.data?.detail || 'Failed to reset daily questions')
                                      }
                                    }
                                  }}
                                  className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                                  title="Reset daily question limit"
                                >
                                  Reset
                                </button>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex gap-2">
                              {u.premium_status === 'approved' && (
                                <button
                                  onClick={async () => {
                                    if (window.confirm(`Are you sure you want to switch ${u.email} back to free account?`)) {
                                      try {
                                        await api.switchUserToFree(u.id)
                                        toast.success('User switched back to free account')
                                        fetchUsers()
                                      } catch (error) {
                                        toast.error(error.response?.data?.detail || 'Failed to switch user to free account')
                                      }
                                    }
                                  }}
                                  className="px-4 py-2 rounded-lg text-sm font-semibold bg-yellow-100 text-yellow-800 hover:bg-yellow-200 transition-colors shadow-sm hover:shadow"
                                  title="Switch user back to free account"
                                >
                                  Back to Free
                                </button>
                              )}
                              {u.premium_status !== 'approved' && (
                                <button
                                  onClick={async () => {
                                    if (window.confirm(`Are you sure you want to upgrade ${u.email} to premium account?`)) {
                                      try {
                                        await api.switchUserToPremium(u.id)
                                        toast.success('User upgraded to premium account')
                                        fetchUsers()
                                      } catch (error) {
                                        toast.error(error.response?.data?.detail || 'Failed to upgrade user to premium account')
                                      }
                                    }
                                  }}
                                  className="px-4 py-2 rounded-lg text-sm font-semibold bg-green-100 text-green-800 hover:bg-green-200 transition-colors shadow-sm hover:shadow"
                                  title="Upgrade user to premium account"
                                >
                                  Free to Premium
                                </button>
                              )}
                          <button
                            onClick={async () => {
                              if (window.confirm(`Delete user ${u.email}? This cannot be undone.`)) {
                                try {
                                  await api.deleteUser(u.id)
                                  toast.success('User deleted')
                                  fetchUsers()
                                  fetchPremiumRequests()
                                } catch (error) {
                                  toast.error(error.response?.data?.detail || 'Failed to delete user')
                                }
                              }
                            }}
                            className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-500 text-white hover:bg-red-600 transition-colors shadow-sm hover:shadow"
                            title="Delete user account"
                          >
                            Delete
                          </button>
                              <button
                                onClick={async () => {
                                  try {
                                    if (u.is_active) {
                                      await api.disableUser(u.id)
                                      toast.success('User disabled')
                                    } else {
                                      await api.enableUser(u.id)
                                      toast.success('User enabled')
                                    }
                                    fetchUsers()
                                  } catch (error) {
                                    toast.error('Failed to update user status')
                                  }
                                }}
                                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm hover:shadow ${
                                  u.is_active ? 'bg-red-100 text-red-800 hover:bg-red-200' : 'bg-green-100 text-green-800 hover:bg-green-200'
                                }`}
                                title={u.is_active ? 'Disable user account' : 'Enable user account'}
                              >
                                {u.is_active ? 'Disable' : 'Enable'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'requests' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">

                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">All Uploads</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={uploadsFilterPeriod}
                    onChange={(e) => {
                      const val = e.target.value
                      setUploadsFilterPeriod(val)
                      fetchUploads(val)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportUploads}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleDeleteUploads}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>

                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Premium Requests</h2>

              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : premiumRequests.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No pending premium requests
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>

                        <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                          <input
                            type="checkbox"
                            checked={selectedUploadIds.length > 0 && selectedUploadIds.length === uploads.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedUploadIds(uploads.map((u) => u.id))
                              } else {
                                setSelectedUploadIds([])
                              }
                            }}
                          />
                        </th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">User Email</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">File Name</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Type</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Size</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Pages</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Uploaded</th>

                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Email</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Requested At</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Status</th>

                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">

                      {uploads.length === 0 ? (
                        <tr>
                          <td colSpan="8" className="px-6 py-4 text-center text-gray-500">No uploads found</td>

                      {premiumRequests.map((req) => (
                        <tr key={req.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{req.user_email}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(req.requested_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1.5 rounded-full text-sm font-semibold ${
                              req.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              req.status === 'approved' ? 'bg-green-100 text-green-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {req.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex gap-2">
                              <button
                                onClick={async () => {
                                  const notes = window.prompt('Add notes (optional):')
                                  if (notes !== null) {
                                    try {
                                      await api.approvePremiumRequest(req.id, notes || '')
                                      toast.success('Premium request approved')
                                      fetchPremiumRequests()
                                      fetchUsers()
                                    } catch (error) {
                                      toast.error(error.response?.data?.detail || 'Failed to approve request')
                                    }
                                  }
                                }}
                                className="px-4 py-2 rounded-lg text-sm font-semibold bg-green-100 text-green-800 hover:bg-green-200 transition-colors shadow-sm hover:shadow"
                                title="Approve premium request (700 questions will be allocated)"
                              >
                                Approve
                              </button>
                              <button
                                onClick={async () => {
                                  if (window.confirm(`Reject premium request from ${req.user_email}?`)) {
                                    try {
                                      await api.rejectPremiumRequest(req.id)
                                      toast.success('Premium request rejected')
                                      fetchPremiumRequests()
                                      fetchUsers()
                                    } catch (error) {
                                      toast.error(error.response?.data?.detail || 'Failed to reject request')
                                    }
                                  }
                                }}
                                className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-100 text-red-800 hover:bg-red-200 transition-colors shadow-sm hover:shadow"
                                title="Reject premium request"
                              >
                                Reject
                              </button>
                            </div>
                          </td>

                        </tr>
                      ) : (
                        uploads.map((upload) => (
                          <tr key={upload.id}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                              <input
                                type="checkbox"
                                checked={selectedUploadIds.includes(upload.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedUploadIds((prev) => [...prev, upload.id])
                                  } else {
                                    setSelectedUploadIds((prev) => prev.filter((id) => id !== upload.id))
                                  }
                                }}
                              />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.user_email}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.file_name}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.file_type}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">
                              {(upload.file_size / 1024).toFixed(2)} KB
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.pages || '-'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">
                              {new Date(upload.created_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <button
                                onClick={() => handleViewUpload(upload.id)}
                                className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                              >
                                Preview
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'uploads' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">All Uploads</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={uploadsFilterPeriod}
                    onChange={(e) => {
                      const val = e.target.value
                      setUploadsFilterPeriod(val)
                      fetchUploads(val)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportUploads}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleDeleteUploads}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                          <input
                            type="checkbox"
                            checked={selectedUploadIds.length > 0 && selectedUploadIds.length === uploads.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedUploadIds(uploads.map((u) => u.id))
                              } else {
                                setSelectedUploadIds([])
                              }
                            }}
                          />
                        </th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">User Email</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">File Name</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Type</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Size</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Pages</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Uploaded</th>
                        <th className="px-6 py-4 text-left text-base font-semibold text-gray-700 uppercase tracking-wide">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {uploads.length === 0 ? (
                        <tr>
                          <td colSpan="8" className="px-6 py-4 text-center text-gray-500">No uploads found</td>
                        </tr>
                      ) : (
                        uploads.map((upload) => (
                          <tr key={upload.id}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                              <input
                                type="checkbox"
                                checked={selectedUploadIds.includes(upload.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedUploadIds((prev) => [...prev, upload.id])
                                  } else {
                                    setSelectedUploadIds((prev) => prev.filter((id) => id !== upload.id))
                                  }
                                }}
                              />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.user_email}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.file_name}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.file_type}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">
                              {(upload.file_size / 1024).toFixed(2)} KB
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">{upload.pages || '-'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-base font-medium text-gray-900">
                              {new Date(upload.created_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <button
                                onClick={() => handleViewUpload(upload.id)}
                                className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                              >
                                Preview
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'reviews' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">User Reviews</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={reviewsFilterPeriod}
                    onChange={(e) => {
                      const val = e.target.value
                      setReviewsFilterPeriod(val)
                      fetchReviews(val)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportReviews}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleDeleteReviews}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : reviews.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No reviews yet</div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-2">
                    <input
                      type="checkbox"
                      checked={selectedReviewIds.length > 0 && selectedReviewIds.length === reviews.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedReviewIds(reviews.map((r) => r.id))
                        } else {
                          setSelectedReviewIds([])
                        }
                      }}
                    />
                    <span className="text-sm text-gray-600">Select all</span>
                  </div>
                  {reviews.map((review) => (
                    <div
                      key={review.id}
                      className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow flex gap-3"
                    >
                      <div className="pt-1">
                        <input
                          type="checkbox"
                          checked={selectedReviewIds.includes(review.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedReviewIds((prev) => [...prev, review.id])
                            } else {
                              setSelectedReviewIds((prev) => prev.filter((id) => id !== review.id))
                            }
                          }}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="font-semibold text-lg text-gray-900">{review.user_email}</p>
                            <div className="flex items-center gap-1 mt-1">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <span key={star} className="text-xl">
                                  {star <= review.rating ? '⭐' : '☆'}
                                </span>
                              ))}
                              <span className="ml-2 text-base font-medium text-gray-600">({review.rating}/5)</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-base text-gray-500">
                              {new Date(review.created_at).toLocaleDateString()}
                            </span>
                            <button
                              onClick={async () => {
                                if (window.confirm('Are you sure you want to delete this review?')) {
                                  try {
                                    await api.deleteReview(review.id)
                                    toast.success('Review deleted successfully')
                                    fetchReviews(reviewsFilterPeriod)
                                  } catch (error) {
                                    toast.error(error.response?.data?.detail || 'Failed to delete review')
                                  }
                                }
                              }}
                              className="px-4 py-2 text-base font-semibold bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors shadow-sm"
                              title="Delete review"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        {review.message && (
                          <p className="text-base text-gray-700 mt-2">{review.message}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'ai-usage' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">AI Usage Tracker</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={aiUsageFilterPeriod}
                    onChange={(e) => {
                      const val = e.target.value
                      setAiUsageFilterPeriod(val)
                      fetchAIUsageLogs(val)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportAIUsage}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleDeleteAIUsage}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              {/* Usage Statistics */}
              {aiUsageStats && (
                <div className="mb-6 space-y-4">
                  {/* Threshold Alert */}
                  {aiUsageStats.is_threshold_reached && (
                    <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">⚠️</span>
                        <div>
                          <p className="font-bold text-red-800">AI API Usage Threshold Reached!</p>
                          <p className="text-sm text-red-700">
                            Current: {aiUsageStats.current_month_tokens.toLocaleString()} / {aiUsageStats.threshold.toLocaleString()} tokens ({aiUsageStats.threshold_percentage.toFixed(1)}%)
                          </p>
                          <p className="text-sm text-red-600 mt-1">
                            Please recharge your OpenAI API key soon to avoid service interruption.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {!aiUsageStats.is_threshold_reached && aiUsageStats.threshold_percentage >= 80 && (
                    <div className="bg-yellow-50 border-2 border-yellow-500 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">⚠️</span>
                        <div>
                          <p className="font-bold text-yellow-800">AI Usage Warning</p>
                          <p className="text-sm text-yellow-700">
                            {aiUsageStats.threshold_percentage.toFixed(1)}% of threshold used. Please recharge soon.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Current Month Usage */}
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                      <h3 className="text-sm font-medium text-gray-600 mb-1">
                        {aiUsageFilterPeriod === 'all' ? 'Current Month' : `Period (${aiUsageFilterPeriod})`}
                      </h3>
                      <p className="text-2xl font-bold text-gray-900">
                        {(aiUsageFilterPeriod === 'all'
                          ? aiUsageStats.current_month_tokens
                          : filteredAIUsageTotals.totalTokens
                        ).toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">tokens</p>
                      <p className="text-xs text-gray-700 mt-1">
                        {aiUsageFilterPeriod === 'all'
                          ? `Cost: $${aiUsageStats.current_month_cost.toFixed(4)}`

                          : 'Cost: N/A (filtered)'}

                          : `Cost: $${filteredAIUsageTotals.cost.toFixed(4)}`}

                      </p>
                    </div>

                    {/* Total Usage */}
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                      <h3 className="text-sm font-medium text-gray-600 mb-1">All Time</h3>
                      <p className="text-2xl font-bold text-gray-900">
                        {(aiUsageFilterPeriod === 'all'
                          ? aiUsageStats.total_tokens
                          : filteredAIUsageTotals.totalTokens
                        ).toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">tokens</p>
                      <p className="text-xs text-gray-700 mt-1">
                        {aiUsageFilterPeriod === 'all'
                          ? `Cost: $${aiUsageStats.total_cost.toFixed(4)}`

                          : 'Cost: N/A (filtered)'}

                          : `Cost: $${filteredAIUsageTotals.cost.toFixed(4)}`}

                      </p>
                    </div>

                    {/* Threshold Progress */}
                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                      <h3 className="text-sm font-medium text-gray-600 mb-1">Threshold</h3>
                      <p className="text-2xl font-bold text-gray-900">
                        {aiUsageStats.threshold_percentage.toFixed(1)}%
                      </p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            aiUsageStats.is_threshold_reached
                              ? 'bg-red-600'
                              : aiUsageStats.threshold_percentage >= 80
                              ? 'bg-yellow-600'
                              : 'bg-green-600'
                          }`}
                          style={{
                            width: `${Math.min(aiUsageStats.threshold_percentage, 100)}%`
                          }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        {aiUsageStats.current_month_tokens.toLocaleString()} / {aiUsageStats.threshold.toLocaleString()}
                      </p>
                    </div>

                    {/* Usage Count */}
                    <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-4 border border-indigo-200">
                      <h3 className="text-sm font-medium text-gray-600 mb-1">Total Requests</h3>
                      <p className="text-2xl font-bold text-gray-900">
                        {(aiUsageFilterPeriod === 'all'
                          ? aiUsageStats.usage_count
                          : filteredAIUsageTotals.count
                        ).toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">API calls</p>
                    </div>
                  </div>

                  {/* Token Breakdown */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <h3 className="font-semibold text-gray-800 mb-3">
                      Token Breakdown ({aiUsageFilterPeriod === 'all' ? 'Current Month' : aiUsageFilterPeriod})
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Prompt Tokens</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {(aiUsageFilterPeriod === 'all'
                            ? aiUsageStats.prompt_tokens
                            : filteredAIUsageTotals.promptTokens
                          ).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Completion Tokens</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {(aiUsageFilterPeriod === 'all'
                            ? aiUsageStats.completion_tokens
                            : filteredAIUsageTotals.completionTokens
                          ).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Daily/Monthly/Yearly Cost Breakdown */}
                  {aiUsageStats && (aiUsageStats.daily_usage || aiUsageStats.monthly_usage) && (
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Daily Cost (Last 7 days) */}
                      {aiUsageStats.daily_usage && aiUsageStats.daily_usage.length > 0 && (
                        <div className="bg-white rounded-lg p-4 border border-gray-200">
                          <h3 className="font-semibold text-gray-800 mb-3">Daily Cost (Last 7 Days)</h3>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {aiUsageStats.daily_usage.slice(-7).reverse().map((day, idx) => (
                              <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                <span className="text-sm text-gray-700">
                                  {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                </span>
                                <div className="flex items-center gap-4">
                                  <span className="text-sm text-gray-600">{day.tokens?.toLocaleString() || 0} tokens</span>
                                  <span className="text-sm font-semibold text-gray-900">${(day.cost || 0).toFixed(4)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Monthly Cost (Last 6 months) */}
                      {aiUsageStats.monthly_usage && aiUsageStats.monthly_usage.length > 0 && (
                        <div className="bg-white rounded-lg p-4 border border-gray-200">
                          <h3 className="font-semibold text-gray-800 mb-3">Monthly Cost (Last 6 Months)</h3>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {aiUsageStats.monthly_usage.slice(-6).reverse().map((month, idx) => (
                              <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                <span className="text-sm text-gray-700">
                                  {new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                                </span>
                                <div className="flex items-center gap-4">
                                  <span className="text-sm text-gray-600">{month.tokens?.toLocaleString() || 0} tokens</span>
                                  <span className="text-sm font-semibold text-gray-900">${(month.cost || 0).toFixed(4)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Usage Logs Table */}
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-800">Recent AI Usage Logs</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            <input
                              type="checkbox"
                              checked={selectedAIUsageIds.length > 0 && selectedAIUsageIds.length === aiUsageLogs.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedAIUsageIds(aiUsageLogs.map((l) => l.id))
                                } else {
                                  setSelectedAIUsageIds([])
                                }
                              }}
                            />
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prompt</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Completion</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {aiUsageLogs.length === 0 ? (
                          <tr>
                            <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                              No AI usage logs yet
                            </td>
                          </tr>
                        ) : (
                          aiUsageLogs.map((log) => (
                            <tr key={log.id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                <input
                                  type="checkbox"
                                  checked={selectedAIUsageIds.includes(log.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedAIUsageIds((prev) => [...prev, log.id])
                                    } else {
                                      setSelectedAIUsageIds((prev) => prev.filter((id) => id !== log.id))
                                    }
                                  }}
                                />
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {new Date(log.created_at).toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {log.user_email || 'System'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {log.model}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {log.prompt_tokens.toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {log.completion_tokens.toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                {log.total_tokens.toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {log.estimated_cost || 'N/A'}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Usage Logs</h2>
                <div className="flex items-center gap-2">
                  <select
                    value={usageFilterPeriod}
                    onChange={(e) => {
                      const value = e.target.value
                      setUsageFilterPeriod(value)
                      fetchUsageLogs(value)
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="all">All</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                  <button
                    onClick={handleExportUsageLogs}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={async () => {
                      if (selectedUsageLogIds.length === 0) {
                        toast.error('Select at least one log to delete')
                        return
                      }
                      const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected log(s)? This cannot be undone.'
                      if (!window.confirm(warnExport)) return
                      if (!window.confirm(`Confirm delete ${selectedUsageLogIds.length} selected log(s)?`)) return
                      try {
                        await api.deleteUsageLogs(selectedUsageLogIds)
                        toast.success('Selected usage logs deleted')
                        fetchUsageLogs(usageFilterPeriod)
                      } catch (error) {
                        toast.error(error.response?.data?.detail || 'Failed to delete logs')
                      }
                    }}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          <input
                            type="checkbox"
                            checked={selectedUsageLogIds.length > 0 && selectedUsageLogIds.length === usageLogs.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedUsageLogIds(usageLogs.map((log) => log.id))
                              } else {
                                setSelectedUsageLogIds([])
                              }
                            }}
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pages</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {usageLogs.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                            No usage logs yet
                          </td>
                        </tr>
                      ) : (
                        usageLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                              <input
                                type="checkbox"
                                checked={selectedUsageLogIds.includes(log.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedUsageLogIds((prev) => [...prev, log.id])
                                  } else {
                                    setSelectedUsageLogIds((prev) => prev.filter((id) => id !== log.id))
                                  }
                                }}
                              />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {log.user_email || `User ID: ${log.user_id}`}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {log.action}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {log.pages || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {log.file_size ? `${(log.file_size / 1024).toFixed(2)} KB` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {new Date(log.created_at).toLocaleString()}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'login-logs' && (
            <div>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-2">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Login Logs</h2>
                <div className="flex items-center gap-2">
          <select
            value={loginFilterPeriod}
            onChange={(e) => {
              const value = e.target.value
              setLoginFilterPeriod(value)
              fetchLoginLogs(value)
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="all">All</option>
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
                  <button
            onClick={handleExportLoginLogs}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Export CSV
                  </button>
          <button
            onClick={async () => {
              if (selectedLoginLogIds.length === 0) {
                toast.error('Select at least one log to delete')
                return
              }
              const warnExport = 'Please export CSV first if you need a backup. Proceed to delete the selected log(s)? This cannot be undone.'
              if (!window.confirm(warnExport)) return
              if (!window.confirm(`Confirm delete ${selectedLoginLogIds.length} selected log(s)?`)) return
              try {
                await api.deleteLoginLogs(selectedLoginLogIds)
                toast.success('Selected login logs deleted')
                fetchLoginLogs(loginFilterPeriod)
              } catch (error) {
                toast.error(error.response?.data?.detail || 'Failed to delete logs')
              }
            }}
            className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
          >
            Delete
          </button>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Track user login activity with device types and session times
              </p>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          <input
                            type="checkbox"
                            checked={selectedLoginLogIds.length > 0 && selectedLoginLogIds.length === loginLogs.length}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedLoginLogIds(loginLogs.map((log) => log.id))
                              } else {
                                setSelectedLoginLogIds([])
                              }
                            }}
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User Agent</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Login Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Logout Time</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loginLogs.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                            No login logs yet
                          </td>
                        </tr>
                      ) : (
                        loginLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                              <input
                                type="checkbox"
                                checked={selectedLoginLogIds.includes(log.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedLoginLogIds((prev) => [...prev, log.id])
                                  } else {
                                    setSelectedLoginLogIds((prev) => prev.filter((id) => id !== log.id))
                                  }
                                }}
                              />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {log.user_email}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                log.device_type === 'mobile' ? 'bg-blue-100 text-blue-800' :
                                log.device_type === 'desktop' ? 'bg-green-100 text-green-800' :
                                log.device_type === 'tablet' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {log.device_type ? log.device_type.charAt(0).toUpperCase() + log.device_type.slice(1) : 'Unknown'}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate" title={log.user_agent || ''}>
                              {log.user_agent ? (log.user_agent.length > 50 ? log.user_agent.substring(0, 50) + '...' : log.user_agent) : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {new Date(log.login_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {log.logout_at ? (
                                <span className="text-gray-900">{new Date(log.logout_at).toLocaleString()}</span>
                              ) : (
                                <span className="text-gray-400 italic">Still logged in</span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'logs-old' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Usage Logs</h2>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pages</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {usageLogs.map((log) => (
                        <tr key={log.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {log.user_email || `User ID: ${log.user_id}`}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{log.action}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{log.pages || '-'}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {log.file_size ? `${(log.file_size / 1024).toFixed(2)} KB` : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {new Date(log.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2025 StudyQnA — Created by GUGAN
          </p>
        </div>
      </footer>
    </div>
  )
}

export default AdminDashboard

