import { useEffect } from 'react'

const PremiumWelcome = ({ onClose }) => {
  useEffect(() => {
    // Load canvas-confetti dynamically
    let confetti = null
    
    const loadConfetti = async () => {
      try {
        const module = await import('canvas-confetti')
        confetti = module.default
        startAnimation(confetti)
      } catch (error) {
        console.warn('canvas-confetti not available, using fallback animation')
        // Fallback: simple CSS animation
        startFallbackAnimation()
      }
    }
    
    const startAnimation = (confettiFn) => {
      if (!confettiFn) return
      
      const duration = 3000
      const animationEnd = Date.now() + duration
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 }

      function randomInRange(min, max) {
        return Math.random() * (max - min) + min
      }

      const interval = setInterval(() => {
        const timeLeft = animationEnd - Date.now()

        if (timeLeft <= 0) {
          return clearInterval(interval)
        }

        const particleCount = 50 * (timeLeft / duration)
        
        confettiFn({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
        })
        confettiFn({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
        })
      }, 250)
      
      return () => clearInterval(interval)
    }
    
    const startFallbackAnimation = () => {
      // Simple CSS-based celebration effect
      const element = document.querySelector('.premium-welcome-modal')
      if (element) {
        element.classList.add('animate-bounce')
      }
    }
    
    loadConfetti()
    
    // Auto close after animation
    const timer = setTimeout(() => {
      if (onClose) onClose()
    }, 3500)

    return () => {
      clearTimeout(timer)
    }
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50 premium-welcome-modal px-4 py-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4 my-auto max-h-[90vh] overflow-y-auto text-center">
        <div className="mb-4">
          <div className="text-6xl mb-4 animate-bounce">🎉</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Premium!
          </h2>
          <p className="text-lg text-gray-600">
            Enjoy full access for 30 days.
          </p>
        </div>
        <button
          onClick={onClose}
          className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Get Started
        </button>
      </div>
    </div>
  )
}

export default PremiumWelcome
