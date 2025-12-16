import { useState, useRef, useEffect } from 'react'
import { isMobileDevice, hasCameraSupport } from '../utils/deviceDetection'
import { api } from '../utils/api'
import toast from 'react-hot-toast'

const FileUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState('general')
  const fileInputRef = useRef(null)
  const cameraInputRef = useRef(null)

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

    // Validate file type
    const isPDF = file.type === 'application/pdf' || file.name.endsWith('.pdf')
    const isImage = file.type.startsWith('image/') || 
                   ['.jpg', '.jpeg', '.png', '.gif', '.bmp'].some(ext => 
                     file.name.toLowerCase().endsWith(ext))

    if (!isPDF && !isImage) {
      toast.error('Only PDF and image files are allowed')
      return
    }

    // Show helpful message for images (only on web, not mobile to avoid clutter)
    if (isImage && !isMobile) {
      toast.info('📚 Only study materials allowed: textbook pages, diagrams, charts, or clean text. Human photos, IDs, and inappropriate content are blocked.', {
        duration: 4000
      })
    }

    // Validate file size (client-side check)
    // PDFs can be up to 100MB for book splitting feature (will be split if >6MB)
    // Images remain at 10MB
    const MAX_PDF_SIZE = 100 * 1024 * 1024  // 100MB (for book splitting)
    const MAX_IMAGE_SIZE = 10 * 1024 * 1024  // 10MB (increased for mobile photos)
    const maxSize = isPDF ? MAX_PDF_SIZE : MAX_IMAGE_SIZE
    const maxSizeMB = isPDF ? 100 : 10

    if (file.size > maxSize) {
      toast.error(`File size exceeds ${maxSizeMB}MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('subject', selectedSubject)  // Add subject selection

    // Show processing message
    const processingToast = toast.loading('📤 Uploading file... Please wait', {
      duration: Infinity
    })

    try {
      const response = await api.uploadFile(formData)
      
      // Update toast to show processing
      toast.dismiss(processingToast)
      const processingToast2 = toast.loading('⏳ Processing file... This may take a moment', {
        duration: Infinity
      })
      
      // Wait a bit to show processing state
      await new Promise(resolve => setTimeout(resolve, 500))
      
      toast.dismiss(processingToast2)
      
      // Check for subject mismatch warning
      if (response.data.subject_mismatch_warning) {
        toast.warning(
          `⚠️ ${response.data.subject_mismatch_warning}${response.data.detected_subject ? ` Detected: ${response.data.detected_subject}` : ''}`,
          {
            duration: isMobile ? 8000 : 6000, // Longer on mobile for readability
            style: {
              maxWidth: isMobile ? '95%' : '500px',
              wordBreak: 'break-word',
              fontSize: isMobile ? '14px' : '13px',
              padding: isMobile ? '16px' : '12px',
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

  const handleCameraCapture = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  return (
    <div className="space-y-4">
      {/* Subject Selection Dropdown */}
      <div className="mb-4 md:mb-6">
        <label 
          htmlFor="subject-select" 
          className={`block font-medium text-gray-700 mb-2 ${isMobile ? 'text-base' : 'text-sm'}`}
        >
          Select Subject
          {!isMobile && <span className="text-gray-500 text-xs ml-1">(for better Q/A generation)</span>}
        </label>
        <select
          id="subject-select"
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          disabled={uploading}
          className={`w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
            isMobile 
              ? 'px-4 py-3 text-base' // Larger touch target and text on mobile
              : 'px-4 py-2 text-sm'
          }`}
        >
          <option value="general">General</option>
          <option value="mathematics">Mathematics</option>
          <option value="english">English</option>
          <option value="tamil">Tamil</option>
          <option value="science">Science</option>
          <option value="social_science">Social Science</option>
        </select>
        <p className={`mt-2 text-gray-500 ${isMobile ? 'text-sm leading-relaxed' : 'text-xs'}`}>
          {selectedSubject === 'mathematics' && '✓ Will use exam-friendly notation and math-specific answer format'}
          {selectedSubject === 'english' && '✓ Will use literature-style answer format with Introduction, Explanation, Analysis, Conclusion'}
          {selectedSubject === 'tamil' && '✓ Will use Tamil literature format with அறிமுகம், விளக்கம், பகுப்பாய்வு, முடிவு (exam-style Tamil)'}
          {selectedSubject === 'science' && '✓ Will use science-specific answer format with Definition, Explanation, Example, Conclusion'}
          {selectedSubject === 'social_science' && '✓ Will use social science format with Background, Key Points, Explanation, Conclusion'}
          {selectedSubject === 'general' && 'Will auto-detect subject from content'}
        </p>
      </div>

      {/* Mobile Camera Button (Mobile Only - Hidden on Desktop) */}
      {isMobile && (
        <div className="block md:hidden">
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleCameraCapture}
            className="hidden"
            id="camera-input-mobile"
          />
          <button
            onClick={() => {
              if (cameraInputRef.current) {
                cameraInputRef.current.click()
              }
            }}
            disabled={uploading}
            type="button"
            className="w-full bg-green-600 text-white py-4 px-6 rounded-lg font-semibold active:bg-green-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-lg shadow-lg relative group"
            title={uploading ? 'Processing photo... Please wait' : 'Use your camera to capture study materials or documents'}
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                📷 Take Photo / Scan Document
              </>
            )}
          </button>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Use your camera to capture images or documents
          </p>
        </div>
      )}

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
          accept=".pdf,image/*"
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
              {isMobile ? 'Choose from gallery or files' : 'or click to browse'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              PDF (max 100MB for books, 40 pages) or Images (max 10MB)
            </p>
          </div>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full md:w-auto bg-blue-600 text-white px-6 py-3 md:py-2 rounded-lg font-semibold active:bg-blue-700 hover:bg-blue-700 transition-colors disabled:opacity-50 text-base md:text-sm relative group"
            title={uploading ? 'Uploading file... Please wait' : 'Click to select a PDF or image file'}
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

