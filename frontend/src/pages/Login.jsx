import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

const Login = () => {
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState('email') // 'email' or 'otp'
  const [loading, setLoading] = useState(false)
  const [emailError, setEmailError] = useState('')
  const { requestOTP, login, deviceLogin, isAdmin } = useAuth()
  const navigate = useNavigate()

  // Check for device token on component mount
  useEffect(() => {
    const deviceToken = localStorage.getItem('device_token')
    const deviceEmail = localStorage.getItem('device_email')
    
    if (deviceToken && deviceEmail) {
      // Try device login automatically
      setEmail(deviceEmail)
      handleDeviceLogin(deviceEmail, deviceToken)
    }
  }, [])

  const handleDeviceLogin = async (email, deviceToken) => {
    setLoading(true)
    try {
      const role = await deviceLogin(email, deviceToken)
      toast.success('Welcome back!')
      
      // Redirect based on role
      if (role === 'admin') {
        navigate('/admin')
      } else {
        navigate('/dashboard')
      }
    } catch (error) {
      // Device login failed - user needs to login with OTP
      // Clear invalid device token
      localStorage.removeItem('device_token')
      localStorage.removeItem('device_email')
      setLoading(false)
      // Continue with normal login flow
    }
  }

  // Email validation function
  const validateEmailFormat = (email) => {
    if (!email) {
      return 'Email address is required'
    }

    const trimmedEmail = email.trim().toLowerCase()
    
    // Basic format check
    const emailRegex = /^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$/
    
    if (!emailRegex.test(trimmedEmail)) {
      return 'Invalid email format. Please enter a valid email address.'
    }

    // Check for invalid patterns
    if (trimmedEmail.includes('..')) {
      return 'Invalid email format. Email cannot contain consecutive dots.'
    }

    if (trimmedEmail.startsWith('.') || trimmedEmail.endsWith('.')) {
      return 'Invalid email format. Email cannot start or end with a dot.'
    }

    if (trimmedEmail.split('@').length !== 2) {
      return 'Invalid email format. Email must contain exactly one @ symbol.'
    }

    const [localPart, domain] = trimmedEmail.split('@')

    if (!localPart || localPart.length > 64) {
      return 'Invalid email format. Username part is too long.'
    }

    if (!domain || domain.length > 255) {
      return 'Invalid email format. Domain part is invalid.'
    }

    if (!domain.includes('.')) {
      return 'Invalid email format. Domain must contain a dot.'
    }

    const domainParts = domain.split('.')
    const tld = domainParts[domainParts.length - 1]
    
    if (tld.length < 2 || !/^[a-zA-Z]+$/.test(tld)) {
      return 'Invalid email format. Domain must have a valid extension (e.g., .com, .org).'
    }

    // Check for test/example domains
    const invalidDomains = ['test.com', 'example.com', 'localhost', '127.0.0.1']
    if (invalidDomains.some(invalid => domain.includes(invalid))) {
      return 'Invalid email address. Please use a real email address.'
    }

    return null // Email is valid
  }

  const handleEmailChange = (e) => {
    const value = e.target.value
    setEmail(value)
    
    // Real-time validation (only show error after user starts typing)
    if (value.length > 0) {
      const error = validateEmailFormat(value)
      setEmailError(error || '')
    } else {
      setEmailError('')
    }
  }

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    
    // Validate email before submitting
    const validationError = validateEmailFormat(email)
    if (validationError) {
      setEmailError(validationError)
      toast.error(validationError)
      return
    }

    setLoading(true)
    setEmailError('')
    
    try {
      const result = await requestOTP(email.trim().toLowerCase())
      
      // Check if device login was successful (no OTP required)
      if (result && !result.requiresOTP) {
        // Device login successful - redirect
        if (result.role === 'admin') {
          navigate('/admin')
        } else {
          navigate('/dashboard')
        }
        return
      }
      
      // OTP required - show OTP input
      setStep('otp')
    } catch (error) {
      // Error message from backend will be shown via toast
      const errorMsg = error.response?.data?.detail || 'Failed to send OTP'
      setEmailError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleOTPSubmit = async (e) => {
    e.preventDefault()
    if (!otp || otp.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP')
      return
    }

    setLoading(true)
    try {
      const role = await login(email, otp)
      toast.success('Login successful!')
      
      // Redirect based on role
      if (role === 'admin') {
        navigate('/admin')
      } else {
        navigate('/dashboard')
      }
    } catch (error) {
      // Error already handled in context
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">StudyQnA Generator</h1>
          <p className="text-gray-600">AI-powered Q/A generation from PDFs and Images</p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleEmailSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={handleEmailChange}
                onBlur={() => {
                  // Validate on blur
                  if (email) {
                    const error = validateEmailFormat(email)
                    setEmailError(error || '')
                  }
                }}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  emailError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                }`}
                placeholder="your.email@example.com"
                required
              />
              {emailError && (
                <p className="mt-1 text-sm text-red-600">{emailError}</p>
              )}
              {!emailError && email && (
                <p className="mt-1 text-sm text-green-600">✓ Valid email format</p>
              )}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleOTPSubmit} className="space-y-6">
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
                Enter OTP
              </label>
              <input
                type="text"
                id="otp"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest"
                placeholder="000000"
                maxLength={6}
                required
              />
              <p className="mt-2 text-sm text-gray-500">
                Check your email for the 6-digit OTP
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setStep('email')
                  setOtp('')
                }}
                className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default Login

