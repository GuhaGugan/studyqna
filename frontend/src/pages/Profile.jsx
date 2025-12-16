import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

const Profile = () => {
  const { user, logout, isPremium } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const response = await api.getUserProfile()
      setProfile(response.data)
    } catch (error) {
      toast.error('Failed to load profile')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Failed to load profile</p>
      </div>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Matching Dashboard */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">StudyQnA Generator</h1>
              <p className="text-sm text-gray-600">{user?.email}</p>
            </div>
            <div className="flex items-center gap-4">
              {!isPremium && (
                <span className="text-sm text-gray-600">
                  Free Plan
                </span>
              )}
              {isPremium && (
                <span className="text-sm text-green-600 font-semibold">
                  Premium Active
                </span>
              )}
              <button
                onClick={() => navigate('/dashboard')}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Dashboard
              </button>
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">User Profile</h1>

          {/* Account Information */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Account Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Email</label>
                <p className="mt-1 text-gray-900">{profile.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Account Created</label>
                <p className="mt-1 text-gray-900">{formatDate(profile.created_at)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Role</label>
                <p className="mt-1 text-gray-900 capitalize">{profile.role}</p>
              </div>
            </div>
          </div>

          {/* Premium Status */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Premium Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Status</label>
                <p className="mt-1">
                  <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                    profile.premium_status === 'approved'
                      ? 'bg-green-100 text-green-800'
                      : profile.premium_status === 'pending'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {profile.premium_status === 'approved' ? 'Active' : 
                     profile.premium_status === 'pending' ? 'Pending' : 'Inactive'}
                  </span>
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Valid Until</label>
                <p className="mt-1 text-gray-900">
                  {profile.premium_valid_until ? formatDate(profile.premium_valid_until) : 'N/A'}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Payment Request Date</label>
                <p className="mt-1 text-gray-900">
                  {profile.premium_request_date ? formatDate(profile.premium_request_date) : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Usage Statistics */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Usage Statistics</h2>
            
            {/* Total Questions */}
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-700">Total Questions</h3>
                <span className="text-sm text-gray-600">
                  {profile.usage_stats.questions?.used || 0} / {profile.usage_stats.questions?.limit || 700}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${profile.usage_stats.questions?.limit > 0
                      ? Math.min(
                          ((profile.usage_stats.questions?.used || 0) / (profile.usage_stats.questions?.limit || 700)) * 100,
                          100
                        )
                      : 0}%`
                  }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Remaining: {profile.usage_stats.questions?.remaining || 0}
              </p>
            </div>

            {/* Daily Questions */}
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-700">Daily Questions</h3>
                <span className="text-sm text-gray-600">
                  {profile.usage_stats.generations?.used || 0} / {profile.usage_stats.generations?.limit || 50}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${profile.usage_stats.generations?.limit > 0
                      ? Math.min(
                          ((profile.usage_stats.generations?.used || 0) / (profile.usage_stats.generations?.limit || 50)) * 100,
                          100
                        )
                      : 0}%`
                  }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Remaining: {profile.usage_stats.generations?.remaining || 0}
              </p>
            </div>

            {/* Monthly Reset */}
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <span className="font-medium">Monthly Reset Date:</span>{' '}
                {formatDate(profile.usage_stats.monthly_reset_date)}
              </p>
              {profile.usage_stats.monthly_reset_day && (
                <p className="text-xs text-gray-600 mt-1">
                  Your monthly quota resets every {profile.usage_stats.monthly_reset_day} of each month.
                </p>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2025 StudyQnA — Created by GUGAN
          </p>
        </div>
      </footer>
    </div>
  )
}

export default Profile

