import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

const OnboardingTour = ({ activeTab, setActiveTab }) => {
  const { user } = useAuth()

  const [currentStep, setCurrentStep] = useState(0)
  const [isActive, setIsActive] = useState(false)
  const [showWelcome, setShowWelcome] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)

  const highlightRef = useRef(null)
  const tooltipRef = useRef(null)
  const animationFrameRef = useRef(null)
  const resizeObserverRef = useRef(null)

  /* -----------------------------------
     COMPREHENSIVE TOUR STEPS
  ----------------------------------- */
  const tourSteps = [
    {
      title: 'Welcome to StudyQnA 🎓',
      content: 'Your intelligent study companion for generating exam-ready questions from study materials. Let\'s explore all the features!',
      target: null,
      position: 'center'
    },
    {
      title: '📤 Upload Tab',
      content: 'Start here! Upload your PDFs or images containing study material. Supported formats: PDF files and images (JPG, PNG). You can upload multiple files.',
      target: '[data-tour="upload-tab"]',
      action: () => setActiveTab('upload'),
      position: 'bottom'
    },
    {
      title: '📊 Usage Limits Dashboard',
      content: 'Monitor your question generation limits here. Total Questions: Your overall quota (700 for premium). Daily Questions: Maximum 50 questions per day. Both reset automatically.',
      target: '[data-tour="quota-cards"]',
      position: 'bottom'
    },
    {
      title: '📁 File Upload Area',
      content: 'Drag and drop files here or click to browse. On desktop, you can drag multiple files. Mobile users can select files from their device. Large PDFs can be split into manageable parts.',
      target: '[data-tour="file-upload"]',
      position: 'bottom'
    },
    {
      title: '⚡ Generate Tab',
      content: 'Create custom question sets from your uploaded materials. Configure difficulty, question types, marks, and output format. Premium users can generate up to 50 questions per day.',
      target: '[data-tour="generate-tab"]',
      action: () => setActiveTab('generate'),
      position: 'bottom'
    },
    {
      title: '💾 Saved Sets Tab',
      content: 'Access all your previously generated question sets here. View, edit, download in multiple formats (PDF, DOCX, TXT), or delete sets you no longer need.',
      target: '[data-tour="saved-tab"]',
      action: () => setActiveTab('saved'),
      position: 'bottom'
    },
    {
      title: '⭐ Review Tab',
      content: 'Share your feedback and help us improve! Rate your experience and leave comments. Your input helps us enhance the platform for everyone.',
      target: '[data-tour="review-tab"]',
      action: () => setActiveTab('review'),
      position: 'bottom'
    },
    {
      title: '👤 Profile Tab',
      content: 'Manage your account settings, view detailed usage statistics, check premium status, and see your subscription details. Track your question generation history here.',
      target: '[data-tour="profile-tab"]',
      action: () => setActiveTab('profile'),
      position: 'bottom'
    },
    {
      title: '🔄 Refresh Button',
      content: 'Click this button to refresh all data across tabs - uploads, saved sets, and profile information. Useful after making changes or uploading new files.',
      target: '[data-tour="refresh-button"]',
      position: 'bottom'
    },
    {
      title: '🎉 You\'re All Set!',
      content: 'You now know all the features! Start by uploading a file, then generate your first question set. Need help? Click the Tour button anytime to revisit this guide.',
      target: null,
      position: 'center'
    }
  ]

  /* -----------------------------------
     AUTO SHOW (FIRST TIME ONLY)
  ----------------------------------- */
  useEffect(() => {
    if (!user) return
    const done = localStorage.getItem(`tour_done_${user.id}`)
    if (!done) {
      // Small delay to ensure page is fully loaded
      setTimeout(() => {
        setShowWelcome(true)
      }, 500)
    }
  }, [user])

  /* -----------------------------------
     MANUAL TOUR TRIGGER
  ----------------------------------- */
  useEffect(() => {
    const startFromButton = () => {
      setShowWelcome(false)
      setIsActive(true)
      setCurrentStep(0)
      setTimeout(() => {
        updateHighlight()
      }, 100)
    }

    window.addEventListener('start-tour', startFromButton)
    return () => window.removeEventListener('start-tour', startFromButton)
  }, [])

  /* -----------------------------------
     SMOOTH HIGHLIGHT UPDATE
  ----------------------------------- */
  const updateHighlight = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    animationFrameRef.current = requestAnimationFrame(() => {
      const step = tourSteps[currentStep]
      if (!step?.target || !highlightRef.current) {
        if (highlightRef.current) {
          highlightRef.current.style.display = 'none'
        }
        return
      }

      const el = document.querySelector(step.target)
      if (!el) {
        if (highlightRef.current) {
          highlightRef.current.style.display = 'none'
        }
        return
      }

      // Ensure element is visible
      el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' })

      // Wait for scroll to complete
      setTimeout(() => {
        const rect = el.getBoundingClientRect()
        const padding = 8

        if (highlightRef.current) {
          highlightRef.current.style.display = 'block'
          highlightRef.current.style.left = `${rect.left - padding}px`
          highlightRef.current.style.top = `${rect.top - padding}px`
          highlightRef.current.style.width = `${rect.width + padding * 2}px`
          highlightRef.current.style.height = `${rect.height + padding * 2}px`
          highlightRef.current.style.borderRadius = getComputedStyle(el).borderRadius || '8px'
        }

        // Update tooltip position
        updateTooltipPosition(rect, step.position)
      }, 300)
    })
  }, [currentStep, tourSteps])

  /* -----------------------------------
     TOOLTIP POSITIONING
  ----------------------------------- */
  const updateTooltipPosition = useCallback((rect, preferredPosition = 'bottom') => {
    if (!tooltipRef.current) return

    const tooltip = tooltipRef.current
    const tooltipRect = tooltip.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const spacing = 16
    const tooltipWidth = 380
    const tooltipHeight = tooltipRect.height || 200

    let top = 0
    let left = 0
    let transform = ''

    // Calculate position based on preferred position and available space
    if (preferredPosition === 'center') {
      top = '50%'
      left = '50%'
      transform = 'translate(-50%, -50%)'
    } else {
      // Try bottom first
      if (preferredPosition === 'bottom' && rect.bottom + spacing + tooltipHeight < viewportHeight) {
        top = rect.bottom + spacing
        left = Math.max(spacing, Math.min(rect.left + (rect.width / 2) - (tooltipWidth / 2), viewportWidth - tooltipWidth - spacing))
        transform = 'translateX(0)'
      }
      // Try top if bottom doesn't fit
      else if (rect.top - spacing - tooltipHeight > 0) {
        top = rect.top - spacing - tooltipHeight
        left = Math.max(spacing, Math.min(rect.left + (rect.width / 2) - (tooltipWidth / 2), viewportWidth - tooltipWidth - spacing))
        transform = 'translateX(0)'
      }
      // Try right if top/bottom don't fit
      else if (rect.right + spacing + tooltipWidth < viewportWidth) {
        top = Math.max(spacing, Math.min(rect.top + (rect.height / 2) - (tooltipHeight / 2), viewportHeight - tooltipHeight - spacing))
        left = rect.right + spacing
        transform = 'translateY(-50%)'
      }
      // Try left as last resort
      else if (rect.left - spacing - tooltipWidth > 0) {
        top = Math.max(spacing, Math.min(rect.top + (rect.height / 2) - (tooltipHeight / 2), viewportHeight - tooltipHeight - spacing))
        left = rect.left - spacing - tooltipWidth
        transform = 'translateY(-50%)'
      }
      // Fallback to bottom with adjusted position
      else {
        top = Math.min(rect.bottom + spacing, viewportHeight - tooltipHeight - spacing)
        left = Math.max(spacing, Math.min(rect.left, viewportWidth - tooltipWidth - spacing))
        transform = 'translateX(0)'
      }
    }

    tooltip.style.top = typeof top === 'string' ? top : `${top}px`
    tooltip.style.left = typeof left === 'string' ? left : `${left}px`
    tooltip.style.transform = transform
  }, [])

  /* -----------------------------------
     EFFECTS FOR UPDATES
  ----------------------------------- */
  useEffect(() => {
    if (!isActive) return

    // Update highlight when step or tab changes
    const timeoutId = setTimeout(() => {
      updateHighlight()
    }, 100)

    // Setup resize observer for smooth updates
    if (!resizeObserverRef.current) {
      resizeObserverRef.current = new ResizeObserver(() => {
        updateHighlight()
      })
      resizeObserverRef.current.observe(document.body)
    }

    // Listen for scroll and resize
    const handleScroll = () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      animationFrameRef.current = requestAnimationFrame(updateHighlight)
    }

    window.addEventListener('resize', handleScroll, { passive: true })
    window.addEventListener('scroll', handleScroll, { passive: true, capture: true })

    return () => {
      clearTimeout(timeoutId)
      window.removeEventListener('resize', handleScroll)
      window.removeEventListener('scroll', handleScroll, { capture: true })
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [currentStep, activeTab, isActive, updateHighlight])

  /* -----------------------------------
     START / FINISH
  ----------------------------------- */
  const startTour = () => {
    setShowWelcome(false)
    setIsActive(true)
    setCurrentStep(0)
    setTimeout(() => {
      updateHighlight()
    }, 100)
  }

  const finishTour = () => {
    setIsActive(false)
    setCurrentStep(0)
    if (user) {
      localStorage.setItem(`tour_done_${user.id}`, 'true')
    }
    // Cleanup
    if (highlightRef.current) {
      highlightRef.current.style.display = 'none'
    }
    if (resizeObserverRef.current) {
      resizeObserverRef.current.disconnect()
      resizeObserverRef.current = null
    }
  }

  /* -----------------------------------
     NAVIGATION
  ----------------------------------- */
  const nextStep = () => {
    if (isTransitioning) return
    
    setIsTransitioning(true)
    const next = currentStep + 1
    if (next >= tourSteps.length) {
      finishTour()
      setIsTransitioning(false)
      return
    }

    // Execute action if present
    if (tourSteps[next]?.action) {
      tourSteps[next].action()
    }

    setTimeout(() => {
      setCurrentStep(next)
      setIsTransitioning(false)
      setTimeout(() => {
        updateHighlight()
      }, 200)
    }, 150)
  }

  const prevStep = () => {
    if (isTransitioning) return
    
    setIsTransitioning(true)
    const prev = currentStep - 1
    if (prev < 0) {
      setIsTransitioning(false)
      return
    }

    // Execute action if present
    if (tourSteps[prev]?.action) {
      tourSteps[prev].action()
    }

    setTimeout(() => {
      setCurrentStep(prev)
      setIsTransitioning(false)
      setTimeout(() => {
        updateHighlight()
      }, 200)
    }, 150)
  }

  const skipToEnd = () => {
    finishTour()
  }

  if (!showWelcome && !isActive) return null
  const step = tourSteps[currentStep]

  /* -----------------------------------
     RENDER
  ----------------------------------- */
  return (
    <>
      {/* Welcome Modal */}
      {showWelcome && (
        <div className="fixed inset-0 z-[200] bg-black/70 backdrop-blur-sm flex items-center justify-center animate-fadeIn">
      
      
        <div className="bg-white rounded-2xl p-8 w-[420px] max-w-[90vw] shadow-2xl animate-scaleIn">
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">🎓</div>
              <h2 className="font-bold text-2xl mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Welcome to StudyQnA
              </h2>
              <p className="text-gray-600 text-sm">
                Let's take a quick tour to explore all features and get you started!
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={finishTour}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl py-3 font-semibold transition-colors"
              >
                Skip Tour
              </button>
              <button
                onClick={startTour}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl py-3 font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
              >
                Start Tour
              </button>
            </div>
          </div>
        </div>
      )}

      {isActive && (
        <>
          {/* Dark overlay with smooth transition */}
          <div
            className="fixed inset-0 z-[150] bg-black/60 backdrop-blur-[o.5px] pointer-events-none transition-opacity duration-300"
            style={{ opacity: isActive ? 1 : 0 }}
          />

          {/* Highlight box with smooth animation */}
          <div
            ref={highlightRef}
            className="fixed z-[160] pointer-events-none rounded-lg transition-all duration-300 ease-out"
            style={{
              display: 'none',
              border: '3px solid #3b82f6',
              boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.65), 0 0 20px rgba(59, 130, 246, 0.5)',
              animation: 'pulse-border 2s ease-in-out infinite'
            }}
          />

          {/* Modern Tooltip */}
          <div
            ref={tooltipRef}
            className="fixed z-[170] bg-white rounded-2xl shadow-2xl w-[380px] max-w-[90vw] animate-slideUp"
            style={{
              top: step?.position === 'center' ? '50%' : 'auto',
              left: step?.position === 'center' ? '50%' : 'auto',
              transform: step?.position === 'center' ? 'translate(-50%, -50%)' : 'none'
            }}
          >
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-2xl p-5 text-white">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-white/20 text-xs font-bold px-2.5 py-1 rounded-full backdrop-blur-sm">
                      STEP {currentStep + 1} of {tourSteps.length}
                    </span>
                  </div>
                  <h4 className="font-bold text-lg leading-tight">{step.title}</h4>
                </div>
                <button
                  onClick={skipToEnd}
                  className="text-white/80 hover:text-white hover:bg-white/20 rounded-lg p-1.5 transition-colors"
                  title="Skip tour"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-5">
              <p className="text-gray-700 leading-relaxed text-sm">{step.content}</p>
            </div>

            {/* Footer with navigation */}
            <div className="flex justify-between items-center px-5 pb-5 border-t border-gray-100 pt-4">
              <div className="flex gap-2">
                {currentStep > 0 && (
                  <button
                    onClick={prevStep}
                    disabled={isTransitioning}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Previous
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* Progress dots */}
                <div className="flex gap-1.5">
                  {tourSteps.map((_, index) => (
                    <div
                      key={index}
                      className={`h-2 rounded-full transition-all ${
                        index === currentStep
                          ? 'w-6 bg-blue-600'
                          : index < currentStep
                          ? 'w-2 bg-blue-300'
                          : 'w-2 bg-gray-300'
                      }`}
                    />
                  ))}
                </div>

                <button
                  onClick={currentStep === tourSteps.length - 1 ? finishTour : nextStep}
                  disabled={isTransitioning}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {currentStep === tourSteps.length - 1 ? (
                    <>
                      Finish
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </>
                  ) : (
                    <>
                      Next
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* CSS Animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { transform: scale(0.9); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes pulse-border {
          0%, 100% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.65), 0 0 20px rgba(59, 130, 246, 0.5); }
          50% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.65), 0 0 30px rgba(59, 130, 246, 0.8); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        .animate-scaleIn {
          animation: scaleIn 0.3s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </>
  )
}

export default OnboardingTour
