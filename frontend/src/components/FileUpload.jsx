import { useState, useRef, useEffect } from 'react'
import { isMobileDevice } from '../utils/deviceDetection'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import { getRotatingMessages } from '../utils/rotatingLoader'

const FileUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const fileInputRef = useRef(null)

  // Detect mobile on mount and window resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(isMobileDevice())
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleFile = async (file) => {
    if (!file) return

    // Validate file type - Only PDFs are supported
    const isPDF = file.type === 'application/pdf' || file.name.endsWith('.pdf')

    if (!isPDF) {
      toast.error('Only PDF files are allowed')
      return
    }

    // Validate file size (client-side check)
    // PDFs can be up to 100MB for book splitting feature (will be split if >6MB)
    const MAX_PDF_SIZE = 100 * 1024 * 1024  // 100MB (for book splitting)
    const maxSize = MAX_PDF_SIZE
    const maxSizeMB = 100

    if (file.size > maxSize) {
      toast.error(`File size exceeds ${maxSizeMB}MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('subject', 'general')  // Default to general, will be auto-detected

    // Get rotating messages for upload
    const uploadMessages = getRotatingMessages('uploading')
    let uploadMessageIndex = 0
    const uploadToastId = 'upload-toast'

    // Show processing message with rotation
    const processingToast = toast.loading(uploadMessages[uploadMessageIndex], {
      duration: Infinity,
      id: uploadToastId
    })
    
    // Start rotating messages every 20 seconds
    const uploadRotateInterval = setInterval(() => {
      uploadMessageIndex = (uploadMessageIndex + 1) % uploadMessages.length
      toast.loading(uploadMessages[uploadMessageIndex], {
        id: uploadToastId,
        duration: Infinity
      })
    }, 20000)

    try {
      const response = await api.uploadFile(formData)
      
      // Clear upload rotation
      clearInterval(uploadRotateInterval)
      
      // Update toast to show processing with new rotating messages
      toast.dismiss(processingToast)
      const processingMessages = getRotatingMessages('processing')
      let processingMessageIndex = 0
      const processingToastId = 'processing-toast'
      
      const processingToast2 = toast.loading(processingMessages[processingMessageIndex], {
        duration: Infinity,
        id: processingToastId
      })
      
      // Start rotating processing messages
      const processingRotateInterval = setInterval(() => {
        processingMessageIndex = (processingMessageIndex + 1) % processingMessages.length
        toast.loading(processingMessages[processingMessageIndex], {
          id: processingToastId,
          duration: Infinity
        })
      }, 20000)
      
      // Wait a bit to show processing state
      await new Promise(resolve => setTimeout(resolve, 500))
      
      clearInterval(processingRotateInterval)
      toast.dismiss(processingToast2)
      
      // Check for subject mismatch warning
      if (response.data.subject_mismatch_warning) {
        toast(
          `⚠️ ${response.data.subject_mismatch_warning}${response.data.detected_subject ? ` Detected: ${response.data.detected_subject}` : ''}`,
          {
            duration: isMobile ? 8000 : 6000, // Longer on mobile for readability
            icon: '⚠️',
            style: {
              maxWidth: isMobile ? '95%' : '500px',
              wordBreak: 'break-word',
              fontSize: isMobile ? '14px' : '13px',
              padding: isMobile ? '16px' : '12px',
              backgroundColor: '#fef3c7',
              color: '#92400e',
              border: '2px solid #f59e0b',
            },
            position: isMobile ? 'top-center' : 'top-right'
          }
        )
      }
      
      // Success - navigate to generate page
      toast.success('✅ File uploaded and processed successfully!', {
        duration: 3000
      })
      
      // Call success handler (navigates to generate tab)
      if (onUploadSuccess) {
        onUploadSuccess(response.data)
        
        // On mobile, scroll to top to show the generate tab
        if (isMobile) {
          setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }, 100)
        }
      }
    } catch (error) {
      // Clear any intervals on error
      if (window.uploadRotateInterval) {
        clearInterval(window.uploadRotateInterval)
        window.uploadRotateInterval = null
      }
      if (window.processingRotateInterval) {
        clearInterval(window.processingRotateInterval)
        window.processingRotateInterval = null
      }
      
      console.error('Upload error:', error)
      console.error('Error response:', error.response)
      console.error('Error data:', error.response?.data)
      
      // Dismiss any loading toasts
      toast.dismiss()
      
      // Extract error message from response
      let errorMessage = 'Upload failed. Please try again.'
      
      if (error.response) {
        // Backend returned an error
        errorMessage = error.response.data?.detail || 
                      error.response.data?.message ||
                      error.response.statusText ||
                      `Upload failed (${error.response.status})`
      } else if (error.message) {
        // Network or other error
        errorMessage = error.message
      }
      
      console.error('Displaying error:', errorMessage)
      
      // Show error prominently on mobile
      toast.error(errorMessage, {
        duration: isMobile ? 8000 : 5000, // Longer on mobile
        style: {
          maxWidth: isMobile ? '95%' : '500px',
          wordBreak: 'break-word',
          fontSize: isMobile ? '14px' : '13px',
          padding: isMobile ? '16px' : '12px',
          backgroundColor: '#fee2e2',
          color: '#991b1b',
          border: '2px solid #fca5a5'
        },
        position: isMobile ? 'top-center' : 'top-right'
      })
    } finally {
      setUploading(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }


  return (
    <div className="space-y-4">
      {/* File Upload Area (Desktop - Hide drag & drop on mobile) */}
      <div
        data-tour="file-upload"
        onDragEnter={!isMobile ? handleDrag : undefined}
        onDragLeave={!isMobile ? handleDrag : undefined}
        onDragOver={!isMobile ? handleDrag : undefined}
        onDrop={!isMobile ? handleDrop : undefined}
        className={`border-2 border-dashed rounded-lg p-4 md:p-8 text-center transition-colors ${
          dragActive && !isMobile
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="hidden"
          disabled={uploading}
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <svg
              className="w-12 h-12 md:w-16 md:h-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          
          <div>
            <p className="text-base md:text-lg font-medium text-gray-700">
              {uploading ? 'Uploading...' : isMobile ? 'Select a file to upload' : 'Drag & drop your file here'}
            </p>
            <p className="text-xs md:text-sm text-gray-500 mt-2">
              {isMobile ? 'Choose PDF file from your device' : 'or click to browse'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              PDF only (max 100MB for books, 40 pages)
            </p>
          </div>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full md:w-auto bg-blue-600 text-white px-6 py-3 md:py-2 rounded-lg font-semibold active:bg-blue-700 hover:bg-blue-700 transition-colors disabled:opacity-50 text-base md:text-sm relative group"
            title={uploading ? 'Uploading file... Please wait' : 'Click to select a PDF file'}
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
            ) : (
              <span>{isMobile ? '📁 Choose File' : 'Select File'}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default FileUpload

