import { useState } from 'react'

const HelpTooltip = ({ content, position = 'top', children, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false)

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        type="button"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors text-xs font-semibold cursor-help"
        aria-label="Help"
      >
        ?
      </button>
      {isVisible && (
        <div
          className={`absolute z-[100] ${positionClasses[position]} w-64 max-w-[90vw] p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl pointer-events-none animate-fadeIn break-words`}
        >
          <div className="relative">
            <div className="overflow-y-auto max-h-[60vh]">
              {content}
            </div>
            {/* Arrow */}
            <div
              className={`absolute ${
                position === 'top' ? 'top-full left-1/2 -translate-x-1/2 border-t-gray-900 border-t-4 border-x-transparent border-x-4' :
                position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-900 border-b-4 border-x-transparent border-x-4' :
                position === 'left' ? 'left-full top-1/2 -translate-y-1/2 border-l-gray-900 border-l-4 border-y-transparent border-y-4' :
                'right-full top-1/2 -translate-y-1/2 border-r-gray-900 border-r-4 border-y-transparent border-y-4'
              }`}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default HelpTooltip

