import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'

const OnboardingTour = ({ activeTab, setActiveTab }) => {
  const { user } = useAuth()

  const [currentStep, setCurrentStep] = useState(0)
  const [isActive, setIsActive] = useState(false)
  const [showWelcome, setShowWelcome] = useState(false)

  const highlightRef = useRef(null)

  /* -----------------------------------
     TOUR STEPS
  ----------------------------------- */
  const tourSteps = [
    { title: 'Welcome to StudyQnA 🎓', content: 'Let\'s quickly walk through the app.', target: null },

    { title: 'Upload', content: 'Upload PDFs or images to start.', target: '[data-tour="upload-tab"]', action: () => setActiveTab('upload') },

    { title: 'Usage Limits', content: 'See daily & total question usage.', target: '[data-tour="quota-cards"]' },

    { title: 'File Upload', content: 'Drag & drop or browse files.', target: '[data-tour="file-upload"]' },

    { title: 'Generate', content: 'Create exam-ready questions.', target: '[data-tour="generate-tab"]', action: () => setActiveTab('generate') },

    { title: 'Saved Sets', content: 'Reuse generated questions.', target: '[data-tour="saved-tab"]', action: () => setActiveTab('saved') },

    { title: 'Reviews', content: 'Share your feedback.', target: '[data-tour="review-tab"]', action: () => setActiveTab('review') },

    { title: 'Profile', content: 'Manage account & plan.', target: '[data-tour="profile-tab"]', action: () => setActiveTab('profile') },

    { title: 'All Set 🎉', content: 'You\'re ready to use StudyQnA!', target: null }
  ]

  /* -----------------------------------
     AUTO SHOW (FIRST TIME ONLY)
  ----------------------------------- */
  useEffect(() => {
    if (!user) return
    const done = localStorage.getItem(`tour_done_${user.id}`)
    if (!done) {
      setShowWelcome(true)
    }
  }, [user])

  /* -----------------------------------
     MANUAL TOUR TRIGGER (TOP BUTTON)
     window.dispatchEvent(new Event('start-tour'))
  ----------------------------------- */
  useEffect(() => {
    const startFromButton = () => {
      setShowWelcome(false)
      setIsActive(true)
      setCurrentStep(0)
      setTimeout(updateHighlight, 300)
    }

    window.addEventListener('start-tour', startFromButton)
    return () => window.removeEventListener('start-tour', startFromButton)
  }, [])

  /* -----------------------------------
     START / FINISH
  ----------------------------------- */
  const startTour = () => {
    setShowWelcome(false)
    setIsActive(true)
    setCurrentStep(0)
    setTimeout(updateHighlight, 300)
  }

  const finishTour = () => {
    setIsActive(false)
    if (user) localStorage.setItem(`tour_done_${user.id}`, 'true')
  }

  /* -----------------------------------
     NAVIGATION
  ----------------------------------- */
  const nextStep = () => {
    const next = currentStep + 1
    if (next >= tourSteps.length) {
      finishTour()
      return
    }
    tourSteps[next]?.action?.()
    setTimeout(() => {
      setCurrentStep(next)
      setTimeout(updateHighlight, 300)
    }, 200)
  }

  const prevStep = () => {
    const prev = currentStep - 1
    if (prev < 0) return
    tourSteps[prev]?.action?.()
    setTimeout(() => {
      setCurrentStep(prev)
      setTimeout(updateHighlight, 300)
    }, 200)
  }

  /* -----------------------------------
     HIGHLIGHT BOX
  ----------------------------------- */
  const updateHighlight = () => {
    const step = tourSteps[currentStep]
    if (!step?.target || !highlightRef.current) {
      if (highlightRef.current) highlightRef.current.style.display = 'none'
      return
    }

    const el = document.querySelector(step.target)
    if (!el) return

    el.scrollIntoView({ behavior: 'smooth', block: 'center' })

    setTimeout(() => {
      const r = el.getBoundingClientRect()
      highlightRef.current.style.display = 'block'
      highlightRef.current.style.left = `${r.left - 6}px`
      highlightRef.current.style.top = `${r.top - 6}px`
      highlightRef.current.style.width = `${r.width + 12}px`
      highlightRef.current.style.height = `${r.height + 12}px`
    }, 200)
  }

  useEffect(() => {
    if (!isActive) return
    updateHighlight()
    window.addEventListener('resize', updateHighlight)
    window.addEventListener('scroll', updateHighlight, true)
    return () => {
      window.removeEventListener('resize', updateHighlight)
      window.removeEventListener('scroll', updateHighlight, true)
    }
  }, [currentStep, activeTab, isActive])

  if (!showWelcome && !isActive) return null
  const step = tourSteps[currentStep]

  /* -----------------------------------
     TOOLTIP POSITION (CHATGPT STYLE)
  ----------------------------------- */
  const tooltipStyle = () => {
    if (!step.target) {
      return { top: '15%', left: '50%', transform: 'translateX(-50%)' }
    }
    const el = document.querySelector(step.target)
    if (!el) return { top: '15%', left: '50%', transform: 'translateX(-50%)' }

    const r = el.getBoundingClientRect()
    return {
      top: Math.min(r.bottom + 14, window.innerHeight - 160),
      left: Math.min(Math.max(r.left, 16), window.innerWidth - 360)
    }
  }

  /* -----------------------------------
     RENDER
  ----------------------------------- */
  return (
    <>
      {/* Welcome Modal */}
      {showWelcome && (
        <div className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center">
          <div className="bg-white rounded-xl p-6 w-[360px]">
            <h2 className="font-bold text-lg mb-2">Welcome to StudyQnA 🎓</h2>
            <p className="text-gray-600 mb-4">Quick tour to get started.</p>
            <div className="flex gap-2">
              <button onClick={finishTour} className="flex-1 bg-gray-200 rounded py-2">
                Skip
              </button>
              <button onClick={startTour} className="flex-1 bg-blue-600 text-white rounded py-2">
                Start
              </button>
            </div>
          </div>
        </div>
      )}

      {isActive && (
        <>
          {/* Dark overlay (not clickable) */}
          <div className="fixed inset-0 z-[150] bg-black/50 pointer-events-none" />

          {/* Highlight box */}
          <div
            ref={highlightRef}
            className="fixed z-[160] pointer-events-none rounded-lg"
            style={{
              display: 'none',
              border: '3px solid #3b82f6',
              boxShadow: '0 0 0 9999px rgba(0,0,0,0.6)'
            }}
          />

          {/* ChatGPT-style popup */}
          <div
            className="fixed z-[170] bg-blue-600 text-white rounded-xl shadow-xl w-[340px]"
            style={tooltipStyle()}
          >
            <div className="flex items-start gap-3 p-4">
              <span className="bg-white text-blue-600 text-xs font-bold px-2 py-0.5 rounded">
                NEW
              </span>

              <div className="flex-1">
                <h4 className="font-semibold text-sm">{step.title}</h4>
                <p className="text-sm opacity-90">{step.content}</p>
              </div>

              <button onClick={finishTour} className="text-lg leading-none">
                ×
              </button>
            </div>

            <div className="flex justify-between items-center px-4 pb-3">
              <span className="text-xs opacity-70">
                {currentStep + 1} / {tourSteps.length}
              </span>

              <div className="flex gap-2">
                {currentStep > 0 && (
                  <button onClick={prevStep} className="text-xs bg-white/20 px-3 py-1 rounded">
                    Prev
                  </button>
                )}
                <button
                  onClick={currentStep === tourSteps.length - 1 ? finishTour : nextStep}
                  className="text-xs bg-white text-blue-600 px-3 py-1 rounded font-semibold"
                >
                  {currentStep === tourSteps.length - 1 ? 'Finish' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}

export default OnboardingTour
