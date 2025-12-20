import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

/**
 * Custom hook to handle idle timeout and auto-logout
 * @param {number} idleTimeoutMinutes - Minutes of inactivity before logout (default: 10)
 * @param {number} warningMinutes - Minutes before logout to show warning (default: 1)
 */
export const useIdleTimeout = (idleTimeoutMinutes = 10, warningMinutes = 1) => {
  const { logout, user } = useAuth()
  const [showWarning, setShowWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(null)
  const timeoutRef = useRef(null)
  const warningTimeoutRef = useRef(null)
  const countdownIntervalRef = useRef(null)
  const lastActivityRef = useRef(Date.now())

  const idleTimeoutMs = idleTimeoutMinutes * 60 * 1000 // Convert to milliseconds
  const warningTimeoutMs = (idleTimeoutMinutes - warningMinutes) * 60 * 1000

  const resetTimer = () => {
    // Clear existing timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current)
      warningTimeoutRef.current = null
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current)
      countdownIntervalRef.current = null
    }

    // Hide warning if it was showing
    setShowWarning(false)
    setTimeRemaining(null)

    // Update last activity time
    lastActivityRef.current = Date.now()

    // Only set timers if user is logged in
    if (!user) return

    // Set warning timer (show warning before logout)
    warningTimeoutRef.current = setTimeout(() => {
      setShowWarning(true)
      const remainingSeconds = warningMinutes * 60
      setTimeRemaining(remainingSeconds)

      // Start countdown
      countdownIntervalRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            clearInterval(countdownIntervalRef.current)
            return 0
          }
          return prev - 1
        })
      }, 1000)

      // Show warning toast
      toast.error(
        `You will be logged out in ${warningMinutes} minute${warningMinutes > 1 ? 's' : ''} due to inactivity. Move your mouse or click anywhere to stay logged in.`,
        {
          duration: warningMinutes * 60 * 1000, // Show for the entire warning period
          id: 'idle-warning', // Use same ID to prevent duplicate toasts
        }
      )
    }, warningTimeoutMs)

    // Set logout timer
    timeoutRef.current = setTimeout(() => {
      toast.error('You have been logged out due to inactivity.', {
        duration: 5000,
      })
      logout()
    }, idleTimeoutMs)
  }

  const handleActivity = () => {
    // Only reset if user is logged in
    if (user) {
      resetTimer()
    }
  }

  useEffect(() => {
    // Only set up idle timeout if user is logged in
    if (!user) {
      // Clear timers if user logs out
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current)
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current)
      setShowWarning(false)
      setTimeRemaining(null)
      return
    }

    // Set initial timer
    resetTimer()

    // Event listeners for user activity
    const events = [
      'mousedown',
      'mousemove',
      'keypress',
      'scroll',
      'touchstart',
      'click',
    ]

    events.forEach((event) => {
      document.addEventListener(event, handleActivity, { passive: true })
    })

    // Cleanup
    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity)
      })
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current)
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]) // Re-run when user changes (login/logout)

  return {
    showWarning,
    timeRemaining,
    resetTimer, // Expose reset function in case needed
  }
}

