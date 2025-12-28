import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'

const ProfileTab = () => {
  const { user, isPremium } = useAuth()
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading profile...</p>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Failed to load profile</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-lg md:text-xl font-semibold mb-4 md:mb-6">User Profile</h2>

      {/* Account Information */}
      <div className="mb-6 md:mb-8">
        <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-3 md:mb-4">Account Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Email</label>
            <p className="text-base md:text-base text-gray-900 font-medium break-words">{profile.email}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Role</label>
            <p className="text-base md:text-base text-gray-900 font-medium capitalize">{profile.role}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Account Created</label>
            <p className="text-base md:text-base text-gray-900 font-medium">{formatDate(profile.created_at)}</p>
          </div>
        </div>
      </div>

      {/* Premium Status */}
      <div className="mb-6 md:mb-8">
        <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-3 md:mb-4">Premium Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Status</label>
            <p className="mt-1">
              <span className={`inline-flex px-3 py-1.5 rounded-full text-sm md:text-sm font-medium ${
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
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Valid Until</label>
            <p className="text-base md:text-base text-gray-900 font-medium">
              {profile.premium_valid_until ? formatDate(profile.premium_valid_until) : 'N/A'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 md:p-4">
            <label className="text-sm md:text-sm font-medium text-gray-600 block mb-2">Payment Request Date</label>
            <p className="text-base md:text-base text-gray-900 font-medium">
              {profile.premium_request_date ? formatDate(profile.premium_request_date) : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      <div className="mb-6 md:mb-8">
        <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-3 md:mb-4">Usage Statistics</h3>
        
        {/* Total Questions */}
        <div className="mb-4 p-4 md:p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm md:text-base font-medium text-gray-800">Total Questions</h4>
            <span className="text-sm md:text-sm font-medium text-gray-700">
              {profile.usage_stats.questions?.used || 0} / {profile.usage_stats.questions?.limit || 700}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 md:h-3 mb-2">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all"
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
          <p className="text-xs md:text-sm text-gray-600">
            Remaining: {profile.usage_stats.questions?.remaining || 0}
          </p>
        </div>

        {/* Daily Questions */}
        <div className="mb-4 p-4 md:p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm md:text-base font-medium text-gray-800">Daily Questions</h4>
            <span className="text-sm md:text-sm font-medium text-gray-700">
              {profile.usage_stats.daily_questions?.used || 0} / {profile.usage_stats.daily_questions?.limit || 50}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 md:h-3 mb-2">
            <div
              className="bg-green-600 h-3 rounded-full transition-all"
              style={{
                width: `${profile.usage_stats.daily_questions?.limit > 0
                  ? Math.min(
                      ((profile.usage_stats.daily_questions?.used || 0) / (profile.usage_stats.daily_questions?.limit || 50)) * 100,
                      100
                    )
                  : 0}%`
              }}
            ></div>
          </div>
          <p className="text-xs md:text-sm text-gray-600">
            Remaining: {profile.usage_stats.daily_questions?.remaining || 0}
          </p>
        </div>

        {/* Monthly Reset */}
        <div className="p-4 md:p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm md:text-sm text-gray-700">
            <span className="font-medium">Monthly Reset Date:</span>{' '}
            {formatDate(profile.usage_stats.monthly_reset_date)}
          </p>
          {profile.usage_stats.monthly_reset_day && (
            <p className="text-xs md:text-sm text-gray-600 mt-1">
              Your monthly quota resets every {profile.usage_stats.monthly_reset_day} of each month.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProfileTab

