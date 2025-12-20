import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import Profile from './pages/Profile'
import ProtectedRoute from './components/ProtectedRoute'
import { useIdleTimeout } from './hooks/useIdleTimeout'

// Component to handle idle timeout (must be inside AuthProvider)
const IdleTimeoutHandler = () => {
  const { showWarning, timeRemaining } = useIdleTimeout(10, 1) // 10 minutes idle, 1 minute warning
  
  // Render warning modal if warning is active
  if (showWarning && timeRemaining !== null) {
    const minutes = Math.floor(timeRemaining / 60)
    const seconds = timeRemaining % 60
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
        <div className="bg-white rounded-lg shadow-2xl p-6 max-w-md mx-4">
          <div className="text-center">
            <div className="text-6xl mb-4">⏰</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Session Timeout Warning
            </h2>
            <p className="text-gray-600 mb-4">
              You have been inactive for 9 minutes. You will be logged out automatically in:
            </p>
            <div className="text-4xl font-bold text-red-600 mb-4">
              {minutes}:{seconds.toString().padStart(2, '0')}
            </div>
            <p className="text-sm text-gray-500">
              Move your mouse or click anywhere to stay logged in.
            </p>
          </div>
        </div>
      </div>
    )
  }
  
  return null
}

function App() {
  return (
    <AuthProvider>
      <IdleTimeoutHandler />
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute adminOnly>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App

