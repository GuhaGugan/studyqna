import { useState, useEffect, useRef, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import FileUpload from '../components/FileUpload'
import QnAGenerator from '../components/QnAGenerator'
import SavedSets from '../components/SavedSets'
import PremiumBanner from '../components/PremiumBanner'
import PremiumWelcome from '../components/PremiumWelcome'
import ReviewForm from '../components/ReviewForm'
import ProfileTab from '../components/ProfileTab'
import PdfSplitParts from '../components/PdfSplitParts'
import OnboardingTour from '../components/OnboardingTour'
import HelpTooltip from '../components/HelpTooltip'

const Dashboard = () => {
  const { user, logout, isPremium, fetchUser } = useAuth()
  const [uploads, setUploads] = useState([])
  const [selectedUpload, setSelectedUpload] = useState(null)
  const [activeTab, setActiveTab] = useState('upload') // 'upload', 'generate', 'saved', 'review'
  const [loading, setLoading] = useState(false)
  const [showPremiumWelcome, setShowPremiumWelcome] = useState(false)
  const [previousPremiumStatus, setPreviousPremiumStatus] = useState(isPremium)
  const [hasShownWelcome, setHasShownWelcome] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [expandedDates, setExpandedDates] = useState(new Set())
  const [showLargePdfModal, setShowLargePdfModal] = useState(false)
  const [largePdfName, setLargePdfName] = useState('')
  const [profileData, setProfileData] = useState(null)

  useEffect(() => {
    fetchUploads()
    fetchProfileData()
  }, [])

  const fetchProfileData = async () => {
    try {
      const response = await api.getUserProfile()
      setProfileData(response.data)
    } catch (error) {
      console.error('Failed to fetch profile data:', error)
    }
  }
  
  // Check for premium activation (only show once when user FIRST becomes premium)
  useEffect(() => {
    if (!user) return
    
    // Check if welcome has already been shown (persists across sessions)
    const welcomeShown = localStorage.getItem(`premiumWelcomeShown_${user.id}`)
    
    // Only show if:
    // 1. User is currently premium
    // 2. User was NOT premium before (just became premium)
    // 3. Welcome hasn't been shown yet
    if (isPremium && !previousPremiumStatus && !welcomeShown && !hasShownWelcome) {
      // User just became premium - show welcome
      console.log('🎉 User just became premium!')
      setShowPremiumWelcome(true)
      setHasShownWelcome(true)
      localStorage.setItem(`premiumWelcomeShown_${user.id}`, 'true')
    }
    
    // Update previous status for next comparison
    setPreviousPremiumStatus(isPremium)
  }, [isPremium, previousPremiumStatus, hasShownWelcome, user])

  // Listen for premium activation event (from AuthContext)
  useEffect(() => {
    if (!user) return
    
    const handlePremiumActivated = () => {
      console.log('🎉 Premium activation event received!')
      const welcomeShown = localStorage.getItem(`premiumWelcomeShown_${user.id}`)
      
      // Only show if welcome hasn't been shown yet
      if (!welcomeShown && !hasShownWelcome) {
        setShowPremiumWelcome(true)
        setHasShownWelcome(true)
        localStorage.setItem(`premiumWelcomeShown_${user.id}`, 'true')
      }
    }
    
    window.addEventListener('premiumActivated', handlePremiumActivated)
    return () => {
      window.removeEventListener('premiumActivated', handlePremiumActivated)
    }
  }, [hasShownWelcome, user])
  
  // Poll for premium status changes (in case admin approves while user is on page)
  useEffect(() => {
    if (isPremium || hasShownWelcome || !user) return // Don't poll if already premium, shown, or no user
    
    const interval = setInterval(async () => {
      try {
        const response = await api.getCurrentUser()
        const currentUser = response.data
        const currentIsPremium = currentUser?.premium_status === 'approved' && 
                                 currentUser?.premium_valid_until && 
                                 new Date(currentUser.premium_valid_until) > new Date()
        
        if (currentIsPremium && !hasShownWelcome) {
          console.log('🎉 Premium status detected via polling!')
          setShowPremiumWelcome(true)
          setHasShownWelcome(true)
          sessionStorage.setItem(`premiumWelcomeShown_${currentUser.id}`, 'true')
        }
      } catch (error) {
        console.error('Error checking premium status:', error)
      }
    }, 5000) // Check every 5 seconds
    
    return () => clearInterval(interval)
  }, [isPremium, hasShownWelcome, user])

  const fetchUploads = async () => {
    setLoading(true)
    try {
      const response = await api.listUploads()
      setUploads(response.data)
      // Keep all date groups collapsed by default (empty Set)
      setExpandedDates(new Set())
    } catch (error) {
      console.error('Failed to fetch uploads:', error)
    } finally {
      setLoading(false)
    }
  }

  // Group uploads by date (descending)
  const groupedUploads = useMemo(() => {
    const groups = {}
    uploads.forEach((u) => {
      const dateKey = u.created_at ? new Date(u.created_at).toDateString() : 'Unknown Date'
      if (!groups[dateKey]) groups[dateKey] = []
      groups[dateKey].push(u)
    })
    // Sort dates descending
    const sorted = Object.entries(groups).sort((a, b) => {
      return new Date(b[0]).getTime() - new Date(a[0]).getTime()
    })
    // Sort uploads within each date by created_at desc
    sorted.forEach(([, list]) => {
      list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    })
    return sorted
  }, [uploads])

  const refreshAll = async () => {
    setLoading(true)
    try {
      // Refresh uploads
      await fetchUploads()
      
      // Refresh saved sets and profile (trigger re-fetch via key change)
      setRefreshTrigger(prev => prev + 1)
      
      // Refresh user data from AuthContext
      if (fetchUser) {
        await fetchUser()
      }
      
      // Refresh profile data to update question counts
      await fetchProfileData()
      
      toast.success('✅ All data refreshed!', { duration: 2000 })
    } catch (error) {
      toast.error('Some data failed to refresh')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = (upload) => {
    console.log('Upload success handler called with:', upload)
    
    // Update uploads list
    setUploads(prev => {
      // Check if upload already exists to avoid duplicates
      const exists = prev.find(u => u.id === upload.id)
      return exists ? prev : [upload, ...prev]
    })
    
    // Set as selected upload
    setSelectedUpload(upload)
    
    // If large PDF (>6MB), prompt to split and stay on Upload tab
    if (upload.file_type === 'pdf' && upload.file_size > 6 * 1024 * 1024) {
      toast.success('📚 Large PDF uploaded! Scrolling to split option...', {
        duration: 3000
      })
      setActiveTab('upload')
      setLargePdfName(upload.file_name || 'PDF')
      setShowLargePdfModal(true)
      
      // Expand the date section and scroll to the split PDF component
      setTimeout(() => {
        // Expand the date section for the uploaded file
        // Find which date group this upload belongs to
        const uploadDate = upload.created_at ? new Date(upload.created_at).toDateString() : new Date().toDateString()
        setExpandedDates(prev => new Set([...prev, uploadDate]))
        
        // Scroll to the split PDF component for this upload
        const splitComponentId = `split-pdf-${upload.id}`
        setTimeout(() => {
          const splitElement = document.getElementById(splitComponentId)
          if (splitElement) {
            splitElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            // Highlight the component briefly
            splitElement.style.transition = 'box-shadow 0.3s ease'
            splitElement.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.5)'
            setTimeout(() => {
              splitElement.style.boxShadow = ''
            }, 2000)
          } else {
            // Fallback: scroll to uploads section
            const uploadSection = document.getElementById('upload-section')
            if (uploadSection) {
              uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }
          }
        }, 300)
      }, 100)
    } else {
      // Small PDFs (<=6MB) go directly to Generate tab
      setActiveTab('generate')
      // Scroll to top on mobile to show the generate tab
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }, 100)
    }
    
    console.log('Navigated to generate tab, selected upload:', upload.id)
  }

  const handleDeleteUpload = async (id) => {
    try {
      await api.deleteUpload(id)
      setUploads(uploads.filter(u => u.id !== id))
      if (selectedUpload?.id === id) {
        setSelectedUpload(null)
      }
      toast.success('File deleted')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Mobile Responsive */}
      <header className="bg-white/90 backdrop-blur border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 md:py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-slate-900 truncate">StudyQnA Generator</h1>
              <p className="text-sm text-slate-600 truncate">{user?.email}</p>
            </div>
            <div className="flex items-center justify-between md:justify-end gap-3 md:gap-4">
              {!isPremium && (
                <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-sm font-semibold">
                  Free Plan
                </span>
              )}
              {isPremium && (
                <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-sm font-semibold">
                  Premium Active
                </span>
              )}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    // Clear tour completion to restart
                    if (user) {
                      localStorage.removeItem(`tour_done_${user.id}`)
                    }
                    // Trigger tour restart via custom event
                    window.dispatchEvent(new Event('start-tour'))
                  }}
                  className="px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition flex items-center gap-2"
                  title="Start guided tour"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="hidden sm:inline">Tour</span>
                </button>
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
                  title="Logout from your account"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Premium Banner */}
      {!isPremium && <PremiumBanner />}

      {/* Main Content */}
      <main id="upload-section" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Mobile tabs: grid buttons */}
        <div className="md:hidden grid grid-cols-2 gap-2 mb-4">
          {[
            { key: 'upload', label: '📤 Upload' },
            { key: 'generate', label: '⚡ Generate' },
            { key: 'saved', label: '💾 Saved' },
            { key: 'review', label: '⭐ Review' },
            { key: 'profile', label: '👤 Profile' },
          ].map((tab) => (
            <button
              key={tab.key}
              data-tour={`${tab.key}-tab`}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full px-3 py-3 text-sm font-semibold rounded-xl border transition ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white shadow'
                  : 'bg-white text-slate-700 border-slate-200'
              }`}
            >
              {tab.label}
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

        {/* Desktop tabs: pill style */}
        <div className="hidden md:flex w-full mb-6 justify-start px-2 items-center gap-2">
          <div className="pill-tabs shadow-sm min-w-max">
            {[
              { key: 'upload', label: '📤 Upload' },
              { key: 'generate', label: '⚡ Generate' },
              { key: 'saved', label: '💾 Saved' },
              { key: 'review', label: '⭐ Review' },
              { key: 'profile', label: '👤 Profile' },
            ].map((tab) => (
              <button
                key={tab.key}
                data-tour={`${tab.key}-tab`}
                onClick={() => setActiveTab(tab.key)}
                className={`pill-tab ${activeTab === tab.key ? 'active' : ''}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <button
            data-tour="refresh-button"
            onClick={refreshAll}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2 text-sm shadow-sm"
            title="Refresh all data (uploads, saved sets, profile)"
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
        <div className="glass-card hover-lift p-4 md:p-6 w-full">
          {activeTab === 'upload' && (
            <div>
              <h2 className="text-lg md:text-xl font-semibold mb-4 md:mb-6">Upload PDF</h2>
              
              {/* Quota Display Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6" data-tour="quota-cards">
                {/* Total Questions Card */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-800">Total Questions</h3>
                    <span className="text-sm font-medium text-gray-600">
                      {profileData?.usage_stats?.questions?.remaining ?? 
                        (profileData?.usage_stats?.questions?.limit 
                          ? (profileData?.usage_stats?.questions?.limit - (profileData?.usage_stats?.questions?.used || 0))
                          : (isPremium ? 700 : 10))} remaining
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all"
                      style={{
                        width: `${(() => {
                          const limit = profileData?.usage_stats?.questions?.limit || (isPremium ? 700 : 10)
                          const used = profileData?.usage_stats?.questions?.used || 0
                          return Math.min((used / limit) * 100, 100)
                        })()}%`
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-600">
                    {profileData?.usage_stats?.questions?.limit 
                      ? `${profileData?.usage_stats?.questions?.used || 0} / ${profileData?.usage_stats?.questions?.limit} questions`
                      : (isPremium 
                          ? `${profileData?.usage_stats?.questions?.used || 0} / 700 questions` 
                          : `${profileData?.usage_stats?.questions?.used || 0} / 10 questions`)}
                  </p>
                </div>

                {/* Daily Questions Card */}
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-800">Daily Questions</h3>
                    <span className="text-sm font-medium text-gray-600">
                      {profileData?.usage_stats?.daily_questions?.remaining ?? 
                        (profileData?.usage_stats?.daily_questions?.limit 
                          ? (profileData?.usage_stats?.daily_questions?.limit - (profileData?.usage_stats?.daily_questions?.used || 0))
                          : (isPremium ? 50 : 10))} remaining
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        profileData?.usage_stats?.daily_questions?.used >= ((profileData?.usage_stats?.daily_questions?.limit || (isPremium ? 50 : 10)) * 0.8)
                          ? profileData?.usage_stats?.daily_questions?.used >= (profileData?.usage_stats?.daily_questions?.limit || (isPremium ? 50 : 10))
                            ? 'bg-red-600'
                            : 'bg-yellow-600'
                          : 'bg-green-600'
                      }`}
                      style={{
                        width: `${(() => {
                          const limit = profileData?.usage_stats?.daily_questions?.limit || (isPremium ? 50 : 10)
                          const used = profileData?.usage_stats?.daily_questions?.used || 0
                          return Math.min((used / limit) * 100, 100)
                        })()}%`
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-600">
                    {profileData?.usage_stats?.daily_questions?.limit 
                      ? `${profileData?.usage_stats?.daily_questions?.used || 0} / ${profileData?.usage_stats?.daily_questions?.limit} per day`
                      : (isPremium 
                          ? `${profileData?.usage_stats?.daily_questions?.used || 0} / 50 per day` 
                          : `${profileData?.usage_stats?.daily_questions?.used || 0} / 10 per day`)}
                  </p>
                  {profileData?.usage_stats?.generations?.reset_time && (
                    <p className="text-xs text-gray-500 mt-1">
                      Resets: {new Date(profileData.usage_stats.generations.reset_time).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>

              <FileUpload onUploadSuccess={handleUploadSuccess} />
              
              {groupedUploads.length > 0 && (
                <div className="mt-8">
                  <h3 className="text-lg font-medium mb-4">Your Uploads</h3>
                  <div className="space-y-4">
                    {groupedUploads.map(([dateKey, items]) => {
                      const isExpanded = expandedDates.has(dateKey)
                      const dateLabel = new Date(dateKey).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })
                      return (
                        <div key={dateKey} className="border rounded-lg bg-white/70">
                          <button
                            onClick={() => {
                              setExpandedDates(prev => {
                                const next = new Set(prev)
                                if (next.has(dateKey)) next.delete(dateKey)
                                else next.add(dateKey)
                                return next
                              })
                            }}
                            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 rounded-t-lg"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-gray-800">{dateLabel}</span>
                              <span className="text-xs text-gray-500">({items.length} upload{items.length > 1 ? 's' : ''})</span>
                            </div>
                            <span className="text-sm text-gray-500">{isExpanded ? '▲' : '▼'}</span>
                          </button>
                          {isExpanded && (
                            <div className="space-y-4 px-4 pb-4">
                              {items.map((upload) => (
                                <div key={upload.id} className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
                                  {/* Show split parts component for large PDFs */}
                                  {upload.file_type === 'pdf' && upload.file_size > 6 * 1024 * 1024 && (
                                    <div id={`split-pdf-${upload.id}`} className="mb-4">
                                      <PdfSplitParts 
                                        uploadId={upload.id} 
                                        onPartSelected={(partUpload) => {
                                          // When a part is selected, treat it as a new upload
                                          setUploads(prev => {
                                            const exists = prev.find(u => u.id === partUpload.id)
                                            return exists ? prev : [partUpload, ...prev]
                                          })
                                          setSelectedUpload(partUpload)
                                          setActiveTab('generate')
                                          toast.success('✅ Part ready for question generation!')
                                        }}
                                        onMultiSelect={(partIds) => {
                                          setSelectedUpload({ ...upload, selectedPartIds: partIds })
                                          setActiveTab('generate')
                                          toast.success(`✅ ${partIds.length} parts selected! Ready to generate.`)
                                        }}
                                      />
                                    </div>
                                  )}
                                  
                                  <div className="flex-1">
                                    <p className="font-medium text-gray-900 mb-2">{upload.file_name}</p>
                                    <p className="text-sm text-gray-500 mb-3">
                                      {upload.file_type} • {(upload.file_size / 1024 / 1024).toFixed(2)} MB
                                      {upload.pages && ` • ${upload.pages} pages`}
                                      {upload.subject && upload.subject !== 'general' && (
                                        <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs font-semibold capitalize">
                                          {upload.subject.replace('_', ' ')}
                                        </span>
                                      )}
                                      {upload.is_split && (
                                        <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                                          Split
                                        </span>
                                      )}
                                    </p>
                                  </div>
                                  <div className="flex gap-2">
                                    {!(upload.file_type === 'pdf' && upload.file_size > 6 * 1024 * 1024) ? (
                                      <button
                                        onClick={() => {
                                          setSelectedUpload(upload)
                                          setActiveTab('generate')
                                        }}
                                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors"
                                      >
                                        Use
                                      </button>
                                    ) : (
                                      <div className="flex-1 px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg border border-gray-200 text-center">
                                        Split first to generate
                                      </div>
                                    )}
                                    <button
                                      onClick={() => handleDeleteUpload(upload.id)}
                                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm transition-colors"
                                    >
                                      Delete
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'generate' && (
            <QnAGenerator
              uploads={uploads}
              selectedUpload={selectedUpload}
              onSelectUpload={setSelectedUpload}
              isPremium={isPremium}
              onGenerationComplete={fetchProfileData}
            />
          )}

          {activeTab === 'saved' && (
            <SavedSets key={refreshTrigger} isPremium={isPremium} />
          )}

          {activeTab === 'review' && (
            <ReviewForm onSubmitted={() => setActiveTab('upload')} />
          )}

          {activeTab === 'profile' && (
            <ProfileTab key={refreshTrigger} />
          )}
        </div>
      </main>

      {/* Premium Welcome Animation */}
      {showPremiumWelcome && (
        <PremiumWelcome 
          onClose={() => {
            setShowPremiumWelcome(false)
            if (user) {
              // Mark as shown in localStorage (persists across sessions)
              localStorage.setItem(`premiumWelcomeShown_${user.id}`, 'true')
            }
          }} 
        />
      )}

      {/* Large PDF Modal */}
      {showLargePdfModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 my-auto max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Large PDF Detected</h3>
              <button
                onClick={() => setShowLargePdfModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1"
                aria-label="Close"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-sm text-gray-700">
                <span className="font-semibold text-gray-900">{largePdfName}</span> is larger than 6MB.
              </p>
              <p className="text-sm text-gray-700">
                Please use <span className="font-semibold">"Split PDF into Parts"</span> in the Upload tab to improve upload, OCR, and question generation performance.
              </p>
              <ul className="text-sm text-gray-700 list-disc list-inside space-y-2">
                <li>We'll split the PDF into ~6MB parts (fewer, larger parts).</li>
                <li>Select any part(s) to generate up to 15 questions.</li>
                <li>After splitting, pick parts and go to Generate to create questions.</li>
              </ul>
            </div>
            <div className="flex flex-col sm:flex-row justify-end gap-2 mt-6 pt-4 border-t border-gray-200">
              <button
                onClick={() => setShowLargePdfModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowLargePdfModal(false)
                  setActiveTab('upload')
                  setTimeout(() => {
                    const target = document.getElementById('upload-section')
                    if (target) {
                      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    } else {
                      window.scrollTo({ top: 0, behavior: 'smooth' })
                    }
                  }, 100)
                }}
                className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Go to Upload & Split
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2025 StudyQnA — Created by GUGAN
          </p>
        </div>
      </footer>

      {/* Onboarding Tour */}
      <OnboardingTour activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  )
}

export default Dashboard

