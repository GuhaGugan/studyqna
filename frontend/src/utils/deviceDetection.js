/**
 * Detect if user is on a mobile device
 */
export const isMobileDevice = () => {
  // Check user agent
  const userAgent = navigator.userAgent || navigator.vendor || window.opera
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile|CriOS/i.test(userAgent)
  
  // Check screen width (mobile is typically < 768px)
  const isMobileWidth = window.innerWidth < 768
  
  // Check touch support
  const hasTouchScreen = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  
  return isMobileUA || (isMobileWidth && hasTouchScreen)
}

/**
 * Check if device has camera support for file input
 * For mobile, we use the capture attribute which works differently
 */
export const hasCameraSupport = () => {
  // For mobile devices, we can use capture attribute in file input
  // This doesn't require getUserMedia API
  if (isMobileDevice()) {
    return true // Mobile devices support camera via file input capture
  }
  
  // For desktop, check for webcam API (optional)
  return navigator.mediaDevices && navigator.mediaDevices.getUserMedia
}

