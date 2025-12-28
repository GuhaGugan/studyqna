import toast from 'react-hot-toast'

/**
 * Create a rotating loading toast that changes messages every 20 seconds
 * @param {string} toastId - The toast ID from react-hot-toast
 * @param {Array<string>|Function} messages - Array of messages or function that returns JSX
 * @param {number} intervalMs - Interval in milliseconds (default: 20000 = 20 seconds)
 * @returns {Function} - Cleanup function to stop rotation
 */
export const createRotatingLoader = (toastId, messages, intervalMs = 20000) => {
  if (!toastId || !messages) return () => {}

  let currentIndex = 0
  const isFunction = typeof messages === 'function'
  const messageArray = isFunction ? null : messages
  const messageFunction = isFunction ? messages : null

  // Start rotating messages
  const intervalId = setInterval(() => {
    if (!toastId) return
    
    if (isFunction && messageFunction) {
      // For function-based messages (with cancel button), update the message part
      const newContent = messageFunction((currentIndex + 1) % 10) // Cycle through
      toast.loading(newContent, {
        id: toastId,
        duration: Infinity
      })
    } else if (messageArray && messageArray.length > 0) {
      currentIndex = (currentIndex + 1) % messageArray.length
      const newMessage = messageArray[currentIndex]
      toast.loading(newMessage, {
        id: toastId,
        duration: Infinity
      })
    }
  }, intervalMs)

  // Return cleanup function
  return () => {
    if (intervalId) {
      clearInterval(intervalId)
    }
  }
}

/**
 * Get rotating messages for different operation types
 */
export const getRotatingMessages = (operationType, context = {}) => {
  const baseMessages = {
    generating: [
      '🤖 AI is analyzing your content...',
      '⚡ Generating high-quality questions...',
      '📚 Processing educational material...',
      '🎯 Creating exam-style questions...',
      '✨ Refining question accuracy...',
      '🔍 Extracting key concepts...',
      '📝 Formatting questions and answers...',
      '🎓 Ensuring board-exam standards...'
    ],
    uploading: [
      '📤 Uploading your file...',
      '⏳ Processing file content...',
      '🔍 Validating file format...',
      '📄 Extracting text content...',
      '✅ Preparing file for processing...'
    ],
    downloading: [
      '📥 Preparing your download...',
      '⚙️ Generating document...',
      '📄 Formatting content...',
      '💾 Finalizing file...',
      '✨ Almost ready...'
    ],
    splitting: [
      '📚 Splitting PDF into parts...',
      '📄 Analyzing PDF structure...',
      '✂️ Creating optimized parts...',
      '📑 Organizing pages...',
      '✅ Preparing parts for selection...'
    ],
    processing: [
      '⏳ Processing your request...',
      '🔄 Working on it...',
      '⚡ Almost done...',
      '✨ Finalizing...'
    ]
  }

  // Add context-specific messages
  if (operationType === 'generating' && context.partCount) {
    return [
      `🤖 AI is creating questions from ${context.partCount} selected parts...`,
      `⚡ Generating questions from ${context.partCount} parts...`,
      `📚 Processing ${context.partCount} parts of content...`,
      `🎯 Creating questions from ${context.partCount} parts...`,
      `✨ Refining questions from ${context.partCount} parts...`,
      `🔍 Analyzing ${context.partCount} parts...`,
      `📝 Formatting questions from ${context.partCount} parts...`,
      `🎓 Ensuring quality from ${context.partCount} parts...`
    ]
  }

  return baseMessages[operationType] || baseMessages.processing
}

