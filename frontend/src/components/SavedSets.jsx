import { useState, useEffect, useMemo, useRef } from 'react'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import axios from 'axios'

const SavedSets = ({ isPremium }) => {
  const [sets, setSets] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSet, setSelectedSet] = useState(null)
  const [expandedDates, setExpandedDates] = useState(new Set())
  const [downloading, setDownloading] = useState(false)
  const [downloadAbortController, setDownloadAbortController] = useState(null)
  const [downloadToastId, setDownloadToastId] = useState(null)
  const viewRefs = useRef({})

  useEffect(() => {
    fetchSets()
  }, [])

  const fetchSets = async () => {
    setLoading(true)
    try {
      const response = await api.listQnASets()
      setSets(response.data)
      // Keep all date groups collapsed by default (empty Set)
      setExpandedDates(new Set())
    } catch (error) {
      toast.error('Failed to load saved sets')
    } finally {
      setLoading(false)
    }
  }

  // Group sets by date (descending)
  const groupedSets = useMemo(() => {
    const groups = {}
    sets.forEach((s) => {
      const dateKey = s.created_at ? new Date(s.created_at).toDateString() : 'Unknown Date'
      if (!groups[dateKey]) groups[dateKey] = []
      groups[dateKey].push(s)
    })
    // Sort dates descending
    const sorted = Object.entries(groups).sort((a, b) => {
      return new Date(b[0]).getTime() - new Date(a[0]).getTime()
    })
    // Sort sets within each date by created_at desc
    sorted.forEach(([, list]) => {
      list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    })
    return sorted
  }, [sets])

  const toggleDateExpansion = (dateKey) => {
    setExpandedDates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(dateKey)) {
        newSet.delete(dateKey)
      } else {
        newSet.add(dateKey)
      }
      return newSet
    })
  }

  // Cancel download handler
  const cancelDownload = () => {
    if (downloadAbortController) {
      downloadAbortController.abort()
      setDownloadAbortController(null)
    }
    if (downloadToastId) {
      toast.dismiss(downloadToastId)
      setDownloadToastId(null)
    }
    setDownloading(false)
    toast.error('❌ Download cancelled', { duration: 2000 })
  }

  const downloadSet = async (setId, format, outputFormat) => {
    // Prevent multiple simultaneous downloads
    if (downloading) {
      toast.error('⏳ A download is already in progress. Please wait...', { duration: 2000 })
      return
    }

    if (!isPremium) {
      toast.error('Premium access required for downloads')
      return
    }

    // Create AbortController for cancellation
    const abortController = new AbortController()
    setDownloadAbortController(abortController)

    // Set downloading state to prevent multiple clicks
    setDownloading(true)

    // Show preparing message with cancel button
    const preparingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>📄 Preparing download... Please wait</span>
          <button
            onClick={() => {
              toast.dismiss(t.id)
              cancelDownload()
            }}
            className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      ),
      {
        duration: Infinity,
        id: 'download-toast'
      }
    )
    setDownloadToastId(preparingToast)
    
    try {
      // Update to generating message with cancel button
      toast.dismiss(preparingToast)
      const generatingToast = toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>⚙️ Generating PDF... This may take a moment</span>
            <button
              onClick={() => {
                toast.dismiss(t.id)
                cancelDownload()
              }}
              className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        ),
        {
          duration: Infinity,
          id: 'download-toast'
        }
      )
      setDownloadToastId(generatingToast)
      
      const response = await axios.get(`/api/qna/sets/${setId}/download`, {
        params: { format, output_format: outputFormat },
        responseType: 'blob',
        signal: abortController.signal
      })
      
      // Check if cancelled before proceeding
      if (abortController.signal.aborted) {
        return
      }
      
      toast.dismiss(generatingToast)
      
      // Show finalizing message
      const finalizingToast = toast.loading('📥 Finalizing download...', {
        duration: 2000
      })
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `questions_set_${setId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.dismiss(finalizingToast)
      toast.success('✅ Download started!', { duration: 3000 })
    } catch (error) {
      if (axios.isCancel(error)) {
        // Download was cancelled - already handled in cancelDownload
        return
      }
      toast.dismiss()
      toast.error('Download failed: ' + (error.response?.data?.detail || 'Unknown error'))
    } finally {
      // Always reset downloading state and cleanup
      setDownloading(false)
      setDownloadAbortController(null)
      setDownloadToastId(null)
    }
  }

  const deleteSet = async (setId) => {
    const confirmed = window.confirm('Delete this Q/A set? This cannot be undone.')
    if (!confirmed) return

    try {
      await api.deleteQnASet(setId)
      setSets(prev => prev.filter(s => s.id !== setId))
      if (selectedSet === setId) {
        setSelectedSet(null)
      }
      toast.success('Set deleted')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete set')
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div>
      <h2 className="text-lg md:text-xl font-semibold mb-4 md:mb-6">My Generated Sets</h2>
      
      {groupedSets.length > 0 ? (
        <div className="space-y-4">
          {groupedSets.map(([dateKey, setsForDate]) => {
            const isExpanded = expandedDates.has(dateKey)
            const dateLabel = new Date(dateKey).toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })
            return (
              <div key={dateKey} className="border border-gray-200 rounded-lg bg-white shadow-sm">
                <button 
                  className="flex items-center justify-between w-full p-4 text-lg font-semibold text-gray-800 hover:bg-gray-50 transition-colors rounded-t-lg"
                  onClick={() => toggleDateExpansion(dateKey)}
                >
                  <span>{dateLabel} ({setsForDate.length} set{setsForDate.length > 1 ? 's' : ''})</span>
                  <svg 
                    className={`w-5 h-5 text-gray-500 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"></path>
                  </svg>
                </button>
                {isExpanded && (
                  <div className="space-y-4 p-4 border-t border-gray-200">
                    {setsForDate.map((set) => (
                      <div
                        key={set.id}
                        className="border rounded-lg p-4 hover:bg-gray-50 transition-colors bg-white"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-semibold">Set #{set.id}</h3>
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>Difficulty: {set.settings_json.difficulty}</p>
                              <p>Type: {set.settings_json.qna_type}</p>
                              <p>Questions: {set.qna_json?.questions?.length || 0}</p>
                            </div>
                          </div>
                          
                          <div className="flex flex-col gap-2">
                            <button
                              onClick={() => {
                                const newSelected = selectedSet === set.id ? null : set.id
                                setSelectedSet(newSelected)
                                
                                // If viewing, ensure date group is expanded and scroll to content
                                if (newSelected) {
                                  // Expand the date group if not already expanded
                                  if (!expandedDates.has(dateKey)) {
                                    setExpandedDates(prev => {
                                      const newSet = new Set(prev)
                                      newSet.add(dateKey)
                                      return newSet
                                    })
                                  }
                                  
                                  // Scroll to the view content after a brief delay to allow expansion
                                  setTimeout(() => {
                                    const viewElement = viewRefs.current[set.id]
                                    if (viewElement) {
                                      viewElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                                    }
                                  }, 100)
                                }
                              }}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                            >
                              {selectedSet === set.id ? 'Hide' : 'View'}
                            </button>
                            
                            {isPremium && (
                              <div className="flex flex-col gap-1">
                                <button
                                  onClick={() => downloadSet(set.id, 'pdf', 'questions_only')}
                                  disabled={downloading}
                                  className="px-3 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {downloading ? '...' : 'Q Only'}
                                </button>
                                <button
                                  onClick={() => downloadSet(set.id, 'pdf', 'questions_answers')}
                                  disabled={downloading}
                                  className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {downloading ? '...' : 'Q+A'}
                                </button>
                                <button
                                  onClick={() => downloadSet(set.id, 'pdf', 'answers_only')}
                                  disabled={downloading}
                                  className="px-3 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {downloading ? '...' : 'Answers'}
                                </button>
                              </div>
                            )}
                            
                            <button
                              onClick={() => deleteSet(set.id)}
                              disabled={downloading}
                              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Delete
                            </button>
                          </div>
                        </div>

                        {selectedSet === set.id && (
                          <div 
                            ref={el => viewRefs.current[set.id] = el}
                            className="mt-4 pt-4 border-t"
                          >
                            <div className="space-y-3">
                              {set.qna_json?.questions?.slice(0, isPremium ? undefined : 3).map((q, idx) => (
                                <div key={idx} className="bg-white border-2 border-gray-300 rounded-lg p-4 shadow-sm mb-3">
                                  <div className="flex items-start gap-3">
                                    <span className="font-bold text-blue-600">Q{idx + 1}.</span>
                                    <div className="flex-1">
                                      <p className="font-medium mb-3 text-gray-900">{q.question}</p>
                                      {q.type === 'mcq' && q.options && (
                                        <div className="mt-2 space-y-2">
                                          {q.options.map((opt, i) => {
                                            const optionLabel = String.fromCharCode(65 + i) // A, B, C, D
                                            return (
                                              <div 
                                                key={i} 
                                                className="flex items-start gap-3 p-2 border border-gray-200 rounded-md bg-gray-50"
                                              >
                                                <span className="font-bold text-blue-600 min-w-[24px]">{optionLabel}.</span>
                                                <span className="text-gray-700 flex-1">{opt}</span>
                                              </div>
                                            )
                                          })}
                                        </div>
                                      )}
                                      {q.marks && (
                                        <div className="mt-2">
                                          <span className="inline-block px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                                            {q.marks} mark{q.marks !== 1 ? 's' : ''}
                                          </span>
                                        </div>
                                      )}
                                      {isPremium && (
                                        <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                                          <p className="text-sm font-semibold text-green-800 mb-1">✓ Answer:</p>
                                          <p className="text-green-700">
                                            {q.correct_answer || q.answer || 'Answer not available'}
                                          </p>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                              {!isPremium && set.qna_json?.questions?.length > 3 && (
                                <p className="text-sm text-yellow-600 text-center">
                                  Upgrade to see all questions and answers
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">No saved Q/A sets yet</p>
          <p className="text-sm text-gray-400 mt-2">Generate some Q/A to see them here</p>
        </div>
      )}
    </div>
  )
}

export default SavedSets

