import toast from 'react-hot-toast'

/**
 * Utility function to start rotating toast messages every 30 seconds
 * with enhanced animations for long-running processes (>20 seconds)
 * @param {string} toastId - The toast ID to update
 * @param {Array} messages - Array of message functions or strings
 * @param {Function} cancelFn - Optional cancel function to pass to message renderers
 * @returns {Function} Cleanup function to stop rotation
 */
export const startRotatingToast = (toastId, messages, cancelFn = null) => {
  if (!toastId || !messages || messages.length === 0) {
    return () => {}
  }

  let messageIndex = 0
  let intervalId = null
  let animationIntervalId = null
  let startTime = Date.now()
  const ANIMATION_THRESHOLD = 20000 // 20 seconds

  // Function to update toast with animation
  const updateToast = (showAnimation = false) => {
    const currentMessage = messages[messageIndex]
    
    // Update the toast with new message
    if (typeof currentMessage === 'function') {
      // For function messages, wrap with animation if needed
      toast.loading(
        (t) => {
          const content = currentMessage(t, cancelFn)
          if (showAnimation) {
            return (
              <div className="flex items-center gap-3 animate-pulse-subtle">
                <div className="relative flex-shrink-0">
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin-fast"></div>
                  <div className="absolute inset-0 w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin-reverse opacity-50"></div>
                </div>
                <div className="flex-1">{content}</div>
              </div>
            )
          }
          return content
        },
        {
          id: toastId,
          duration: Infinity
        }
      )
    } else {
      // For string messages, wrap with animation if needed
      const content = showAnimation ? (
        <div className="flex items-center gap-3 animate-pulse-subtle">
          <div className="relative flex-shrink-0">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin-fast"></div>
            <div className="absolute inset-0 w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin-reverse opacity-50"></div>
          </div>
          <span className="flex-1">{currentMessage}</span>
        </div>
      ) : currentMessage
      
      toast.loading(content, {
        id: toastId,
        duration: Infinity
      })
    }
  }

  // Start rotating messages every 30 seconds
  intervalId = setInterval(() => {
    messageIndex = (messageIndex + 1) % messages.length
    const elapsed = Date.now() - startTime
    const showAnimation = elapsed >= ANIMATION_THRESHOLD
    updateToast(showAnimation)
  }, 30000) // 30 seconds

  // Start animation check every 5 seconds after 20 seconds
  animationIntervalId = setInterval(() => {
    const elapsed = Date.now() - startTime
    if (elapsed >= ANIMATION_THRESHOLD) {
      // Force update with animation
      updateToast(true)
    }
  }, 5000) // Check every 5 seconds

  // Return cleanup function
  return () => {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
    if (animationIntervalId) {
      clearInterval(animationIntervalId)
      animationIntervalId = null
    }
  }
}

/**
 * Enhanced toast loading with automatic animation after 20 seconds
 * @param {string|Function} content - Toast content
 * @param {Object} options - Toast options
 * @param {number} threshold - Time threshold in ms (default 20000)
 * @returns {Function} Cleanup function
 */
export const startAnimatedToast = (content, options = {}, threshold = 20000) => {
  const toastId = options.id || `animated-toast-${Date.now()}`
  const startTime = Date.now()
  let animationIntervalId = null
  let isAnimated = false

  // Initial toast
  const initialToast = toast.loading(content, {
    ...options,
    id: toastId,
    duration: Infinity
  })

  // Start checking for animation threshold
  animationIntervalId = setInterval(() => {
    const elapsed = Date.now() - startTime
    if (elapsed >= threshold && !isAnimated) {
      isAnimated = true
      
      // Update toast with animation
      const animatedContent = (
        <div className="flex items-center gap-3 animate-pulse-subtle">
          <div className="relative">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin-fast"></div>
            <div className="absolute inset-0 w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin-reverse opacity-50"></div>
          </div>
          <div className="flex-1">{typeof content === 'function' ? content(null) : content}</div>
        </div>
      )
      
      toast.loading(animatedContent, {
        ...options,
        id: toastId,
        duration: Infinity
      })
    }
  }, 5000) // Check every 5 seconds

  // Return cleanup function
  return () => {
    if (animationIntervalId) {
      clearInterval(animationIntervalId)
    }
    toast.dismiss(toastId)
  }
}

/**
 * Predefined message sets for different processes
 */
export const messageSets = {
  generating: [
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>⚡ Generating questions... This may take a moment</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>🔄 Still processing... Please be patient</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>⏳ Working on it... Almost there!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>✨ Creating quality questions... Hang tight!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    )
  ],
  generatingPdf: [
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>⚙️ Generating PDF... This may take a moment</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>📄 Still creating PDF... Please wait</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>🔄 Processing document... Almost ready!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>📚 Formatting your PDF... Just a bit more!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    )
  ],
  uploading: [
    '📤 Uploading file... Please wait',
    '⏳ Still uploading... Almost done!',
    '🔄 Processing upload... Hang on!',
    '📁 Transferring file... Just a moment!'
  ],
  processing: [
    '⏳ Processing file... This may take a moment',
    '🔄 Still processing... Please be patient',
    '⚙️ Working on it... Almost there!',
    '✨ Analyzing content... Just a bit more!'
  ],
  splitting: [
    '📚 Splitting PDF into parts... This may take a moment',
    '🔄 Still splitting... Please wait',
    '📄 Processing pages... Almost done!',
    '⚙️ Organizing parts... Just a moment!'
  ],
  preparing: [
    '📥 Preparing part for question generation...',
    '🔄 Setting up... Please wait',
    '⚙️ Getting ready... Almost there!',
    '✨ Preparing content... Just a moment!'
  ],
  preparingDownload: [
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>📄 Preparing download... Please wait</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>🔄 Still preparing... Please be patient</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>⏳ Getting ready... Almost there!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    ),
    (t, cancelFn) => (
      <div className="flex items-center gap-3">
        <span>📦 Organizing files... Just a moment!</span>
        <button
          onClick={() => {
            toast.dismiss(t.id)
            if (cancelFn) cancelFn()
          }}
          className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    )
  ]
}

// Add CSS animations to document head if not already added
if (typeof document !== 'undefined' && !document.getElementById('toast-animations-style')) {
  const style = document.createElement('style')
  style.id = 'toast-animations-style'
  style.textContent = `
    @keyframes spin-fast {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes spin-reverse {
      from { transform: rotate(360deg); }
      to { transform: rotate(0deg); }
    }
    @keyframes pulse-subtle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }
    .animate-spin-fast {
      animation: spin-fast 0.8s linear infinite;
    }
    .animate-spin-reverse {
      animation: spin-reverse 1.2s linear infinite;
    }
    .animate-pulse-subtle {
      animation: pulse-subtle 2s ease-in-out infinite;
    }
  `
  document.head.appendChild(style)
}
