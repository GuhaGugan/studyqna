import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import QRCode from 'qrcode.react'

const PremiumBanner = () => {
  const [showQR, setShowQR] = useState(false)
  const [requesting, setRequesting] = useState(false)

  // Replace these with your actual payment links
  // Option 1: UPI Payment Links (works with both PhonePe and Google Pay)
  const PHONEPE_LINK = "YOUR_PHONEPE_PAYMENT_LINK_HERE" // e.g., "https://phon.pe/your-link-id" or UPI link
  const GPAY_LINK = "YOUR_GPAY_PAYMENT_LINK_HERE" // e.g., "https://gpay.app.goo.gl/your-link-id" or UPI link
  
  // Option 2: Universal UPI Link (works with any UPI app)
  // Format: upi://pay?pa=YOUR_UPI_ID@paytm&pn=StudyQnA&am=599&cu=INR&tn=Premium%20Subscription
  const UPI_PAYMENT_LINK = "YOUR_UPI_PAYMENT_LINK_HERE" // Replace with your UPI payment link

  const handleRequestPremium = async () => {
    setRequesting(true)
    try {
      await api.requestPremium()
      toast.success('Premium request submitted! Admin will review it shortly.')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to request premium')
    } finally {
      setRequesting(false)
    }
  }

  return (
    <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white py-4">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex-1 text-center sm:text-left">
            <h3 className="font-bold text-lg mb-1">Upgrade to Full Access</h3>
            <p className="text-sm">
              650+ Q/A generation, downloads, and premium features
            </p>
          </div>
          <div className="flex items-center gap-4">
            {showQR && (
              <div className="bg-white p-4 rounded-lg shadow-lg">
                <div className="flex flex-col sm:flex-row gap-4 items-center">
                  {/* PhonePe QR Code */}
                  <div className="flex flex-col items-center">
                    <QRCode 
                      value={PHONEPE_LINK !== "YOUR_PHONEPE_PAYMENT_LINK_HERE" ? PHONEPE_LINK : UPI_PAYMENT_LINK} 
                      size={120} 
                    />
                    <p className="text-xs text-gray-600 mt-2 text-center font-semibold">PhonePe</p>
                    <p className="text-xs text-gray-500 mt-1">Scan & Pay ₹599</p>
                  </div>
                  
                  {/* Google Pay QR Code */}
                  <div className="flex flex-col items-center">
                    <QRCode 
                      value={GPAY_LINK !== "YOUR_GPAY_PAYMENT_LINK_HERE" ? GPAY_LINK : UPI_PAYMENT_LINK} 
                      size={120} 
                    />
                    <p className="text-xs text-gray-600 mt-2 text-center font-semibold">Google Pay</p>
                    <p className="text-xs text-gray-500 mt-1">Scan & Pay ₹599</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-3 text-center">
                  Pay using any UPI app (PhonePe, Google Pay, Paytm, etc.)
                </p>
              </div>
            )}
            <button
              onClick={() => setShowQR(!showQR)}
              className="px-4 py-2 bg-white text-orange-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-sm"
            >
              {showQR ? 'Hide QR' : 'Show QR Code'}
            </button>
            <button
              onClick={handleRequestPremium}
              disabled={requesting}
              className="px-6 py-2 bg-white text-orange-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50 text-sm"
            >
              {requesting ? 'Requesting...' : 'Request Access'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PremiumBanner

