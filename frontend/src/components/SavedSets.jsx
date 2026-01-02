import { useState, useEffect, useMemo, useRef } from 'react'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import axios from 'axios'
import { getRotatingMessages } from '../utils/rotatingLoader'

const SavedSets = ({ isPremium }) => {
  const [sets, setSets] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSet, setSelectedSet] = useState(null)
  const [expandedDates, setExpandedDates] = useState(new Set())
  const [downloading, setDownloading] = useState(false)
  const [downloadAbortController, setDownloadAbortController] = useState(null)
  const [downloadToastId, setDownloadToastId] = useState(null)
  const [downloadDropdownOpen, setDownloadDropdownOpen] = useState({}) // Track which dropdown is open
  const [editingSet, setEditingSet] = useState(null) // Track which set is being edited
  const [editedDataMap, setEditedDataMap] = useState({}) // Store edited data per set ID
  const viewRefs = useRef({})

  useEffect(() => {
    fetchSets()
  }, [])


  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.download-dropdown')) {
        setDownloadDropdownOpen({})
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
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
    // Clear rotating interval
    if (window.downloadRotateInterval) {
      clearInterval(window.downloadRotateInterval)
      window.downloadRotateInterval = null
    }
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

  const downloadSet = async (setId, format, outputFormat, editedData = null) => {
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

    const formatName = format.toUpperCase()
    // Show preparing message with cancel button
    const preparingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>📄 Preparing {formatName} download... Please wait</span>
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
            <span>⚙️ Generating {formatName}... This may take a moment</span>
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
      
      // Check if there's edited data for this set
      const editedDataForSet = editedDataMap[setId]
      let response
      if (editedDataForSet) {
        // Use POST endpoint with edited data
        response = await axios.post(
          `/api/qna/sets/${setId}/download?format=${format}&output_format=${outputFormat}`,
          { questions: editedDataForSet },
          {
            responseType: 'blob',
            signal: abortController.signal
          }
        )
      } else {
        // Use GET endpoint for original data
        response = await axios.get(`/api/qna/sets/${setId}/download`, {
          params: { format, output_format: outputFormat },
          responseType: 'blob',
          signal: abortController.signal
        })
      }
      
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

  // Helper function to convert answer object to string
  const formatAnswer = (answer) => {
    if (!answer) return ''
    if (typeof answer === 'string') return answer
    if (typeof answer === 'object') {
      // Handle structured answer objects
      const parts = []
      if (answer.background || answer.context) {
        parts.push(`Background/Context: ${answer.background || answer.context}`)
      }
      if (answer.key_points && Array.isArray(answer.key_points)) {
        parts.push(`Key Points:\n${answer.key_points.map((kp, i) => `${i + 1}. ${kp}`).join('\n')}`)
      } else if (answer.key_points) {
        parts.push(`Key Points: ${answer.key_points}`)
      }
      if (answer.explanation) {
        parts.push(`Explanation: ${answer.explanation}`)
      }
      if (answer.analysis) {
        parts.push(`Analysis: ${answer.analysis}`)
      }
      if (answer.introduction) {
        parts.push(`Introduction: ${answer.introduction}`)
      }
      if (answer.definition) {
        parts.push(`Definition: ${answer.definition}`)
      }
      if (answer.example) {
        parts.push(`Example: ${answer.example}`)
      }
      if (answer.given) {
        parts.push(`Given: ${answer.given}`)
      }
      if (answer.formula) {
        parts.push(`Formula: ${answer.formula}`)
      }
      if (answer.steps && Array.isArray(answer.steps)) {
        parts.push(`Steps:\n${answer.steps.map((step, i) => `Step ${i + 1}: ${step}`).join('\n')}`)
      } else if (answer.steps) {
        parts.push(`Steps: ${answer.steps}`)
      }
      if (answer.final || answer.final_answer) {
        parts.push(`Final Answer: ${answer.final || answer.final_answer}`)
      }
      if (answer.conclusion) {
        parts.push(`Conclusion: ${answer.conclusion}`)
      }
      return parts.length > 0 ? parts.join('\n\n') : JSON.stringify(answer, null, 2)
    }
    return String(answer)
  }

  const handleEdit = (setId) => {
    setEditingSet(setId)
    // If there's already edited data, it will be used automatically
  }

  const handleCancelEdit = (setId) => {
    setEditingSet(null)
  }

  const handleSaveEdit = (setId, questions) => {
    setEditedDataMap(prev => ({
      ...prev,
      [setId]: JSON.parse(JSON.stringify(questions))
    }))
    setEditingSet(null)
    toast.success('✅ Changes saved. Your edits will be included in downloads.')
  }

  const updateQuestion = (setId, questionIndex, field, value) => {
    const currentSet = sets.find(s => s.id === setId)
    if (!currentSet) return

    const existingEdited = editedDataMap[setId]
    const questions = existingEdited || JSON.parse(JSON.stringify(currentSet.qna_json.questions))
    
    const updated = [...questions]
    updated[questionIndex] = { ...updated[questionIndex], [field]: value }
    
    setEditedDataMap(prev => ({
      ...prev,
      [setId]: updated
    }))
  }

  const updateAnswer = (setId, questionIndex, value) => {
    const currentSet = sets.find(s => s.id === setId)
    if (!currentSet) return

    const existingEdited = editedDataMap[setId]
    const questions = existingEdited || JSON.parse(JSON.stringify(currentSet.qna_json.questions))
    
    const updated = [...questions]
    updated[questionIndex] = { ...updated[questionIndex], correct_answer: value }
    
    setEditedDataMap(prev => ({
      ...prev,
      [setId]: updated
    }))
  }

  const updateOption = (setId, questionIndex, optionIndex, value) => {
    const currentSet = sets.find(s => s.id === setId)
    if (!currentSet) return

    const existingEdited = editedDataMap[setId]
    const questions = existingEdited || JSON.parse(JSON.stringify(currentSet.qna_json.questions))
    
    const updated = [...questions]
    const newOptions = [...updated[questionIndex].options]
    newOptions[optionIndex] = value
    updated[questionIndex] = { ...updated[questionIndex], options: newOptions }
    
    setEditedDataMap(prev => ({
      ...prev,
      [setId]: updated
    }))
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
      if (editingSet === setId) {
        setEditingSet(null)
      }
      // Remove edited data for deleted set
      setEditedDataMap(prev => {
        const newMap = { ...prev }
        delete newMap[setId]
        return newMap
      })
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
                              <>
                                <button
                                  onClick={() => {
                                    handleEdit(set.id)
                                    // Also open view if not already open
                                    if (selectedSet !== set.id) {
                                      setSelectedSet(set.id)
                                    }
                                  }}
                                  className={`px-4 py-2 rounded-lg text-sm ${
                                    editingSet === set.id
                                      ? 'bg-green-600 text-white hover:bg-green-700'
                                      : editedDataMap[set.id]
                                      ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                                      : 'bg-yellow-600 text-white hover:bg-yellow-700'
                                  }`}
                                  title={editedDataMap[set.id] ? 'Edit saved changes' : 'Edit questions'}
                                >
                                  {editingSet === set.id ? 'Editing...' : editedDataMap[set.id] ? '✓ Edit' : 'Edit'}
                                </button>
                                
                                {/* Download Dropdown */}
                                <div className="relative download-dropdown">
                                  <button
                                    onClick={() => setDownloadDropdownOpen(prev => ({
                                      ...prev,
                                      [set.id]: !prev[set.id]
                                    }))}
                                    disabled={downloading}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 w-full"
                                  >
                                    <span>Download</span>
                                    <svg 
                                      className={`w-4 h-4 transition-transform ${downloadDropdownOpen[set.id] ? 'rotate-180' : ''}`}
                                      fill="none" 
                                      stroke="currentColor" 
                                      viewBox="0 0 24 24"
                                    >
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  </button>
                                  
                                  {downloadDropdownOpen[set.id] && (
                                    <div className="absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                                      <div className="py-1">
                                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 border-b">PDF</div>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'pdf', 'questions_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q Only
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'pdf', 'questions_answers')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q+A
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'pdf', 'answers_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Answers
                                        </button>
                                        
                                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 border-t border-b">DOCX</div>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'docx', 'questions_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q Only
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'docx', 'questions_answers')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q+A
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'docx', 'answers_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Answers
                                        </button>
                                        
                                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 border-t border-b">TXT</div>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'txt', 'questions_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q Only
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'txt', 'questions_answers')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Q+A
                                        </button>
                                        <button
                                          onClick={() => {
                                            downloadSet(set.id, 'txt', 'answers_only')
                                            setDownloadDropdownOpen(prev => ({ ...prev, [set.id]: false }))
                                          }}
                                          disabled={downloading}
                                          className="w-full text-left px-4 py-2 text-xs hover:bg-gray-100 disabled:opacity-50"
                                        >
                                          Answers
                                        </button>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </>
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
                            {editingSet === set.id ? (
                              // Edit Mode
                              <div className="space-y-3">
                                {(() => {
                                  const existingEdited = editedDataMap[set.id]
                                  const questionsToEdit = existingEdited || set.qna_json?.questions || []
                                  return questionsToEdit.slice(0, isPremium ? undefined : 3).map((q, idx) => (
                                    <div key={idx} className="bg-white border-2 border-gray-300 rounded-lg p-4 shadow-sm mb-3">
                                      <div className="flex items-start gap-3">
                                        <span className="font-bold text-blue-600">Q{idx + 1}.</span>
                                        <div className="flex-1">
                                          {/* Editable Question */}
                                          <textarea
                                            value={q.question || ''}
                                            onChange={(e) => updateQuestion(set.id, idx, 'question', e.target.value)}
                                            className="w-full px-3 py-2 mb-3 font-medium text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
                                            rows={3}
                                            placeholder="Enter question text..."
                                          />
                                          
                                          {/* Image Description Display (Edit Mode) */}
                                          {q.image_description && (
                                            <div className="mt-2 mb-3 p-2 md:p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                              <p className="text-xs md:text-sm font-semibold text-blue-800 mb-1">📊 Figure/Diagram:</p>
                                              <textarea
                                                value={q.image_description || ''}
                                                onChange={(e) => updateQuestion(set.id, idx, 'image_description', e.target.value)}
                                                className="w-full px-2 py-1 text-xs md:text-sm text-blue-700 italic bg-transparent border border-blue-300 rounded focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y"
                                                rows={2}
                                                placeholder="Enter image/figure description..."
                                              />
                                            </div>
                                          )}
                                          {/* Editable MCQ Options */}
                                          {q.type === 'mcq' && q.options && (
                                            <div className="mt-2 space-y-2 mb-3">
                                              {q.options.map((opt, i) => {
                                                const optionLabel = String.fromCharCode(97 + i) // a, b, c, d (lowercase)
                                                return (
                                                  <div 
                                                    key={i} 
                                                    className="flex items-start gap-3 p-2 border border-gray-200 rounded-md bg-gray-50"
                                                  >
                                                    <span className="font-bold text-blue-600 min-w-[24px]">{optionLabel})</span>
                                                    <input
                                                      type="text"
                                                      value={opt}
                                                      onChange={(e) => updateOption(set.id, idx, i, e.target.value)}
                                                      className="flex-1 text-gray-700 bg-transparent border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:outline-none break-words"
                                                      placeholder={`Option ${optionLabel}`}
                                                    />
                                                  </div>
                                                )
                                              })}
                                            </div>
                                          )}
                                          
                                          {/* Marks Badge */}
                                          {q.marks && (
                                            <div className="mt-2 mb-3">
                                              <span className="inline-block px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                                                {q.marks} mark{q.marks !== 1 ? 's' : ''}
                                              </span>
                                              {q.type && (
                                                <span className="ml-2 inline-block px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded">
                                                  Type: {q.type}
                                                </span>
                                              )}
                                            </div>
                                          )}
                                          
                                          {/* Editable Answer */}
                                          {isPremium && (
                                            <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                                              <p className="text-sm font-semibold text-green-800 mb-2">✓ Answer:</p>
                                              <textarea
                                                value={formatAnswer(q.correct_answer || q.answer)}
                                                onChange={(e) => updateAnswer(set.id, idx, e.target.value)}
                                                className="w-full px-3 py-2 text-green-700 bg-transparent border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-y whitespace-pre-wrap"
                                                rows={q.type === 'mcq' ? 3 : 8}
                                                placeholder="Enter answer text..."
                                              />
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  ))
                                })()}
                                
                                {/* Save/Cancel Buttons */}
                                <div className="flex items-center justify-end gap-3 mt-4 pt-4 border-t">
                                  <button
                                    onClick={() => handleCancelEdit(set.id)}
                                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm"
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={() => {
                                      const questionsToSave = editedDataMap[set.id] || set.qna_json?.questions || []
                                      handleSaveEdit(set.id, questionsToSave)
                                    }}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                                  >
                                    Save Changes
                                  </button>
                                </div>
                              </div>
                            ) : (
                              // View Mode
                              <div className="space-y-3">
                                {set.qna_json?.questions?.slice(0, isPremium ? undefined : 3).map((q, idx) => (
                                  <div key={idx} className="bg-white border-2 border-gray-300 rounded-lg p-4 shadow-sm mb-3">
                                    <div className="flex items-start gap-3">
                                      <span className="font-bold text-blue-600">Q{idx + 1}.</span>
                                      <div className="flex-1">
                                        <p className="font-medium mb-3 text-gray-900">{q.question}</p>
                                        {q.image_description && (
                                          <div className="mt-2 mb-3 p-2 md:p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                            <p className="text-xs md:text-sm font-semibold text-blue-800 mb-1">📊 Figure/Diagram:</p>
                                            <p className="text-xs md:text-sm text-blue-700 italic break-words">{q.image_description}</p>
                                          </div>
                                        )}
                                        {q.type === 'mcq' && q.options && (
                                          <div className="mt-2 space-y-2">
                                            {q.options.map((opt, i) => {
                                              const optionLabel = String.fromCharCode(97 + i) // a, b, c, d (lowercase)
                                              return (
                                                <div 
                                                  key={i} 
                                                  className="flex items-start gap-3 p-2 border border-gray-200 rounded-md bg-gray-50"
                                                >
                                                  <span className="font-bold text-blue-600 min-w-[24px]">{optionLabel})</span>
                                                  <span className="text-gray-700 flex-1 break-words">{opt}</span>
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
                                            <div className="text-green-700 whitespace-pre-wrap">
                                              {formatAnswer(q.correct_answer || q.answer) || 'Answer not available'}
                                            </div>
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
                            )}
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

