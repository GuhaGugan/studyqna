import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import { getRotatingMessages } from '../utils/rotatingLoader'

const PdfSplitParts = ({ uploadId, onPartSelected, onMultiSelect }) => {
  const [parts, setParts] = useState([])
  const [loading, setLoading] = useState(false)
  const [splitting, setSplitting] = useState(false)
  const [renamingPartId, setRenamingPartId] = useState(null)
  const [newName, setNewName] = useState('')
  const [previewPartId, setPreviewPartId] = useState(null)
  const [selectedPartIds, setSelectedPartIds] = useState([])  // Multi-select state
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    if (uploadId) {
      checkSplitStatus()
    }
  }, [uploadId])

  const checkSplitStatus = async () => {
    try {
      const response = await api.getSplitParts(uploadId)
      if (response.data && response.data.length > 0) {
        setParts(response.data)
      }
    } catch (error) {
      // If no parts exist, that's okay - PDF might not be split yet
      if (error.response?.status !== 404) {
        console.error('Error checking split parts:', error)
      }
    }
  }

  const handleSplit = async () => {
    setSplitting(true)
    const splitMessages = getRotatingMessages('splitting')
    let splitMessageIndex = 0
    const splitToastId = 'split-toast'
    
    const splitToast = toast.loading(splitMessages[splitMessageIndex], {
      duration: Infinity,
      id: splitToastId
    })
    
    // Start rotating messages every 20 seconds
    const splitRotateInterval = setInterval(() => {
      splitMessageIndex = (splitMessageIndex + 1) % splitMessages.length
      toast.loading(splitMessages[splitMessageIndex], {
        id: splitToastId,
        duration: Infinity
      })
    }, 20000)

    try {
      const response = await api.splitPdf(uploadId, 6.0)
      clearInterval(splitRotateInterval)
      toast.dismiss(splitToast)
      
      if (response.data && response.data.parts) {
        setParts(response.data.parts)
        toast.success(
          `✅ PDF successfully split into ${response.data.total_parts} parts!`,
          { duration: 5000 }
        )
      }
    } catch (error) {
      if (window.splitRotateInterval) {
        clearInterval(window.splitRotateInterval)
        window.splitRotateInterval = null
      }
      toast.dismiss(splitToast)
      const errorMsg = error.response?.data?.detail || 'Failed to split PDF'
      toast.error(errorMsg, { duration: 5000 })
      console.error('Split error:', error)
    } finally {
      setSplitting(false)
    }
  }

  const handleRename = async (partId, currentName) => {
    if (!newName.trim()) {
      toast.error('Please enter a name')
      return
    }

    try {
      const response = await api.renameSplitPart(partId, newName.trim())
      setParts(parts.map(p => p.id === partId ? response.data : p))
      setRenamingPartId(null)
      setNewName('')
      toast.success('✅ Part renamed successfully')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to rename part'
      toast.error(errorMsg)
    }
  }

  const handlePreview = async (partId) => {
    if (previewPartId === partId) {
      setPreviewPartId(null)
      return
    }

    setPreviewPartId(partId)
    try {
      const response = await api.previewSplitPart(partId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (error) {
      toast.error('Failed to load preview')
      setPreviewPartId(null)
    }
  }

  const handleSelect = async (part) => {
    // Single select mode (existing functionality)
    const selectToast = toast.loading('📥 Preparing part for question generation...', {
      duration: Infinity
    })

    try {
      // Download the part as a regular upload
      const response = await api.downloadSplitPart(part.id)
      
      toast.dismiss(selectToast)
      toast.success('✅ Part ready for question generation!', { duration: 3000 })
      
      // Call the callback with the new upload ID
      if (onPartSelected) {
        onPartSelected(response.data)
      }
    } catch (error) {
      toast.dismiss(selectToast)
      const errorMsg = error.response?.data?.detail || 'Failed to prepare part'
      toast.error(errorMsg, { duration: 5000 })
    }
  }

  const handleToggleSelect = (partId) => {
    setSelectedPartIds(prev => {
      if (prev.includes(partId)) {
        return prev.filter(id => id !== partId)
      } else {
        return [...prev, partId]
      }
    })
  }

  const handleGenerateFromSelected = () => {
    if (selectedPartIds.length === 0) {
      toast.error('Please select at least one part')
      return
    }

    if (selectedPartIds.length > 10) {
      toast.error('Please select maximum 10 parts at a time')
      return
    }

    // Call the multi-select callback
    if (onMultiSelect) {
      onMultiSelect(selectedPartIds)
    }
  }

  if (parts.length === 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              📚 Large PDF Detected
            </h3>
            <p className="text-gray-700 mb-4">
              Your PDF is larger than 6MB. To improve upload, OCR, and question generation performance, 
              we can automatically split it into smaller parts (approximately 6MB each).
            </p>
            <button
              onClick={handleSplit}
              disabled={splitting}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {splitting ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Splitting...
                </span>
              ) : (
                'Split PDF into Parts'
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            ✅ PDF Split into {parts.length} Parts
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Your book was successfully split into smaller parts (approximately 6MB each) to improve upload, OCR, and question generation performance.
          </p>
          {selectedPartIds.length > 0 && (
            <p className="text-sm text-blue-600 mt-2 font-medium">
              {selectedPartIds.length} part{selectedPartIds.length > 1 ? 's' : ''} selected
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setExpanded(prev => !prev)}
            className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-200"
          >
            {expanded ? 'Hide Parts' : 'Show Parts'}
          </button>
          {selectedPartIds.length > 0 && (
            <button
              onClick={handleGenerateFromSelected}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <span>⚡ Generate from {selectedPartIds.length} Selected</span>
            </button>
          )}
        </div>
      </div>

      {expanded && (
      <div className="space-y-3">
        {parts.map((part) => (
          <div
            key={part.id}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                    Part {part.part_number}
                  </span>
                  <span className="text-sm text-gray-600">
                    Pages {part.start_page}–{part.end_page} ({part.total_pages} pages)
                  </span>
                  <span className="text-sm text-gray-500">
                    {(part.file_size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
                
                {renamingPartId === part.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder={part.custom_name || part.file_name}
                      className="flex-1 px-3 py-1 border border-gray-300 rounded text-sm"
                      autoFocus
                    />
                    <button
                      onClick={() => handleRename(part.id, part.custom_name || part.file_name)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setRenamingPartId(null)
                        setNewName('')
                      }}
                      className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-base font-medium text-gray-900">
                      {part.custom_name || part.file_name}
                    </span>
                    <button
                      onClick={() => {
                        setRenamingPartId(part.id)
                        setNewName(part.custom_name || part.file_name)
                      }}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                      title="Rename this part"
                    >
                      ✏️ Rename
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 ml-4">
                {/* Multi-select checkbox */}
                <input
                  type="checkbox"
                  checked={selectedPartIds.includes(part.id)}
                  onChange={() => handleToggleSelect(part.id)}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  title="Select for multi-part generation"
                />
                <button
                  onClick={() => handlePreview(part.id)}
                  className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                  title="Preview first 5 pages"
                >
                  {previewPartId === part.id ? 'Hide' : 'Preview'}
                </button>
                <button
                  onClick={() => handleSelect(part)}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                  title="Select this single part"
                >
                  ✅ Use Single
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}
    </div>
  )
}

export default PdfSplitParts

