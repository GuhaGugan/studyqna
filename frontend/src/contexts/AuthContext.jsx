import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/user/me')
      const newUser = response.data
      
      // Check if user just became premium (trigger welcome animation)
      const wasPremium = user?.premium_status === 'approved' && 
                        user?.premium_valid_until && 
                        new Date(user.premium_valid_until) > new Date()
      const isNowPremium = newUser?.premium_status === 'approved' && 
                          newUser?.premium_valid_until && 
                          new Date(newUser.premium_valid_until) > new Date()
      
      // If user just became premium (wasn't premium before, but is now), trigger welcome animation
      if (user && !wasPremium && isNowPremium) {
        // Dispatch custom event for premium activation
        console.log('🎉 Premium activated! Dispatching event...')
        window.dispatchEvent(new CustomEvent('premiumActivated', { 
          detail: { userId: newUser.id } 
        }))
      }
      
      setUser(newUser)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  // Helper function to extract error message from FastAPI validation errors
  const getErrorMessage = (error) => {
    if (!error?.response?.data) {
      return 'An unexpected error occurred'
    }
    
    const detail = error.response.data.detail
    
    // If detail is a string, return it directly
    if (typeof detail === 'string') {
      return detail
    }
    
    // If detail is an array (validation errors), format it
    if (Array.isArray(detail) && detail.length > 0) {
      const firstError = detail[0]
      // Return a user-friendly message
      if (firstError.msg) {
        const field = firstError.loc && firstError.loc.length > 1 
          ? firstError.loc[firstError.loc.length - 1] 
          : 'field'
        return `${field}: ${firstError.msg}`
      }
      return 'Validation error: Please check your input'
    }
    
    // Fallback
    return 'Request failed. Please try again.'
  }

  const login = async (email, otp) => {
    try {
      const response = await axios.post('/api/auth/otp/verify', { email, otp })
      const { access_token, role } = response.data
      
      localStorage.setItem('token', access_token)
      setToken(access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      await fetchUser()
      
      return role
    } catch (error) {
      const errorMsg = getErrorMessage(error)
      toast.error(errorMsg)
      throw error
    }
  }

  const requestOTP = async (email) => {
    try {
      await axios.post('/api/auth/otp/request', { email })
      toast.success('OTP sent to your email')
    } catch (error) {
      const errorMsg = getErrorMessage(error)
      toast.error(errorMsg)
      throw error
    }
  }

  const logout = async () => {
    try {
      // Call logout endpoint to record logout time
      await axios.post('/api/user/logout')
    } catch (error) {
      // Even if logout endpoint fails, continue with local logout
      console.error('Failed to log logout time:', error)
    } finally {
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)
      delete axios.defaults.headers.common['Authorization']
    }
  }

  const value = {
    user,
    loading,
    login,
    requestOTP,
    logout,
    fetchUser,
    isAdmin: user?.role === 'admin',
    isPremium: user?.premium_status === 'approved' && 
               new Date(user?.premium_valid_until) > new Date()
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

