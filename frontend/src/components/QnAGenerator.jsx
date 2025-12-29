import { useState, useEffect, useRef } from 'react'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import { InlineMath, BlockMath } from 'react-katex'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { getRotatingMessages } from '../utils/rotatingLoader'
import { isMobileDevice } from '../utils/deviceDetection'
import 'katex/dist/katex.min.css'

const QnAGenerator = ({ uploads, selectedUpload, onSelectUpload, isPremium, onGenerationComplete }) => {
  const { fetchUser } = useAuth()
  const deriveTypeFromMarks = (marks) => {
    if (marks === 'mixed') return 'mixed'
    const m = parseInt(marks, 10)
    if (m === 1) return 'mcq'
    if (m === 2) return 'short'
    return 'descriptive' // 3, 5, 10, defaults
  }

  // Check if multi-select mode (selectedPartIds from PdfSplitParts)
  const selectedPartIds = selectedUpload?.selectedPartIds || null
  
  // Calculate default questions based on parts selected and marks pattern
  // Pattern per part based on marks:
  // - 1 mark: 12 questions per part
  // - 2 marks: 6 questions per part
  // - 3 marks: 4 questions per part
  // - 5 marks: 3 questions per part
  // - 10 marks: 2 questions per part (desktop only, excluded on mobile)
  // - mixed: 16 questions per part (desktop) or 15 questions per part (mobile - no 10 marks)
  const calculateDefaultQuestions = (partCount, marksPattern, mobileMode = false) => {
    if (!partCount || partCount === 0) return isPremium ? 10 : 3
    
    // For mixed pattern: 15 questions per part on mobile (no 10 marks), 16 on desktop
    let questionsPerPart = mobileMode ? 15 : 16 // Default for mixed
    
    if (marksPattern && marksPattern !== 'mixed') {
      const marks = parseInt(marksPattern, 10)
      switch (marks) {
        case 1:
          questionsPerPart = 12
          break
        case 2:
          questionsPerPart = 6
          break
        case 3:
          questionsPerPart = 4
          break
        case 5:
          questionsPerPart = 3
          break
        case 10:
          // 10 marks excluded on mobile
          questionsPerPart = mobileMode ? 0 : 2
          break
        default:
          questionsPerPart = mobileMode ? 15 : 16
      }
    }
    
    return partCount * questionsPerPart
  }
  
  const [settings, setSettings] = useState({
    upload_id: selectedPartIds ? null : (selectedUpload?.id || ''),  // null if multi-select
    part_ids: selectedPartIds || null,  // Array of part IDs for multi-select
    difficulty: 'medium',
    qna_type: 'mixed',
    num_questions: selectedPartIds && selectedPartIds.length > 0 
      ? calculateDefaultQuestions(selectedPartIds.length, 'mixed', false) // Will be updated when isMobile is set
      : (isPremium ? 10 : 3),
    output_format: isPremium ? 'questions_answers' : 'questions_only',  // Free users get questions_only by default
    include_answers: isPremium,  // Free users can't include answers
    marks: 'mixed',
    target_language: '' // No default language - user must select
  })
  const [isNumQuestionsManuallySet, setIsNumQuestionsManuallySet] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)
  const [generationComplete, setGenerationComplete] = useState(false) // Track if generation is complete
  const [isMobile, setIsMobile] = useState(false) // Track mobile device
  
  // Detect mobile device and update distribution accordingly
  useEffect(() => {
    const checkMobile = () => {
      const mobile = isMobileDevice()
      setIsMobile(mobile)
      // Update num_questions if parts are selected and mobile status changed
      if (selectedPartIds && selectedPartIds.length > 0 && !isNumQuestionsManuallySet) {
        const calculated = calculateDefaultQuestions(selectedPartIds.length, settings.marks, mobile)
        setSettings(prev => ({
          ...prev,
          num_questions: calculated
        }))
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [selectedPartIds, settings.marks, isNumQuestionsManuallySet])
  
  // Reset generation complete state when upload/part selection changes
  // Convert selectedPartIds to string for reliable change detection
  const selectedPartIdsStr = selectedUpload?.selectedPartIds ? JSON.stringify(selectedUpload.selectedPartIds.sort()) : ''
  
  // Debug: Track result state changes
  useEffect(() => {
    console.log('📊 Result state changed:', {
      hasResult: !!result,
      resultId: result?.id,
      questionCount: result?.qna_json?.questions?.length || 0,
      isMobile: isMobile
    })
  }, [result, isMobile])
  
  useEffect(() => {
    // Reset when selectedUpload changes (including when parts are selected)
    console.log('🔄 Resetting result due to upload/part change:', {
      selectedUploadId: selectedUpload?.id,
      selectedPartIdsStr,
      isMobile
    })
    setGenerationComplete(false)
    setResult(null)
    setEditedQuestions([])
  }, [selectedUpload?.id, selectedPartIdsStr]) // Use stringified sorted array for reliable change detection
  
  // Also reset when settings change (parts/upload selection) - this handles cases where selectedUpload doesn't change
  useEffect(() => {
    // Reset if we have a valid selection (upload or parts) - this ensures reset even if selectedUpload reference doesn't change
    const hasUpload = settings.upload_id && settings.upload_id !== ''
    const hasParts = settings.part_ids && Array.isArray(settings.part_ids) && settings.part_ids.length > 0
    
    if (hasUpload || hasParts) {
      setGenerationComplete(false)
    }
  }, [settings.upload_id, JSON.stringify(settings.part_ids)]) // Use JSON.stringify to detect array changes
  const [showDownloadMenu, setShowDownloadMenu] = useState(false)
  const [editedQuestions, setEditedQuestions] = useState([])
  const [downloading, setDownloading] = useState(false)
  const [downloadAbortController, setDownloadAbortController] = useState(null)
  const [downloadToastId, setDownloadToastId] = useState(null)
  const [generateAbortController, setGenerateAbortController] = useState(null)
  const [generateToastId, setGenerateToastId] = useState(null)
  
  // Helper function to render LaTeX in text
  const renderLatexInText = (text) => {
    if (!text) return null
    
    // Split by LaTeX delimiters and render accordingly
    const parts = text.split(/(\\(?:\([^)]*\)|\[[^\]]*\]))/g)
    return parts.map((part, i) => {
      if (part.match(/^\\\(.*\\\)$/)) {
        // Inline math
        const math = part.slice(2, -2) // Remove \( and \)
        return <InlineMath key={i} math={math} />
      } else if (part.match(/^\\\[.*\\\]$/)) {
        // Display math
        const math = part.slice(2, -2) // Remove \[ and \]
        return <BlockMath key={i} math={math} />
      } else {
        return <span key={i}>{part}</span>
      }
    })
  }
  
  // Helper function to extract LaTeX from text (removes delimiters)
  const extractLatex = (text) => {
    if (!text) return ''
    // Remove \( and \) or \[ and \]
    return text.replace(/\\\(|\\\)/g, '').replace(/\\\[|\\\]/g, '').trim()
  }
  
  // Helper function to parse string answer with embedded headings
  const parseStringAnswer = (answerStr) => {
    if (typeof answerStr !== 'string') return null
    
    // Check for English structure (Introduction, Explanation, Analysis, Conclusion)
    const englishPattern = /(?:Introduction|Introduction:)\s*([^\n]+(?:\n(?!Explanation|Analysis|Conclusion)[^\n]+)*)/i
    const explanationPattern = /(?:Explanation|Explanation:)\s*([^\n]+(?:\n(?!Analysis|Conclusion|Introduction)[^\n]+)*)/i
    const analysisPattern = /(?:Analysis|Analysis:)\s*([^\n]+(?:\n(?!Conclusion|Introduction|Explanation)[^\n]+)*)/i
    const conclusionPattern = /(?:Conclusion|Conclusion:)\s*([^\n]+(?:\n(?!Introduction|Explanation|Analysis)[^\n]+)*)/i
    
    // Check for Science structure (Definition, Explanation, Example, Conclusion)
    const definitionPattern = /(?:Definition|Definition:)\s*([^\n]+(?:\n(?!Explanation|Example|Conclusion)[^\n]+)*)/i
    const examplePattern = /(?:Example|Example:)\s*([^\n]+(?:\n(?!Conclusion|Definition|Explanation)[^\n]+)*)/i
    
    // Check for Social Science structure (Background/Context, Key Points, Explanation, Conclusion)
    // Using RegExp constructor to avoid issues with forward slashes in regex literals
    const backgroundPattern = new RegExp('(?:Background|Context|Background/Context|Background / Context|Background/Context:)\\s*([^\\n]+(?:\\n(?!Key Points|Explanation|Conclusion)[^\\n]+)*)', 'i')
    const keyPointsPattern = /(?:Key Points|Key Points:)\s*([^\n]+(?:\n(?!Explanation|Conclusion|Background|Context)[^\n]+)*)/i
    
    // Try English structure first
    const introMatch = answerStr.match(englishPattern)
    const explMatch = answerStr.match(explanationPattern)
    const analMatch = answerStr.match(analysisPattern)
    const conclMatch = answerStr.match(conclusionPattern)
    
    if (introMatch || explMatch || analMatch || conclMatch) {
      return {
        introduction: introMatch ? introMatch[1].trim() : null,
        explanation: explMatch ? explMatch[1].trim() : null,
        analysis: analMatch ? analMatch[1].trim() : null,
        conclusion: conclMatch ? conclMatch[1].trim() : null,
        type: 'english'
      }
    }
    
    // Try Science structure
    const defMatch = answerStr.match(definitionPattern)
    const explMatch2 = answerStr.match(explanationPattern)
    const exMatch = answerStr.match(examplePattern)
    const conclMatch2 = answerStr.match(conclusionPattern)
    
    if (defMatch || explMatch2 || exMatch || conclMatch2) {
      return {
        definition: defMatch ? defMatch[1].trim() : null,
        explanation: explMatch2 ? explMatch2[1].trim() : null,
        example: exMatch ? exMatch[1].trim() : null,
        conclusion: conclMatch2 ? conclMatch2[1].trim() : null,
        type: 'science'
      }
    }
    
    // Try Social Science structure
    const bgMatch = answerStr.match(backgroundPattern)
    const kpMatch = answerStr.match(keyPointsPattern)
    const explMatch3 = answerStr.match(explanationPattern)
    const conclMatch3 = answerStr.match(conclusionPattern)
    
    if (bgMatch || kpMatch || explMatch3 || conclMatch3) {
      return {
        background: bgMatch ? bgMatch[1].trim() : null,
        key_points: kpMatch ? kpMatch[1].trim() : null,
        explanation: explMatch3 ? explMatch3[1].trim() : null,
        conclusion: conclMatch3 ? conclMatch3[1].trim() : null,
        type: 'social_science'
      }
    }
    
    return null
  }
  
  // Helper function to render answer based on marks and subject (STRICT UI LOGIC)
  const renderAnswer = (answer, marks) => {
    if (!answer) return null
    
    // If answer is a string (1-2 marks, or fallback)
    if (typeof answer === 'string') {
      // Try to parse as structured answer with embedded headings
      const parsed = parseStringAnswer(answer)
      if (parsed) {
        // Re-render as structured object
        return renderAnswer(parsed, marks)
      }
      
      // If not structured, render as plain text/LaTeX
      if (marks === 1 || marks === 2) {
        // 1-2 marks: InlineMath
        return renderLatexInText(answer)
      } else if (marks === 3) {
        // 3 marks: Brief explanation with example - render as formatted text
        return <div className="whitespace-pre-wrap text-gray-800">{answer}</div>
      } else if (marks === 5) {
        // 5 marks: BlockMath
        const latex = extractLatex(answer)
        if (latex) {
          return <BlockMath math={latex} />
        }
        return renderLatexInText(answer)
      } else if (marks === 10) {
        // 10 marks: BlockMath (for main content)
        const latex = extractLatex(answer)
        if (latex) {
          return <BlockMath math={latex} />
        }
        // For 10 marks, if it's a long string, render as paragraphs
        return <div className="whitespace-pre-wrap text-gray-800">{answer}</div>
      } else {
        // Fallback: render as LaTeX
        return renderLatexInText(answer)
      }
    }
    
    // If answer is an object (5+ marks structured format)
    if (typeof answer === 'object' && answer !== null) {
      // Check if it's English/Literature style answer (Introduction, Explanation, Analysis, Conclusion)
      if (answer.introduction || answer.explanation || answer.analysis || answer.conclusion) {
        return (
          <div className="space-y-2 md:space-y-4">
            {answer.introduction && (
              <div className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">Introduction:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.introduction}</div>
              </div>
            )}
            {answer.explanation && (
              <div className="border-l-4 border-purple-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-xs md:text-base block mb-1">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.explanation}</div>
              </div>
            )}
            {answer.analysis && (
              <div className="border-l-4 border-orange-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-xs md:text-base block mb-1">Analysis:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.analysis}</div>
              </div>
            )}
            {answer.conclusion && (
              <div className="border-l-4 border-green-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-xs md:text-base block mb-1">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Check if it's Science style answer (Definition, Explanation, Example, Conclusion)
      if (answer.definition && (answer.explanation || answer.example || answer.conclusion)) {
        return (
          <div className="space-y-2 md:space-y-4">
            {answer.definition && (
              <div className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">Definition:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.definition}</div>
              </div>
            )}
            {answer.explanation && (
              <div className="border-l-4 border-purple-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-xs md:text-base block mb-1">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.explanation}</div>
              </div>
            )}
            {answer.example && (
              <div className="border-l-4 border-orange-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-xs md:text-base block mb-1">Example:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.example}</div>
              </div>
            )}
            {answer.conclusion && (
              <div className="border-l-4 border-green-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-xs md:text-base block mb-1">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{answer.conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Check if it's Social Science style answer (Background, Key Points, Explanation, Conclusion)
      // Handle both formats: lowercase/underscore (background, context, key_points) and capitalized/spaced (Background/Context, Key Points)
      const backgroundContext = answer.background || answer.context || answer["Background/Context"] || answer["Background"] || answer["Context"]
      const keyPoints = answer.key_points || answer["Key Points"] || answer["key_points"] || answer["keyPoints"]
      const explanation = answer.explanation || answer["Explanation"]
      const conclusion = answer.conclusion || answer["Conclusion"]
      
      if (backgroundContext || keyPoints) {
        return (
          <div className="space-y-2 md:space-y-4">
            {backgroundContext && (
              <div className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">Background / Context:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{backgroundContext}</div>
              </div>
            )}
            {keyPoints && (
              <div className="border-l-4 border-purple-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-xs md:text-base block mb-1">Key Points:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm">
                  {Array.isArray(keyPoints) ? (
                    <ol className="list-decimal list-inside space-y-1 ml-2 md:ml-4">
                      {keyPoints.map((point, i) => (
                        <li key={i} className="break-words">{point}</li>
                      ))}
                    </ol>
                  ) : (
                    <div className="break-words whitespace-pre-line">{keyPoints}</div>
                  )}
                </div>
              </div>
            )}
            {explanation && (
              <div className="border-l-4 border-orange-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-xs md:text-base block mb-1">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{explanation}</div>
              </div>
            )}
            {conclusion && (
              <div className="border-l-4 border-green-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-xs md:text-base block mb-1">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Math-style answer (Given, Formula, Steps, etc.)
      if (marks === 5) {
        // 5 marks: BlockMath
        return (
          <div className="space-y-2 md:space-y-3">
            {answer.given && (
              <div className="text-xs md:text-sm">
                <span className="font-semibold">Given: </span>
                <InlineMath math={extractLatex(answer.given)} />
              </div>
            )}
            {answer.formula && (
              <div className="text-xs md:text-sm">
                <span className="font-semibold">Formula: </span>
                <BlockMath math={extractLatex(answer.formula)} />
              </div>
            )}
            {answer.steps && Array.isArray(answer.steps) && (
              <div className="mt-2">
                <span className="font-semibold text-xs md:text-sm">Steps:</span>
                <ol className="list-decimal list-inside mt-1 space-y-2 ml-2 md:ml-4">
                  {answer.steps.map((step, i) => (
                    <li key={i} className="text-xs md:text-sm">
                      <BlockMath math={extractLatex(step)} />
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {answer.final && (
              <div className="mt-2 text-xs md:text-sm">
                <span className="font-semibold">Final Answer: </span>
                <BlockMath math={extractLatex(answer.final)} />
              </div>
            )}
          </div>
        )
      } else if (marks === 10) {
        // 10 marks: Check if it's board-style format (post-processed) or original format
        if (answer.substitution !== undefined || answer.calculation !== undefined || answer.final_answer !== undefined) {
          // Board-style format: Given, Formula, Substitution, Calculation, Final Answer
          return (
            <div className="space-y-2 md:space-y-3 mt-2">
              {answer.given && (
                <div className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                  <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">Given:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-xs md:text-sm break-words">{answer.given}</div>
                </div>
              )}
              {answer.formula && (
                <div className="border-l-4 border-purple-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-purple-50/30">
                  <span className="font-semibold text-purple-700 text-xs md:text-base block mb-1">Formula:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-xs md:text-sm break-words">{answer.formula}</div>
                </div>
              )}
              {answer.substitution && (
                <div className="border-l-4 border-orange-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-orange-50/30">
                  <span className="font-semibold text-orange-700 text-xs md:text-base block mb-1">Substitution:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-xs md:text-sm break-words">{answer.substitution}</div>
                </div>
              )}
              {answer.calculation && (
                <div className="border-l-4 border-green-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-green-50/30">
                  <span className="font-semibold text-green-700 text-xs md:text-base block mb-1">Calculation:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-xs md:text-sm break-words">{answer.calculation}</div>
                </div>
              )}
              {answer.final_answer && (
                <div className="mt-2 md:mt-3 p-2 md:p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                  <span className="font-bold text-green-800 text-xs md:text-base break-words">{answer.final_answer}</span>
                </div>
              )}
            </div>
          )
        }
        
        // Original structured format (for non-post-processed answers)
        return (
          <div className="space-y-3">
            {answer.given && (
              <div>
                <span className="font-semibold">Given: </span>
                <BlockMath math={extractLatex(answer.given)} />
              </div>
            )}
            {answer.definition && (
              <div>
                <span className="font-semibold">Definition: </span>
                <BlockMath math={extractLatex(answer.definition)} />
              </div>
            )}
            {answer.formula && (
              <div>
                <span className="font-semibold">Formula/Theorem: </span>
                <BlockMath math={extractLatex(answer.formula)} />
              </div>
            )}
            {answer.coefficients && (
              <div>
                <span className="font-semibold">Coefficients: </span>
                <InlineMath math={extractLatex(answer.coefficients)} />
              </div>
            )}
            {answer.steps && Array.isArray(answer.steps) && (
              <div className="mt-3">
                <span className="font-semibold">Step-by-step Working:</span>
                <ol className="list-decimal list-inside mt-2 space-y-2 ml-4">
                  {answer.steps.map((step, i) => (
                    <li key={i} className="text-base">
                      <BlockMath math={extractLatex(step)} />
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {answer.function_values && Array.isArray(answer.function_values) && answer.function_values.length > 0 && (
              <div className="mt-3">
                <span className="font-semibold">Function Values:</span>
                <ul className="list-disc list-inside mt-2 space-y-2 ml-4">
                  {answer.function_values.map((value, i) => (
                    <li key={i} className="text-base">
                      <BlockMath math={extractLatex(value)} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {answer.final && (
              <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded">
                <span className="font-semibold">Final Conclusion: </span>
                <BlockMath math={extractLatex(answer.final)} />
              </div>
            )}
          </div>
        )
      } else {
        // Other marks (3, etc.): Use BlockMath
        return (
          <div className="space-y-2">
            {answer.given && (
              <div>
                <span className="font-semibold">Given: </span>
                {renderLatexInText(answer.given)}
              </div>
            )}
            {answer.formula && (
              <div>
                <span className="font-semibold">Formula: </span>
                <BlockMath math={extractLatex(answer.formula)} />
              </div>
            )}
            {answer.steps && Array.isArray(answer.steps) && (
              <div className="mt-2">
                <span className="font-semibold">Steps:</span>
                <ol className="list-decimal list-inside mt-1 space-y-1 ml-4">
                  {answer.steps.map((step, i) => (
                    <li key={i} className="text-sm">
                      <BlockMath math={extractLatex(step)} />
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {answer.final && (
              <div className="mt-2">
                <span className="font-semibold">Final Answer: </span>
                <BlockMath math={extractLatex(answer.final)} />
              </div>
            )}
          </div>
        )
      }
      
      // Fallback: If object doesn't match any pattern, try to render it generically
      // This handles cases where the structure is slightly different
      const hasAnyContent = Object.keys(answer).some(key => {
        const val = answer[key]
        return val && (
          (typeof val === 'string' && val.trim() !== '') ||
          (Array.isArray(val) && val.length > 0) ||
          (typeof val === 'object' && val !== null && Object.keys(val).length > 0)
        )
      })
      
      if (hasAnyContent) {
        // Render as a generic structured answer
        return (
          <div className="space-y-2 md:space-y-3">
            {Object.entries(answer).map(([key, value]) => {
              if (!value || (typeof value === 'string' && value.trim() === '') || 
                  (Array.isArray(value) && value.length === 0)) {
                return null
              }
              
              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
              
              if (Array.isArray(value)) {
                return (
                  <div key={key} className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                    <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">{displayKey}:</span>
                    <ol className="list-decimal list-inside space-y-1 ml-2 md:ml-4 mt-1">
                      {value.map((item, i) => (
                        <li key={i} className="text-gray-800 text-xs md:text-sm break-words">{String(item)}</li>
                      ))}
                    </ol>
                  </div>
                )
              } else if (typeof value === 'object' && value !== null) {
                return (
                  <div key={key} className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                    <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">{displayKey}:</span>
                    <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">
                      {JSON.stringify(value, null, 2)}
                    </div>
                  </div>
                )
              } else {
                return (
                  <div key={key} className="border-l-4 border-blue-500 pl-2 md:pl-3 py-1.5 md:py-2 bg-blue-50/30">
                    <span className="font-semibold text-blue-700 text-xs md:text-base block mb-1">{displayKey}:</span>
                    <div className="mt-1 text-gray-800 whitespace-pre-wrap text-xs md:text-sm break-words">{String(value)}</div>
                  </div>
                )
              }
            })}
          </div>
        )
      }
    }
    
    // Final fallback: convert to string
    return <div className="whitespace-pre-wrap text-gray-800">{String(answer)}</div>
  }
  
  // Update settings when selectedUpload changes
  useEffect(() => {
    const partIds = selectedUpload?.selectedPartIds || null
    const partCount = partIds ? partIds.length : 0
    // Reset manual flag when parts selection changes (new selection = new default)
    if (partCount > 0) {
      setIsNumQuestionsManuallySet(false)
    }
    setSettings(prev => ({
      ...prev,
      upload_id: partIds ? null : (selectedUpload?.id || ''),
      part_ids: partIds || null,
      // Auto-update num_questions when parts selection changes (reset to default)
      num_questions: partCount > 0 
        ? calculateDefaultQuestions(partCount, prev.marks, isMobile)
        : (partCount === 0
          ? (isPremium ? 10 : 3)
          : prev.num_questions)
    }))
    // Always reset generation complete when selection changes (allows re-generation from same or different content)
    setGenerationComplete(false)
    setResult(null)
    setEditedQuestions([])
  }, [selectedUpload, isPremium])
  
  // Update num_questions when marks pattern changes (if parts are selected) - only if not manually set
  useEffect(() => {
    if (selectedPartIds && selectedPartIds.length > 0 && !isNumQuestionsManuallySet) {
      const calculated = calculateDefaultQuestions(selectedPartIds.length, settings.marks)
      setSettings(prev => ({
        ...prev,
        num_questions: calculated
      }))
    }
  }, [settings.marks, selectedPartIds, isNumQuestionsManuallySet])

  // Update output_format when premium status changes (only reset if premium is lost)
  useEffect(() => {
    if (!isPremium && (settings.output_format === 'questions_answers' || settings.output_format === 'answers_only')) {
      setSettings(prev => ({
        ...prev,
        output_format: 'questions_only',
        include_answers: false
      }))
    }
  }, [isPremium])

  // Auto-enforce question type based on marks
  useEffect(() => {
    const derived = deriveTypeFromMarks(settings.marks)
    if (settings.qna_type !== derived) {
      setSettings(prev => ({ ...prev, qna_type: derived }))
    }
  }, [settings.marks])

  // Cancel generation handler
  const cancelGeneration = () => {
    console.log('🛑 Cancelling generation...')
    
    // Abort the request FIRST - this is critical
    if (generateAbortController) {
      console.log('🛑 Aborting request...')
      generateAbortController.abort()
    }
    
    // Clear rotating interval immediately
    if (window.generateRotateInterval) {
      clearInterval(window.generateRotateInterval)
      window.generateRotateInterval = null
    }
    
    // Dismiss toast immediately
    if (generateToastId) {
      toast.dismiss(generateToastId)
      setGenerateToastId(null)
    }
    
    // Reset state immediately - this stops all UI updates
    setGenerating(false)
    setGenerateAbortController(null)
    
    // Show cancellation message
    toast.error('❌ Generation cancelled', { duration: 2000 })
  }


  const handleGenerate = async () => {
    // Prevent multiple simultaneous generations
    if (generating) {
      toast.error('⏳ Generation is already in progress. Please wait...', { duration: 2000 })
      return
    }

    // Check if multi-select mode or single upload mode
    if (!settings.upload_id && !settings.part_ids) {
      toast.error('Please select an upload or parts first')
      return
    }
    
    if (settings.part_ids && settings.part_ids.length === 0) {
      toast.error('Please select at least one part')
      return
    }

    // Create AbortController for cancellation
    const abortController = new AbortController()
    setGenerateAbortController(abortController)

    setGenerating(true)
    
    // Get rotating messages for generation
    const partCount = settings.part_ids?.length || 0
    const generatingMessages = getRotatingMessages('generating', { partCount })
    let currentMessageIndex = 0
    
    // Show generating animation with cancel button and rotating messages
    const generatingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>{generatingMessages[currentMessageIndex]}</span>
          <button
            onClick={() => {
              toast.dismiss(t.id)
              cancelGeneration()
            }}
            className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      ),
      {
        duration: Infinity,
        id: 'generate-toast'
      }
    )
    setGenerateToastId(generatingToast)
    
    // Start rotating messages every 20 seconds
    const rotateInterval = setInterval(() => {
      currentMessageIndex = (currentMessageIndex + 1) % generatingMessages.length
      toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>{generatingMessages[currentMessageIndex]}</span>
            <button
              onClick={() => {
                toast.dismiss(t.id)
                cancelGeneration()
              }}
              className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        ),
        {
          id: 'generate-toast',
          duration: Infinity
        }
      )
    }, 20000)
    
    // Store interval for cleanup
    if (!window.generateRotateInterval) {
      window.generateRotateInterval = rotateInterval
    }
    
    try {
      // Normalize marks → type
      const normalizedType = deriveTypeFromMarks(settings.marks)

      // Get subject from selected upload or use default
      const uploadSubject = selectedUpload?.subject || 'general'
      
      // Create default distribution pattern if parts are selected
      let customDistribution = null
      if (settings.part_ids && settings.part_ids.length > 0) {
        const partCount = settings.part_ids.length
        
        if (settings.marks === 'mixed') {
          // For mixed pattern: use user's manual input if set, otherwise calculate default
          const defaultTotal = 16 * partCount  // Default: 16 questions per part
          const totalQuestions = isNumQuestionsManuallySet 
            ? settings.num_questions  // Use user's manual input
            : defaultTotal  // Use calculated default
          
          // Distribute the total questions proportionally across marks
          // Pattern: 1 mark (6) + 2 marks (4) + 3 marks (3) + 5 marks (2) + 10 marks (1) = 16 per part
          const totalPerPart = 16
          const expectedTotal = totalPerPart * partCount
          
          // Calculate base counts per part
          // For mobile: exclude 10-mark questions (15 questions per part instead of 16)
          // For desktop: include all marks (16 questions per part)
          const questionsPerPart = isMobile ? 15 : 16
          const adjustedExpectedTotal = questionsPerPart * partCount
          const adjustedTotalQuestions = isNumQuestionsManuallySet 
            ? settings.num_questions 
            : (isMobile ? 15 * partCount : defaultTotal)
          
          const baseCounts = {
            1: 6,   // MCQ
            2: 4,   // Short
            3: 3,   // Descriptive
            5: 2,   // Descriptive
            10: isMobile ? 0 : 1   // Descriptive - EXCLUDED on mobile
          }
          
          // Calculate proportional distribution
          const scaleFactor = adjustedTotalQuestions / adjustedExpectedTotal
          
          // Calculate counts ensuring minimum of 1 for each type (if totalQuestions allows)
          // Skip 10 marks on mobile
          let counts = {
            1: Math.max(1, Math.round(baseCounts[1] * partCount * scaleFactor)),
            2: Math.max(1, Math.round(baseCounts[2] * partCount * scaleFactor)),
            3: Math.max(1, Math.round(baseCounts[3] * partCount * scaleFactor)),
            5: Math.max(1, Math.round(baseCounts[5] * partCount * scaleFactor)),
            10: isMobile ? 0 : Math.max(1, Math.round(baseCounts[10] * partCount * scaleFactor))
          }
          
          // If total is too small, prioritize higher marks (3, 5, 10) over lower marks
          let currentTotal = Object.values(counts).reduce((sum, count) => sum + count, 0)
          if (currentTotal > totalQuestions) {
            // Scale down proportionally, but ensure at least 1 of each if possible
            const excess = currentTotal - totalQuestions
            // Reduce from lower marks first
            if (counts[1] > 1 && excess > 0) {
              const reduce = Math.min(counts[1] - 1, excess)
              counts[1] -= reduce
              currentTotal -= reduce
            }
            if (counts[2] > 1 && currentTotal > totalQuestions) {
              const reduce = Math.min(counts[2] - 1, currentTotal - totalQuestions)
              counts[2] -= reduce
              currentTotal -= reduce
            }
            if (counts[3] > 1 && currentTotal > totalQuestions) {
              const reduce = Math.min(counts[3] - 1, currentTotal - totalQuestions)
              counts[3] -= reduce
              currentTotal -= reduce
            }
            if (counts[5] > 1 && currentTotal > totalQuestions) {
              const reduce = Math.min(counts[5] - 1, currentTotal - totalQuestions)
              counts[5] -= reduce
              currentTotal -= reduce
            }
            if (counts[10] > 1 && currentTotal > totalQuestions) {
              const reduce = Math.min(counts[10] - 1, currentTotal - totalQuestions)
              counts[10] -= reduce
              currentTotal -= reduce
            }
          }
          
          // Build distribution array, filtering out zero counts
          // On mobile: exclude 10-mark questions entirely
          customDistribution = [
            { marks: 1, count: counts[1], type: 'mcq' },
            { marks: 2, count: counts[2], type: 'short' },
            { marks: 3, count: counts[3], type: 'descriptive' },
            { marks: 5, count: counts[5], type: 'descriptive' },
            ...(isMobile ? [] : [{ marks: 10, count: counts[10], type: 'descriptive' }]) // Only include 10 marks on desktop
          ].filter(item => item.count > 0) // Remove zero counts
          
          // Adjust to match exact total (add/subtract from largest count item)
          // Use adjusted total for mobile (15 per part) or original total for desktop
          const targetTotal = isMobile ? adjustedTotalQuestions : totalQuestions
          currentTotal = customDistribution.reduce((sum, item) => sum + item.count, 0)
          if (currentTotal !== targetTotal && customDistribution.length > 0) {
            const diff = targetTotal - currentTotal
            // Find the item with the largest count to adjust
            const largestIndex = customDistribution.reduce((maxIdx, item, idx) => 
              item.count > customDistribution[maxIdx].count ? idx : maxIdx, 0
            )
            customDistribution[largestIndex].count += diff
            // Ensure count doesn't go negative or zero
            if (customDistribution[largestIndex].count <= 0) {
              // Remove this item and redistribute
              customDistribution.splice(largestIndex, 1)
              // Recalculate without this item
              const newTotal = customDistribution.reduce((sum, item) => sum + item.count, 0)
              if (newTotal < totalQuestions && customDistribution.length > 0) {
                customDistribution[0].count += (totalQuestions - newTotal)
              }
            }
          }
          
          // Final filter to ensure no zero counts
          customDistribution = customDistribution.filter(item => item.count > 0)
        } else {
          // Single marks pattern: use user's manual input if set, otherwise calculate
          const marks = parseInt(settings.marks, 10)
          
          // Use manual input if user has set it, otherwise calculate default
          const totalQuestions = isNumQuestionsManuallySet 
            ? settings.num_questions  // Use user's manual input
            : calculateDefaultQuestions(partCount, settings.marks)  // Use calculated default
          
          let questionType = 'descriptive'
          if (marks === 1) {
            questionType = 'mcq'
          } else if (marks === 2) {
            questionType = 'short'
          }
          
          customDistribution = [
            { marks: marks, count: totalQuestions, type: questionType }
          ]
        }
      }
      
      const requestData = {
        ...settings,
        qna_type: normalizedType,
        subject: uploadSubject,  // Pass subject from upload
        // Remove upload_id if using part_ids (multi-select mode)
        ...(settings.part_ids ? { upload_id: null } : { part_ids: null }),
        // Add custom distribution if parts are selected
        ...(customDistribution ? { custom_distribution: customDistribution } : {})
      }
      
      // Debug: Log distribution for troubleshooting
      if (customDistribution) {
        console.log('📊 Custom Distribution being sent:', customDistribution)
        console.log('📊 Total questions from distribution:', customDistribution.reduce((sum, item) => sum + item.count, 0))
        console.log('📊 Distribution breakdown:', customDistribution.map(item => `${item.marks} marks (${item.type}): ${item.count} questions`).join(', '))
      }
      
      // Update toast to show processing with cancel button
      toast.dismiss(generatingToast)
      const processingToast = toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>
              {settings.part_ids 
                ? `🤖 AI is creating questions from ${settings.part_ids.length} selected parts... Please wait`
                : '🤖 AI is creating your questions... Please wait'}
            </span>
            <button
              onClick={() => {
                toast.dismiss(t.id)
                cancelGeneration()
              }}
              className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        ),
        {
          duration: Infinity,
          id: 'generate-toast'
        }
      )
      setGenerateToastId(processingToast)
      
      // Check if cancelled before making request
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before sending')
        return
      }
      
      const response = await axios.post('/api/qna/generate', requestData, {
        signal: abortController.signal,
        timeout: 0 // No timeout, rely on abort signal
      })
      
      // Check if cancelled immediately after request
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled after response')
        return
      }
      
      // Check again before processing response
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before processing')
        return
      }
      
      toast.dismiss(processingToast)
      toast.dismiss() // clear any prior error/success toasts
      
      // Final check before setting result
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before setting result')
        return
      }
      
      // Debug: Log full response structure
      console.log('📦 Full Response Data:', {
        hasData: !!response.data,
        hasQnaJson: !!response.data?.qna_json,
        hasQuestions: !!response.data?.qna_json?.questions,
        questionCount: response.data?.qna_json?.questions?.length || 0,
        isMobile: isMobile,
        responseStructure: Object.keys(response.data || {}),
        qnaJsonStructure: response.data?.qna_json ? Object.keys(response.data.qna_json) : []
      })
      
      setResult(response.data)
      const questionsArray = response.data?.qna_json?.questions || []
      setEditedQuestions(questionsArray)
      
      // Debug: Log answer data to console
      if (questionsArray.length > 0) {
        console.log('📊 Generated Questions with Answers:', questionsArray.map((q, i) => ({
          questionNum: i + 1,
          question: q.question?.substring(0, 50),
          marks: q.marks,
          hasCorrectAnswer: !!q.correct_answer,
          hasAnswer: !!q.answer,
          correctAnswerType: typeof q.correct_answer,
          correctAnswerPreview: q.correct_answer ? (typeof q.correct_answer === 'string' ? q.correct_answer.substring(0, 100) : JSON.stringify(q.correct_answer).substring(0, 100)) : 'MISSING',
          answerKeys: typeof q.correct_answer === 'object' && q.correct_answer !== null ? Object.keys(q.correct_answer) : 'N/A'
        })))
        console.log('✅ Result state set. Questions count:', questionsArray.length, 'isMobile:', isMobile)
      } else {
        console.warn('⚠️ No questions in response!', {
          responseData: response.data,
          qnaJson: response.data?.qna_json,
          questions: response.data?.qna_json?.questions
        })
      }
      
      // Disable generate button after successful generation
      // User must upload new content or refresh page to generate again
      setGenerationComplete(true)
      
      // Check if cancelled before showing messages
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before showing messages')
        return
      }
      
      // Check if fewer questions were generated than requested
      const questions = response.data?.qna_json?.questions || []
      const actualCount = response.data?.qna_json?.actual_question_count ?? questions.length
      const requestedCount = response.data?.qna_json?.requested_question_count ?? settings.num_questions
      
      // Refresh user data to update quota counts after generation (only if not cancelled)
      if (!abortController.signal.aborted) {
        try {
          if (fetchUser) {
            await fetchUser()
          }
          // Call callback to refresh profile data if provided
          if (onGenerationComplete && !abortController.signal.aborted) {
            onGenerationComplete()
          }
        } catch (refreshError) {
          console.warn('Failed to refresh user data after generation:', refreshError)
          // Don't fail the generation if refresh fails
        }
      }
      
      // Check if cancelled before showing any messages
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before showing success messages')
        return
      }
      
      // Debug: Log questions and answers
      console.log('📋 Generated questions:', actualCount)
      questions.forEach((q, idx) => {
        console.log(`Q${idx + 1} (${q.marks} marks):`, {
          has_correct_answer: !!q.correct_answer,
          has_answer: !!q.answer,
          correct_answer_type: typeof q.correct_answer,
          correct_answer_preview: q.correct_answer ? (typeof q.correct_answer === 'string' ? q.correct_answer.substring(0, 50) : 'object') : 'missing'
        })
      })
      
      // Show popup if fewer questions were generated than requested
      if (actualCount < requestedCount && !abortController.signal.aborted) {
        toast(
          `For better accuracy, the system generated ${actualCount} question${actualCount !== 1 ? 's' : ''} instead of the requested ${requestedCount}, based on the depth of the selected content.`,
          {
            duration: 6000,
            icon: 'ℹ️',
            style: {
              maxWidth: '500px',
              wordBreak: 'break-word',
              fontSize: '14px',
              padding: '16px',
              backgroundColor: '#dbeafe',
              color: '#1e40af',
              border: '2px solid #3b82f6',
            },
            position: 'top-center'
          }
        )
      }
      
      // Final check before showing success message
      if (abortController.signal.aborted) {
        console.log('🛑 Request cancelled before showing success')
        return
      }
      
      // For free users, show only preview
      if (!isPremium) {
        toast.success('✅ Preview generated! Upgrade for full access.', { duration: 3000 })
      } else {
        toast.success('✅ Q/A generated successfully!', { duration: 3000 })
      }
    } catch (error) {
      // Check if it was cancelled
      if (axios.isCancel(error) || abortController.signal.aborted) {
        console.log('🛑 Generation cancelled (caught in catch)')
        // Already handled in cancelGeneration, just clean up
        toast.dismiss()
        return
      }
      
      // Only show error if not cancelled
      if (!abortController.signal.aborted) {
        toast.dismiss()
        const detail = error?.response?.data?.detail || error?.response?.data || error?.message || 'Generation failed'
        console.error('Generation failed:', {
          detail,
          status: error?.response?.status,
          data: error?.response?.data
        })
        toast.error(typeof detail === 'string' ? detail : 'Generation failed')
      }
    } finally {
      // Always cleanup intervals
      if (window.generateRotateInterval) {
        clearInterval(window.generateRotateInterval)
        window.generateRotateInterval = null
      }
      
      // Reset state - but only if not already reset by cancelGeneration
      // If cancelled, cancelGeneration already reset everything, so we just ensure cleanup
      if (!abortController.signal.aborted) {
        // Normal completion or error - reset state
        setGenerating(false)
        setGenerateAbortController(null)
        setGenerateToastId(null)
      } else {
        // Was cancelled - cancelGeneration already handled state, but ensure cleanup
        console.log('🛑 Finally block: Request was cancelled, cleanup already done')
        // Double-check state is reset
        if (generating) {
          setGenerating(false)
        }
        if (generateAbortController) {
          setGenerateAbortController(null)
        }
        if (generateToastId) {
          setGenerateToastId(null)
        }
      }
    }
  }

  const renderPreview = () => {
    // Debug: Log renderPreview call
    console.log('🎨 renderPreview called:', {
      hasResult: !!result,
      hasEditedQuestions: editedQuestions.length > 0,
      editedQuestionsCount: editedQuestions.length,
      resultQnaJson: !!result?.qna_json,
      resultQuestionsCount: result?.qna_json?.questions?.length || 0,
      isMobile: isMobile
    })
    
    if (!result) {
      console.log('❌ renderPreview: No result, returning null')
      return null
    }
    
    // Always prefer result.qna_json?.questions if editedQuestions is empty or doesn't match
    // This ensures questions are displayed even if editedQuestions state hasn't updated yet
    const resultQuestions = result.qna_json?.questions || []
    const questions = (editedQuestions.length > 0 && editedQuestions.length === resultQuestions.length) 
      ? editedQuestions 
      : resultQuestions
    const previewCount = isPremium ? questions.length : Math.min(3, questions.length)
    
    // Debug: Log questions being rendered
    console.log('🎨 Rendering preview:', {
      totalQuestions: questions.length,
      previewCount,
      isPremium,
      isMobile,
      questionsWithAnswers: questions.filter(q => q.correct_answer || q.answer).length,
      sampleQuestion: questions[0] ? {
        hasCorrectAnswer: !!questions[0].correct_answer,
        hasAnswer: !!questions[0].answer,
        correctAnswerType: typeof questions[0].correct_answer,
        correctAnswerKeys: typeof questions[0].correct_answer === 'object' && questions[0].correct_answer !== null ? Object.keys(questions[0].correct_answer) : 'N/A'
      } : 'No questions'
    })
    
    if (questions.length === 0) {
      console.warn('⚠️ renderPreview: No questions to render!', {
        editedQuestions,
        resultQnaJson: result.qna_json,
        resultQuestions: result.qna_json?.questions
      })
      return null
    }

    return (
      <div className="mt-4 md:mt-6 space-y-4 md:space-y-6">
        <h3 className="text-base md:text-lg font-semibold">Generated Questions</h3>
        
        {questions.slice(0, previewCount).map((q, idx) => (
          <div key={idx} className="border-2 border-gray-300 rounded-lg p-3 md:p-5 bg-white shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start gap-2 md:gap-3">
              <span className="font-bold text-blue-600 text-base md:text-lg flex-shrink-0">Q{idx + 1}.</span>
              <div className="flex-1 min-w-0">
                <div className="flex flex-col md:flex-row gap-2 md:gap-3 items-start mb-2">
                  <textarea
                    value={q.question || ''}
                    onChange={(e) => {
                      const updated = [...questions]
                      updated[idx] = { ...updated[idx], question: e.target.value }
                      setEditedQuestions(updated)
                    }}
                    className="flex-1 w-full border border-gray-300 rounded-md px-2 md:px-3 py-1.5 md:py-2 text-xs md:text-sm min-w-0"
                    rows={2}
                  />
                  <div className="flex flex-col md:flex-col items-start md:items-end gap-1 w-full md:w-auto">
                    <span className="inline-block px-2 py-1 text-[10px] md:text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                      {q.marks} mark{q.marks !== 1 ? 's' : ''}
                    </span>
                    <span className="text-[9px] md:text-[11px] text-gray-500">Auto-set type: {deriveTypeFromMarks(q.marks)}</span>
                    {q.source && (
                      <span className="text-[8px] md:text-[10px] text-gray-500 bg-gray-100 px-1.5 md:px-2 py-0.5 rounded mt-1 break-words">
                        📄 Part {q.source.part_number} {q.source.exact_page ? `(Page ${q.source.exact_page})` : (q.source.page_range || `Pages ${q.source.start_page}-${q.source.end_page}`)}
                      </span>
                    )}
                  </div>
                </div>

                {q.type === 'mcq' && q.options && (
                  <div className="mt-2 md:mt-3 space-y-1.5 md:space-y-2">
                    {q.options.map((opt, i) => {
                      const optionLabel = String.fromCharCode(65 + i)
                      return (
                        <div 
                          key={i} 
                          className="flex items-start gap-2 md:gap-3 p-1.5 md:p-2 border border-gray-200 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <span className="font-bold text-blue-600 min-w-[20px] md:min-w-[24px] text-xs md:text-sm">{optionLabel}.</span>
                          <span className="text-gray-700 flex-1 text-xs md:text-sm break-words">{opt}</span>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Always show answer section for premium users if answer exists */}
                {isPremium && (
                  <div className="mt-3 md:mt-4 p-3 md:p-4 bg-green-50 rounded-lg border-2 border-green-300">
                    <p className="text-xs md:text-sm font-semibold text-green-800 mb-2">✓ Correct Answer:</p>
                    <div className="text-green-700 font-medium text-xs md:text-sm">
                      {(() => {
                        const answer = q.correct_answer || q.answer
                        
                        // Debug: Log answer data for every question
                        const answerObj = q.correct_answer || q.answer
                        console.log(`🔍 Q${idx + 1} Answer Debug:`, {
                          hasCorrectAnswer: !!q.correct_answer,
                          hasAnswer: !!q.answer,
                          correctAnswerType: typeof q.correct_answer,
                          answerType: typeof q.answer,
                          correctAnswerValue: q.correct_answer,
                          answerValue: q.answer,
                          answerKeys: typeof answerObj === 'object' && answerObj !== null ? Object.keys(answerObj) : 'N/A',
                          answerValues: typeof answerObj === 'object' && answerObj !== null ? Object.entries(answerObj).map(([k, v]) => ({ key: k, value: v, type: typeof v, isEmpty: typeof v === 'string' ? v.trim() === '' : (Array.isArray(v) ? v.length === 0 : !v) })) : 'N/A',
                          fullQuestion: q,
                          answerStringified: typeof answerObj === 'object' && answerObj !== null ? JSON.stringify(answerObj, null, 2) : String(answerObj)
                        })
                        
                        // Debug logging for missing answers
                        if (!answer || answer === "N/A" || answer === "N/A - Answer not generated by AI") {
                          console.warn(`⚠️ Missing or invalid answer for Q${idx + 1} (${q.marks} marks):`, { 
                            answer, 
                            question: q.question?.substring(0, 50),
                            hasCorrectAnswer: !!q.correct_answer,
                            hasAnswer: !!q.answer,
                            correctAnswerType: typeof q.correct_answer,
                            answerType: typeof q.answer,
                            fullQuestionObject: q
                          })
                          return <span className="text-yellow-600 italic text-xs">Answer not generated. Please regenerate questions.</span>
                        }
                        if (typeof answer === 'object' && answer !== null) {
                          const keys = Object.keys(answer)
                          if (keys.length === 0) {
                            console.warn(`⚠️ Empty answer object for Q${idx + 1} (${q.marks} marks):`, q)
                            return <span className="text-yellow-600 italic text-xs">Answer object is empty. Please regenerate questions.</span>
                          }
                          // Check if all values are empty/null
                          const allEmpty = keys.every(key => {
                            const val = answer[key]
                            return !val || (typeof val === 'string' && val.trim() === '') || (Array.isArray(val) && val.length === 0)
                          })
                          if (allEmpty) {
                            console.warn(`⚠️ Answer object has all empty values for Q${idx + 1} (${q.marks} marks):`, { answer, keys })
                            return <span className="text-yellow-600 italic text-xs">Answer is empty. Please regenerate questions.</span>
                          }
                        }
                        if (typeof answer === 'string' && answer.trim() === '') {
                          console.warn(`⚠️ Empty string answer for Q${idx + 1} (${q.marks} marks):`, q)
                          return <span className="text-yellow-600 italic text-xs">Answer is empty. Please regenerate questions.</span>
                        }
                        // Try renderAnswer first (for structured objects with proper formatting)
                        let rendered = renderAnswer(answer, q.marks || 0)
                        
                        // If renderAnswer returns null or if answer is a string with structured content, try formatAnswer-style rendering
                        if (!rendered) {
                          // Fallback: If answer is a string that might contain structured content, try to format it
                          if (typeof answer === 'string' && answer.includes('Background/Context') || answer.includes('Key Points') || answer.includes('Explanation') || answer.includes('Conclusion')) {
                            // It's a formatted string - render it as-is with proper whitespace
                            rendered = <div className="whitespace-pre-wrap text-gray-800">{answer}</div>
                          } else if (typeof answer === 'object' && answer !== null) {
                            // Try to format as structured answer (like SavedSets does)
                            const parts = []
                            if (answer.background || answer.context) {
                              parts.push(`Background/Context: ${answer.background || answer.context}`)
                            }
                            if (answer.key_points) {
                              if (Array.isArray(answer.key_points)) {
                                parts.push(`Key Points:\n${answer.key_points.map((kp, i) => `${i + 1}. ${kp}`).join('\n')}`)
                              } else {
                                parts.push(`Key Points: ${answer.key_points}`)
                              }
                            }
                            if (answer.explanation) {
                              parts.push(`Explanation: ${answer.explanation}`)
                            }
                            if (answer.conclusion) {
                              parts.push(`Conclusion: ${answer.conclusion}`)
                            }
                            if (parts.length > 0) {
                              rendered = <div className="whitespace-pre-wrap text-gray-800">{parts.join('\n\n')}</div>
                            }
                          }
                        }
                        
                        if (!rendered) {
                          console.warn(`⚠️ renderAnswer returned null for Q${idx + 1} (${q.marks} marks):`, { 
                            answer, 
                            answerType: typeof answer,
                            marks: q.marks,
                            questionType: q.type,
                            answerKeys: typeof answer === 'object' && answer !== null ? Object.keys(answer) : 'N/A',
                            answerString: typeof answer === 'string' ? answer.substring(0, 200) : (typeof answer === 'object' ? JSON.stringify(answer).substring(0, 200) : 'N/A')
                          })
                          // Final fallback: Display answer as text/JSON
                          if (typeof answer === 'string' && answer.trim()) {
                            return <div className="whitespace-pre-wrap text-gray-800">{answer}</div>
                          } else if (typeof answer === 'object' && answer !== null) {
                            // Try to format structured answer one more time
                            const parts = []
                            if (answer.background || answer.context) parts.push(`Background/Context: ${answer.background || answer.context}`)
                            if (answer.key_points) {
                              if (Array.isArray(answer.key_points)) {
                                parts.push(`Key Points:\n${answer.key_points.map((kp, i) => `${i + 1}. ${kp}`).join('\n')}`)
                              } else {
                                parts.push(`Key Points: ${answer.key_points}`)
                              }
                            }
                            if (answer.explanation) parts.push(`Explanation: ${answer.explanation}`)
                            if (answer.conclusion) parts.push(`Conclusion: ${answer.conclusion}`)
                            if (answer.introduction) parts.push(`Introduction: ${answer.introduction}`)
                            if (answer.analysis) parts.push(`Analysis: ${answer.analysis}`)
                            if (answer.definition) parts.push(`Definition: ${answer.definition}`)
                            if (answer.example) parts.push(`Example: ${answer.example}`)
                            if (parts.length > 0) {
                              return <div className="whitespace-pre-wrap text-gray-800">{parts.join('\n\n')}</div>
                            }
                            // Last resort: show as JSON
                            return <div className="whitespace-pre-wrap text-gray-800 font-mono text-xs">{JSON.stringify(answer, null, 2)}</div>
                          }
                          return <span className="text-yellow-600 italic text-xs">Answer could not be rendered. Please regenerate questions.</span>
                        }
                        return rendered
                      })()}
                    </div>
                  </div>
                )}

                {q.marks && (
                  <div className="mt-2">
                    <span className="inline-block px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                      {q.marks} mark{q.marks !== 1 ? 's' : ''}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {!isPremium && questions.length > 3 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
            <p className="text-yellow-800 font-semibold">
              Upgrade to Premium to see all {questions.length} questions and answers
            </p>
          </div>
        )}

        {isPremium && (
          <div className="relative inline-flex mt-3 md:mt-4 w-full md:w-auto">
            <button
              onClick={() => downloadSet(result.id, 'pdf', 'questions_answers')}
              disabled={downloading}
              className="flex-1 md:flex-none px-3 md:px-4 py-2 bg-green-600 text-white rounded-l-lg md:rounded-l-lg rounded-r-lg md:rounded-r-none hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm md:text-base"
              title={downloading ? "Download in progress..." : "Download Q+A (PDF)"}
            >
              {downloading ? (
                <>
                  <svg className="animate-spin h-3 w-3 md:h-4 md:w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-xs md:text-sm">Downloading...</span>
                </>
              ) : (
                <span className="text-xs md:text-base">Download</span>
              )}
            </button>
            <button
              onClick={() => setShowDownloadMenu((prev) => !prev)}
              disabled={downloading}
              className="px-2 md:px-3 py-2 bg-green-600 text-white rounded-r-lg hover:bg-green-700 border-l border-green-500 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              title={downloading ? "Download in progress..." : "More formats"}
            >
              <svg className="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showDownloadMenu && !downloading && (
              <div className="absolute z-20 top-full left-0 mt-2 w-full md:w-72 max-h-64 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-xl">
                <div className="py-1">
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'pdf', 'questions_only') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Question (PDF)
                  </button>
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'pdf', 'questions_answers') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Q+A (PDF)
                  </button>
                  <div className="border-t border-gray-200 my-1" />
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'docx', 'questions_only') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Questions (DOCX)
                  </button>
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'docx', 'questions_answers') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Q+A (DOCX)
                  </button>
                  <div className="border-t border-gray-200 my-1" />
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'txt', 'questions_only') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Question (TXT)
                  </button>
                  <button
                    onClick={() => { setShowDownloadMenu(false); downloadSet(result.id, 'txt', 'questions_answers') }}
                    disabled={downloading}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Q+A (TXT)
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  // Cancel download handler
  const cancelDownload = () => {
    // Clear rotating interval
    if (window.downloadRotateInterval) {
      clearInterval(window.downloadRotateInterval)
      window.downloadRotateInterval = null
    }
    if (downloadAbortController) {
      downloadAbortController.abort()
      setDownloadAbortController(null)
    }
    if (downloadToastId) {
      toast.dismiss(downloadToastId)
      setDownloadToastId(null)
    }
    setDownloading(false)
    toast.error('❌ Download cancelled', { duration: 2000 })
  }

  const downloadSet = async (setId, format, outputFormat) => {
    // Prevent multiple simultaneous downloads
    if (downloading) {
      toast.error('⏳ A download is already in progress. Please wait...', { duration: 2000 })
      return
    }

    // Close download menu if open
    setShowDownloadMenu(false)

    // Create AbortController for cancellation
    const abortController = new AbortController()
    setDownloadAbortController(abortController)

    // Set downloading state to prevent multiple clicks
    setDownloading(true)
    
    const downloadMessages = getRotatingMessages('downloading')
    let downloadMessageIndex = 0
    
    // Show preparing message with cancel button and rotation
    const preparingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>{downloadMessages[downloadMessageIndex]}</span>
          <button
            onClick={() => {
              toast.dismiss(t.id)
              cancelDownload()
            }}
            className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      ),
      {
        duration: Infinity,
        id: 'download-toast'
      }
    )
    setDownloadToastId(preparingToast)
    
    // Start rotating messages every 20 seconds
    const downloadRotateInterval = setInterval(() => {
      downloadMessageIndex = (downloadMessageIndex + 1) % downloadMessages.length
      toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>{downloadMessages[downloadMessageIndex]}</span>
            <button
              onClick={() => {
                toast.dismiss(t.id)
                cancelDownload()
              }}
              className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        ),
        {
          id: 'download-toast',
          duration: Infinity
        }
      )
    }, 20000)
    
    // Store interval for cleanup
    window.downloadRotateInterval = downloadRotateInterval
    
    try {
      // Update to generating message (keep same rotation)
      toast.dismiss(preparingToast)
      const generatingToast = toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>{downloadMessages[downloadMessageIndex]}</span>
            <button
              onClick={() => {
                toast.dismiss(t.id)
                cancelDownload()
              }}
              className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        ),
        {
          duration: Infinity,
          id: 'download-toast'
        }
      )
      setDownloadToastId(generatingToast)
      
      let blobData = null

      // Try edited payload first (POST), then fallback to stored set (existing API)
      if (editedQuestions && editedQuestions.length) {
        const payload = {
          ...(result?.qna_json || {}),
          questions: editedQuestions
        }
        const url = `/api/qna/sets/${setId}/download?format=${format}&output_format=${outputFormat}`
        try {
          const resp = await axios.post(url, payload, { 
            responseType: 'blob',
            signal: abortController.signal
          })
          blobData = resp.data
        } catch (postErr) {
          if (axios.isCancel(postErr)) {
            // Download was cancelled
            return
          }
          console.warn('Edited download failed, falling back to stored set', postErr)
        }
      }

      if (!blobData && !abortController.signal.aborted) {
        const response = await axios.get(`/api/qna/sets/${setId}/download`, {
          params: { format, output_format: outputFormat },
          responseType: 'blob',
          signal: abortController.signal
        })
        blobData = response.data
      }
      
      // Check if cancelled before proceeding
      if (abortController.signal.aborted) {
        return
      }
      
      // Clear rotation before finalizing
      if (window.downloadRotateInterval) {
        clearInterval(window.downloadRotateInterval)
        window.downloadRotateInterval = null
      }
      
      toast.dismiss(generatingToast)
      
      // Show finalizing message
      const finalizingToast = toast.loading('📥 Finalizing download...', {
        duration: 2000
      })
      
      const blob = new Blob([blobData])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `questions_set_${setId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.dismiss(finalizingToast)
      toast.success('✅ Download started!', { duration: 3000 })
    } catch (error) {
      if (axios.isCancel(error)) {
        // Download was cancelled - already handled in cancelDownload
        return
      }
      // Clear rotation on error
      if (window.downloadRotateInterval) {
        clearInterval(window.downloadRotateInterval)
        window.downloadRotateInterval = null
      }
      toast.dismiss()
      toast.error('Download failed: ' + (error.response?.data?.detail || 'Unknown error'))
    } finally {
      // Always reset downloading state and cleanup
      if (window.downloadRotateInterval) {
        clearInterval(window.downloadRotateInterval)
        window.downloadRotateInterval = null
      }
      setDownloading(false)
      setDownloadAbortController(null)
      setDownloadToastId(null)
    }
  }

  return (
    <div>
      <h2 className="text-lg md:text-xl font-semibold mb-4 md:mb-6">Generate Q/A</h2>

      {/* Upload Selection or Multi-Select Info */}
      {selectedPartIds && selectedPartIds.length > 0 ? (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-green-600 font-semibold">✅ Multi-Select Mode</span>
          </div>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              Generating quality questions from <strong>{selectedPartIds.length} selected part{selectedPartIds.length > 1 ? 's' : ''}</strong>.
            </p>
            <div className="bg-white p-3 rounded border border-green-200">
              <p className="text-xs font-semibold text-gray-700 mb-1">📋 Recommended Distribution Pattern:</p>
              {settings.marks === 'mixed' ? (
                <>
                  <p className="text-xs text-gray-600 mb-2">
                    Per part (40 pages): 1 mark (6 MCQ) + 2 marks (4) + 3 marks (3) + 5 marks (2){isMobile ? '' : ' + 10 marks (1)'} = <strong>{isMobile ? '15' : '16'} questions</strong>
                    {isMobile && <span className="text-blue-600 ml-1 block mt-1">(10-mark questions excluded on mobile for better display)</span>}
                  </p>
                  <p className="text-xs text-gray-600">
                    Total for {selectedPartIds.length} part{selectedPartIds.length > 1 ? 's' : ''}: <strong className="text-green-700">{calculateDefaultQuestions(selectedPartIds.length, settings.marks, isMobile)} questions</strong>
                  </p>
                </>
              ) : (
                <>
                  <p className="text-xs text-gray-600 mb-2">
                    Per part (40 pages): <strong>{settings.marks} mark{settings.marks !== '1' ? 's' : ''} → {calculateDefaultQuestions(1, settings.marks, isMobile)} questions</strong>
                    {isMobile && settings.marks === '10' && <span className="text-blue-600 ml-1 block mt-1">(10-mark questions excluded on mobile)</span>}
                  </p>
                  <p className="text-xs text-gray-600">
                    Total for {selectedPartIds.length} part{selectedPartIds.length > 1 ? 's' : ''}: <strong className="text-green-700">{calculateDefaultQuestions(selectedPartIds.length, settings.marks, isMobile)} questions</strong>
                  </p>
                </>
              )}
            </div>
            <p className="text-xs text-gray-600 italic">
              Each generated question will show its source part and page range for easy reference.
            </p>
          </div>
          <button
            onClick={() => {
              // Clear multi-select mode
              onSelectUpload({ ...selectedUpload, selectedPartIds: null })
            }}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Clear selection
          </button>
        </div>
      ) : (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            Please select an upload from the <strong>Upload</strong> tab and click the <strong>Use</strong> button to generate questions.
          </p>
        </div>
      )}

      {/* Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Difficulty
          </label>
          <select
            value={settings.difficulty}
            onChange={(e) => setSettings({ ...settings, difficulty: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>

        <div>
          <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
            Question Type
          </label>
          <div className="flex items-center gap-2">
            <input
              value={deriveTypeFromMarks(settings.marks)}
              readOnly
              className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
            />
            <span className="text-xs text-gray-500">Auto-set from marks</span>
          </div>
        </div>

        <div>
          <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
            Number of Questions
          </label>
          <div className="relative group">
            <input
              type="number"
              min="1"
              max={selectedPartIds && selectedPartIds.length > 0 
                ? calculateDefaultQuestions(selectedPartIds.length, settings.marks) 
                : (isPremium ? 15 : 3)}
              value={settings.num_questions}
              onChange={(e) => {
                const inputValue = e.target.value
                // Allow user to type freely - store as string/number
                // Mark as manually set immediately when user starts typing
                setIsNumQuestionsManuallySet(true)
                
                // Allow empty string while typing
                if (inputValue === '') {
                  setSettings({ ...settings, num_questions: '' })
                  return
                }
                
                // Parse the value
                const numValue = parseInt(inputValue, 10)
                
                // If it's a valid number, use it
                if (!isNaN(numValue)) {
                  const max = selectedPartIds && selectedPartIds.length > 0 
                    ? calculateDefaultQuestions(selectedPartIds.length, settings.marks) 
                    : (isPremium ? 15 : 3)
                  
                  // Allow typing even if temporarily exceeds max (validate on blur)
                  if (numValue > max) {
                    // Still allow typing, but will validate on blur
                    setSettings({ ...settings, num_questions: numValue })
                  } else if (numValue < 1) {
                    // Still allow typing, but will validate on blur
                    setSettings({ ...settings, num_questions: numValue })
                  } else {
                    setSettings({ ...settings, num_questions: numValue })
                  }
                } else {
                  // If not a valid number, still allow typing (user might be in middle of typing)
                  setSettings({ ...settings, num_questions: inputValue })
                }
              }}
              onBlur={(e) => {
                // Validate and normalize on blur
                const inputValue = e.target.value
                if (inputValue === '' || isNaN(parseInt(inputValue, 10))) {
                  // If empty or invalid, set to minimum
                  const min = 1
                  setSettings({ ...settings, num_questions: min })
                  setIsNumQuestionsManuallySet(true)
                  return
                }
                
                const val = parseInt(inputValue, 10)
                const max = selectedPartIds && selectedPartIds.length > 0 
                  ? calculateDefaultQuestions(selectedPartIds.length, settings.marks) 
                  : (isPremium ? 15 : 3)
                
                if (val < 1) {
                  setSettings({ ...settings, num_questions: 1 })
                  setIsNumQuestionsManuallySet(true)
                } else if (val > max) {
                  setSettings({ ...settings, num_questions: max })
                  setIsNumQuestionsManuallySet(true)
                  toast.error(`Maximum ${max} questions allowed${selectedPartIds && selectedPartIds.length > 0 ? ` for ${selectedPartIds.length} part${selectedPartIds.length > 1 ? 's' : ''}` : ` for ${isPremium ? 'premium' : 'free'} users`}`)
                } else {
                  setSettings({ ...settings, num_questions: val })
                  setIsNumQuestionsManuallySet(true)
                }
              }}
              className="w-full px-4 py-2 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder={selectedPartIds && selectedPartIds.length > 0 
                ? `1-${calculateDefaultQuestions(selectedPartIds.length, settings.marks)}` 
                : `1-${isPremium ? 15 : 3}`}
            />
            {/* Hover tooltip showing max limit */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-[100]">
              <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl whitespace-nowrap relative">
                Max: {selectedPartIds && selectedPartIds.length > 0 
                  ? calculateDefaultQuestions(selectedPartIds.length, settings.marks) 
                  : (isPremium ? 15 : 3)} questions
                <div className="absolute left-1/2 -translate-x-1/2 -top-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
              </div>
            </div>
          </div>
          <p className="text-xs md:text-sm text-gray-500 mt-1">
            {selectedPartIds && selectedPartIds.length > 0 ? (
              <>
                {settings.marks === 'mixed' ? (
                  <>Recommended: <strong>{calculateDefaultQuestions(selectedPartIds.length, settings.marks)} questions</strong> for {selectedPartIds.length} part{selectedPartIds.length > 1 ? 's' : ''} (16 per part)</>
                ) : (
                  <>Recommended: <strong>{calculateDefaultQuestions(selectedPartIds.length, settings.marks)} questions</strong> for {selectedPartIds.length} part{selectedPartIds.length > 1 ? 's' : ''} ({calculateDefaultQuestions(1, settings.marks)} per part)</>
                )}
              </>
            ) : (
              <>Type any number from 1 to {isPremium ? 15 : 3} (hover input to see limit)</>
            )}
          </p>
        </div>

        <div>
          <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
            Marks Pattern
          </label>
          <select
            value={settings.marks}
            onChange={(e) => {
              const val = e.target.value
              const partCount = selectedPartIds ? selectedPartIds.length : 0
              setSettings(prev => ({
                ...prev,
                marks: val,
                qna_type: deriveTypeFromMarks(val),
                // Auto-update num_questions when marks pattern changes (if parts are selected)
                num_questions: partCount > 0 
                  ? calculateDefaultQuestions(partCount, val)
                  : prev.num_questions
              }))
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="1">1 mark</option>
            <option value="2">2 marks</option>
            <option value="3">3 marks</option>
            <option value="5">5 marks</option>
            <option value="10">10 marks</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>

        <div>
          <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
            Output Format
          </label>
          <select
            value={settings.output_format}
            onChange={(e) => {
              const newFormat = e.target.value
              
              // Check if free user is trying to access premium features
              if (!isPremium && (newFormat === 'questions_answers' || newFormat === 'answers_only')) {
                // Show premium notification with detailed message
                toast(
                  (t) => (
                    <div className="flex flex-col gap-2">
                      <p className="font-semibold text-amber-900 text-base">
                        ⭐ Premium Feature Available!
                      </p>
                      <p className="text-sm text-amber-800">
                        "Questions + Answers" and "Answers Only" are exclusive to Premium users.
                      </p>
                      <p className="text-sm font-medium text-amber-900 mt-2">
                        💳 Upgrade to Premium for just ₹599/month and unlock:
                      </p>
                      <ul className="text-xs text-amber-800 list-disc list-inside mt-1 space-y-1">
                        <li>Generate questions with answers</li>
                        <li>Download PDFs in multiple formats</li>
                        <li>Up to 15 questions per generation</li>
                        <li>All premium features</li>
                      </ul>
                      <p className="text-xs text-amber-700 mt-2 font-medium">
                        👆 Click "Show QR Code" in the banner above to pay and activate Premium!
                      </p>
                    </div>
                  ),
                  {
                    duration: 2500,
                    icon: '🔒',
                    style: {
                      background: '#fef3c7',
                      color: '#92400e',
                      border: '2px solid #f59e0b',
                      padding: '16px',
                      borderRadius: '8px',
                      maxWidth: '450px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    },
                  }
                )
                
                // Reset to questions_only for free users
                setSettings({ ...settings, output_format: 'questions_only' })
                return
              }
              
              // Allow change for premium users or if selecting questions_only
              setSettings({ ...settings, output_format: newFormat })
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="questions_only">Questions Only</option>
            <option value="questions_answers">
              Questions + Answers {!isPremium ? '🔒 Premium' : ''}
            </option>
            <option value="answers_only">
              Answers Only {!isPremium ? '🔒 Premium' : ''}
            </option>
          </select>
          {!isPremium && (
            <p className="text-xs text-amber-600 mt-1 font-medium">
              💡 Free users can only generate questions. Upgrade to Premium to get answers and downloads!
            </p>
          )}
          {isPremium && (
            <p className="text-xs text-gray-500 mt-1">
              Choose whether to include answers in the generated output
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
            Target Language
            <span className="text-xs md:text-xs text-gray-500 ml-2">
              (Output language)
            </span>
          </label>
          
          {/* Language Recommendation */}
          {settings.upload_id || (settings.part_ids && settings.part_ids.length > 0) ? (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-2">
                <span className="text-blue-600 text-lg">💡</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-800 mb-1">
                    Language Selection Recommendation
                  </p>
                  <p className="text-xs text-blue-700">
                    For accurate Q/A generation, select the same language as your uploaded content.
                    Matching the target language with your content language will ensure better question quality.
                  </p>
                </div>
              </div>
            </div>
          ) : null}
          
          <div className="relative">
            <select
              value={settings.target_language}
              onChange={(e) => setSettings({ ...settings, target_language: e.target.value })}
              className={`w-full px-4 py-2 border rounded-lg ${
                !settings.target_language
                  ? 'border-gray-300 bg-gray-50'
                  : 'border-gray-300'
              }`}
              required
            >
            <option value="">-- Select Language --</option>
            <option value="english">English</option>
            <option value="tamil">Tamil (தமிழ்)</option>
            <option value="hindi">Hindi (हिंदी)</option>
            <option value="arabic">Arabic (العربية)</option>
            <option value="spanish">Spanish (Español)</option>
            <option value="telugu">Telugu (తెలుగు)</option>
            <option value="kannada">Kannada (ಕನ್ನಡ)</option>
            <option value="malayalam">Malayalam (മലയാളം)</option>
            </select>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            All questions and answers will be generated in the selected language
          </p>
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={generating || (generationComplete && !settings.part_ids && !settings.upload_id) || (!settings.upload_id && !settings.part_ids) || !settings.target_language}
        className="w-full md:w-auto px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title={generationComplete && !settings.part_ids && !settings.upload_id ? 'Q/A already generated. Please select parts or upload new content to generate again.' : ''}
      >
        {generating ? 'Generating...' : (generationComplete && !settings.part_ids && !settings.upload_id ? 'Already Generated' : 'Generate Q/A')}
      </button>
      {generationComplete && !settings.part_ids && !settings.upload_id && (
        <p className="text-xs text-gray-500 mt-2 text-center">
          Q/A generated. Select parts or upload new content to generate again.
        </p>
      )}

      {/* Results */}
      {renderPreview()}
    </div>
  )
}

export default QnAGenerator
