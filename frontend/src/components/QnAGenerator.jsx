import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import { InlineMath, BlockMath } from 'react-katex'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
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

  const [useCustomDistribution, setUseCustomDistribution] = useState(false)
  const [customDistribution, setCustomDistribution] = useState([
    { marks: 2, count: 5, type: 'short' },
    { marks: 1, count: 10, type: 'mcq' }
  ])
  
  // Check if multi-select mode (selectedPartIds from PdfSplitParts)
  const selectedPartIds = selectedUpload?.selectedPartIds || null
  
  const [settings, setSettings] = useState({
    upload_id: selectedPartIds ? null : (selectedUpload?.id || ''),  // null if multi-select
    part_ids: selectedPartIds || null,  // Array of part IDs for multi-select
    difficulty: 'medium',
    qna_type: 'mixed',
    num_questions: isPremium ? 10 : 3,
    output_format: isPremium ? 'questions_answers' : 'questions_only',  // Free users get questions_only by default
    include_answers: isPremium,  // Free users can't include answers
    marks: 'mixed',
    target_language: 'english'
  })
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)
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
          <div className="space-y-4">
            {answer.introduction && (
              <div className="border-l-4 border-blue-500 pl-3 py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-base">Introduction:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.introduction}</div>
              </div>
            )}
            {answer.explanation && (
              <div className="border-l-4 border-purple-500 pl-3 py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-base">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.explanation}</div>
              </div>
            )}
            {answer.analysis && (
              <div className="border-l-4 border-orange-500 pl-3 py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-base">Analysis:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.analysis}</div>
              </div>
            )}
            {answer.conclusion && (
              <div className="border-l-4 border-green-500 pl-3 py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-base">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Check if it's Science style answer (Definition, Explanation, Example, Conclusion)
      if (answer.definition && (answer.explanation || answer.example || answer.conclusion)) {
        return (
          <div className="space-y-4">
            {answer.definition && (
              <div className="border-l-4 border-blue-500 pl-3 py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-base">Definition:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.definition}</div>
              </div>
            )}
            {answer.explanation && (
              <div className="border-l-4 border-purple-500 pl-3 py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-base">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.explanation}</div>
              </div>
            )}
            {answer.example && (
              <div className="border-l-4 border-orange-500 pl-3 py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-base">Example:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.example}</div>
              </div>
            )}
            {answer.conclusion && (
              <div className="border-l-4 border-green-500 pl-3 py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-base">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Check if it's Social Science style answer (Background, Key Points, Explanation, Conclusion)
      if (answer.background || answer.context || answer.key_points) {
        return (
          <div className="space-y-4">
            {(answer.background || answer.context) && (
              <div className="border-l-4 border-blue-500 pl-3 py-2 bg-blue-50/30">
                <span className="font-semibold text-blue-700 text-base">Background / Context:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.background || answer.context}</div>
              </div>
            )}
            {answer.key_points && (
              <div className="border-l-4 border-purple-500 pl-3 py-2 bg-purple-50/30">
                <span className="font-semibold text-purple-700 text-base">Key Points:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">
                  {Array.isArray(answer.key_points) ? (
                    <ul className="list-disc list-inside space-y-1 ml-4">
                      {answer.key_points.map((point, i) => (
                        <li key={i}>{point}</li>
                      ))}
                    </ul>
                  ) : (
                    answer.key_points
                  )}
                </div>
              </div>
            )}
            {answer.explanation && (
              <div className="border-l-4 border-orange-500 pl-3 py-2 bg-orange-50/30">
                <span className="font-semibold text-orange-700 text-base">Explanation:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.explanation}</div>
              </div>
            )}
            {answer.conclusion && (
              <div className="border-l-4 border-green-500 pl-3 py-2 bg-green-50/30">
                <span className="font-semibold text-green-700 text-base">Conclusion:</span>
                <div className="mt-1 text-gray-800 whitespace-pre-wrap">{answer.conclusion}</div>
              </div>
            )}
          </div>
        )
      }
      
      // Math-style answer (Given, Formula, Steps, etc.)
      if (marks === 5) {
        // 5 marks: BlockMath
        return (
          <div className="space-y-3">
            {answer.given && (
              <div>
                <span className="font-semibold">Given: </span>
                <InlineMath math={extractLatex(answer.given)} />
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
                <ol className="list-decimal list-inside mt-1 space-y-2 ml-4">
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
      } else if (marks === 10) {
        // 10 marks: Check if it's board-style format (post-processed) or original format
        if (answer.substitution !== undefined || answer.calculation !== undefined || answer.final_answer !== undefined) {
          // Board-style format: Given, Formula, Substitution, Calculation, Final Answer
          return (
            <div className="space-y-3 mt-2">
              {answer.given && (
                <div className="border-l-4 border-blue-500 pl-3 py-2 bg-blue-50/30">
                  <span className="font-semibold text-blue-700 text-base">Given:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-sm">{answer.given}</div>
                </div>
              )}
              {answer.formula && (
                <div className="border-l-4 border-purple-500 pl-3 py-2 bg-purple-50/30">
                  <span className="font-semibold text-purple-700 text-base">Formula:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-sm">{answer.formula}</div>
                </div>
              )}
              {answer.substitution && (
                <div className="border-l-4 border-orange-500 pl-3 py-2 bg-orange-50/30">
                  <span className="font-semibold text-orange-700 text-base">Substitution:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-sm">{answer.substitution}</div>
                </div>
              )}
              {answer.calculation && (
                <div className="border-l-4 border-green-500 pl-3 py-2 bg-green-50/30">
                  <span className="font-semibold text-green-700 text-base">Calculation:</span>
                  <div className="mt-1 text-gray-800 whitespace-pre-wrap font-mono text-sm">{answer.calculation}</div>
                </div>
              )}
              {answer.final_answer && (
                <div className="mt-3 p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                  <span className="font-bold text-green-800 text-base">{answer.final_answer}</span>
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
    }
    
    return <span>{String(answer)}</span>
  }
  
  // Update settings when selectedUpload changes
  useEffect(() => {
    const partIds = selectedUpload?.selectedPartIds || null
    setSettings(prev => ({
      ...prev,
      upload_id: partIds ? null : (selectedUpload?.id || ''),
      part_ids: partIds || null
    }))
  }, [selectedUpload])

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

  // Auto-enforce question type based on marks when in simple mode
  useEffect(() => {
    if (useCustomDistribution) return
    const derived = deriveTypeFromMarks(settings.marks)
    if (settings.qna_type !== derived) {
      setSettings(prev => ({ ...prev, qna_type: derived }))
    }
  }, [settings.marks, useCustomDistribution])

  // Cancel generation handler
  const cancelGeneration = () => {
    if (generateAbortController) {
      generateAbortController.abort()
      setGenerateAbortController(null)
    }
    if (generateToastId) {
      toast.dismiss(generateToastId)
      setGenerateToastId(null)
    }
    setGenerating(false)
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

    // Validate custom distribution if enabled
    if (useCustomDistribution) {
      const totalQuestions = customDistribution.reduce((sum, item) => sum + (item.count || 0), 0)
      const maxQuestions = isPremium ? 15 : 3
      
      if (totalQuestions === 0) {
        toast.error('Please add at least one distribution item')
        return
      }
      
      if (totalQuestions > maxQuestions) {
        toast.error(`Total questions (${totalQuestions}) exceeds your limit (${maxQuestions})`)
        return
      }
      
      // Validate each item
      for (const item of customDistribution) {
        if (!item.count || item.count < 1) {
          toast.error('Each distribution item must have at least 1 question')
          return
        }
        if (!item.marks || ![1, 2, 3, 5, 10].includes(item.marks)) {
          toast.error('Marks must be 1, 2, 3, 5, or 10')
          return
        }
      }
    }

    // Create AbortController for cancellation
    const abortController = new AbortController()
    setGenerateAbortController(abortController)

    setGenerating(true)
    
    // Show generating animation with cancel button
    const generatingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>⚡ Generating questions... This may take a moment</span>
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
    
    try {
      // Normalize marks → type for simple mode
      const normalizedType = deriveTypeFromMarks(settings.marks)

      // Normalize custom distribution types if enabled
      const normalizedDistribution = useCustomDistribution
        ? customDistribution.map(item => ({
            ...item,
            type: deriveTypeFromMarks(item.marks)
          }))
        : null

      // Get subject from selected upload or use default
      const uploadSubject = selectedUpload?.subject || 'general'
      
      const requestData = {
        ...settings,
        qna_type: normalizedType,
        subject: uploadSubject,  // Pass subject from upload
        // Remove upload_id if using part_ids (multi-select mode)
        ...(settings.part_ids ? { upload_id: null } : { part_ids: null }),
        ...(useCustomDistribution && { 
          custom_distribution: normalizedDistribution,
          num_questions: normalizedDistribution.reduce((sum, item) => sum + (item.count || 0), 0)
        })
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
      
      const response = await axios.post('/api/qna/generate', requestData, {
        signal: abortController.signal
      })
      
      // Check if cancelled before proceeding
      if (abortController.signal.aborted) {
        return
      }
      
      toast.dismiss(processingToast)
      toast.dismiss() // clear any prior error/success toasts
      setResult(response.data)
      setEditedQuestions(response.data?.qna_json?.questions || [])
      
      // Refresh user data to update quota counts after generation
      try {
        if (fetchUser) {
          await fetchUser()
        }
        // Call callback to refresh profile data if provided
        if (onGenerationComplete) {
          onGenerationComplete()
        }
      } catch (refreshError) {
        console.warn('Failed to refresh user data after generation:', refreshError)
        // Don't fail the generation if refresh fails
      }
      
      // Debug: Log questions and answers
      const questions = response.data?.qna_json?.questions || []
      console.log('📋 Generated questions:', questions.length)
      questions.forEach((q, idx) => {
        console.log(`Q${idx + 1} (${q.marks} marks):`, {
          has_correct_answer: !!q.correct_answer,
          has_answer: !!q.answer,
          correct_answer_type: typeof q.correct_answer,
          correct_answer_preview: q.correct_answer ? (typeof q.correct_answer === 'string' ? q.correct_answer.substring(0, 50) : 'object') : 'missing'
        })
      })
      
      // For free users, show only preview
      if (!isPremium) {
        toast.success('✅ Preview generated! Upgrade for full access.', { duration: 3000 })
      } else {
        toast.success('✅ Q/A generated successfully!', { duration: 3000 })
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        // Generation was cancelled - already handled in cancelGeneration
        return
      }
      toast.dismiss()
      const detail = error?.response?.data?.detail || error?.response?.data || error?.message || 'Generation failed'
      console.error('Generation failed:', {
        detail,
        status: error?.response?.status,
        data: error?.response?.data
      })
      toast.error(typeof detail === 'string' ? detail : 'Generation failed')
    } finally {
      // Always reset generating state and cleanup
      setGenerating(false)
      setGenerateAbortController(null)
      setGenerateToastId(null)
    }
  }

  const addDistributionItem = () => {
    const maxQuestions = isPremium ? 15 : 3
    const currentTotal = customDistribution.reduce((sum, item) => sum + (item.count || 0), 0)
    if (currentTotal >= maxQuestions) {
      toast.error(`Maximum ${maxQuestions} questions allowed`)
      return
    }
    setCustomDistribution([...customDistribution, { marks: 1, count: 1, type: 'mcq' }])
  }

  const removeDistributionItem = (index) => {
    if (customDistribution.length <= 1) {
      toast.error('At least one distribution item is required')
      return
    }
    setCustomDistribution(customDistribution.filter((_, i) => i !== index))
  }

  const updateDistributionItem = (index, field, value) => {
    const updated = [...customDistribution]
    updated[index] = { ...updated[index], [field]: value }
    
    // Auto-determine type based on marks
    if (field === 'marks') {
      const marks = parseInt(value)
      updated[index].type = deriveTypeFromMarks(marks)
    }
    
    setCustomDistribution(updated)
  }

  const renderPreview = () => {
    if (!result) return null
    const questions = editedQuestions.length ? editedQuestions : (result.qna_json?.questions || [])
    const previewCount = isPremium ? questions.length : Math.min(3, questions.length)

    return (
      <div className="mt-6 space-y-6">
        <h3 className="text-lg font-semibold">Generated Questions</h3>
        
        {questions.slice(0, previewCount).map((q, idx) => (
          <div key={idx} className="border-2 border-gray-300 rounded-lg p-5 bg-white shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start gap-3">
              <span className="font-bold text-blue-600 text-lg">Q{idx + 1}.</span>
              <div className="flex-1">
                <div className="flex gap-3 items-start mb-2">
                  <textarea
                    value={q.question || ''}
                    onChange={(e) => {
                      const updated = [...questions]
                      updated[idx] = { ...updated[idx], question: e.target.value }
                      setEditedQuestions(updated)
                    }}
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                    rows={2}
                  />
                  <div className="flex flex-col items-end gap-1">
                    <span className="inline-block px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                      {q.marks} mark{q.marks !== 1 ? 's' : ''}
                    </span>
                    <span className="text-[11px] text-gray-500">Auto-set type: {deriveTypeFromMarks(q.marks)}</span>
                  </div>
                </div>

                {q.type === 'mcq' && q.options && (
                  <div className="mt-3 space-y-2">
                    {q.options.map((opt, i) => {
                      const optionLabel = String.fromCharCode(65 + i)
                      return (
                        <div 
                          key={i} 
                          className="flex items-start gap-3 p-2 border border-gray-200 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <span className="font-bold text-blue-600 min-w-[24px]">{optionLabel}.</span>
                          <span className="text-gray-700 flex-1">{opt}</span>
                        </div>
                      )
                    })}
                  </div>
                )}

                {isPremium && settings.output_format !== 'questions_only' && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg border-2 border-green-300">
                    <p className="text-sm font-semibold text-green-800 mb-2">✓ Correct Answer:</p>
                    <div className="text-green-700 font-medium">
                      {(() => {
                        const answer = q.correct_answer || q.answer
                        if (!answer || answer === "N/A" || answer === "N/A - Answer not generated by AI") {
                          console.warn(`⚠️ Missing or invalid answer for Q${idx + 1} (${q.marks} marks):`, { answer, question: q.question?.substring(0, 50) })
                          return <span className="text-yellow-600 italic">Answer not generated. Please regenerate questions.</span>
                        }
                        if (typeof answer === 'object' && Object.keys(answer).length === 0) {
                          console.warn(`⚠️ Empty answer object for Q${idx + 1} (${q.marks} marks):`, q)
                          return <span className="text-yellow-600 italic">Answer object is empty. Please regenerate questions.</span>
                        }
                        const rendered = renderAnswer(answer, q.marks || 0)
                        if (!rendered) {
                          console.warn(`⚠️ renderAnswer returned null for Q${idx + 1} (${q.marks} marks):`, { answer, answerType: typeof answer })
                          return <span className="text-yellow-600 italic">Answer could not be rendered. Please regenerate questions.</span>
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
          <div className="relative inline-flex mt-4">
            <button
              onClick={() => downloadSet(result.id, 'pdf', 'questions_answers')}
              disabled={downloading}
              className="px-4 py-2 bg-green-600 text-white rounded-l-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              title={downloading ? "Download in progress..." : "Download Q+A (PDF)"}
            >
              {downloading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Downloading...
                </>
              ) : (
                'Download'
              )}
            </button>
            <button
              onClick={() => setShowDownloadMenu((prev) => !prev)}
              disabled={downloading}
              className="px-3 py-2 bg-green-600 text-white rounded-r-lg hover:bg-green-700 border-l border-green-500 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              title={downloading ? "Download in progress..." : "More formats"}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showDownloadMenu && !downloading && (
              <div className="absolute z-20 top-full left-0 mt-2 w-72 max-h-64 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-xl">
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
    
    // Show preparing message with cancel button
    const preparingToast = toast.loading(
      (t) => (
        <div className="flex items-center gap-3">
          <span>📄 Preparing download... Please wait</span>
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
    
    try {
      // Update to generating message with cancel button
      toast.dismiss(preparingToast)
      const generatingToast = toast.loading(
        (t) => (
          <div className="flex items-center gap-3">
            <span>⚙️ Generating PDF... This may take a moment</span>
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
      toast.dismiss()
      toast.error('Download failed: ' + (error.response?.data?.detail || 'Unknown error'))
    } finally {
      // Always reset downloading state and cleanup
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
          <p className="text-sm text-gray-700">
            Generating questions from <strong>{selectedPartIds.length} selected part{selectedPartIds.length > 1 ? 's' : ''}</strong>.
            Questions will be generated from the combined content of all selected parts (max 15 questions total).
          </p>
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
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Upload
          </label>
          <select
            value={settings.upload_id || ''}
            onChange={(e) => {
              const uploadId = e.target.value ? parseInt(e.target.value) : null
              setSettings({ ...settings, upload_id: uploadId, part_ids: null })
              onSelectUpload(uploads.find(u => u.id === uploadId))
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select an upload --</option>
            {uploads.map((upload) => (
              <option key={upload.id} value={upload.id}>
                {upload.file_name} ({upload.file_type})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Distribution Mode Toggle */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg" data-tour="distribution-mode">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Distribution Mode
            </label>
            <p className="text-xs text-gray-600">
              {useCustomDistribution 
                ? 'Custom: Set exact distribution for each mark pattern'
                : 'Simple: Use a single marks pattern for all questions'}
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useCustomDistribution}
              onChange={(e) => setUseCustomDistribution(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            <span className="ml-3 text-sm font-medium text-gray-700">
              {useCustomDistribution ? 'Custom' : 'Simple'}
            </span>
          </label>
        </div>
      </div>

      {/* Custom Distribution Selector */}
      {useCustomDistribution && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Custom Distribution</h3>
            <button
              onClick={addDistributionItem}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              + Add Pattern
            </button>
          </div>
          
          <div className="space-y-3 mb-4">
            {customDistribution.map((item, index) => {
              const totalQuestions = customDistribution.reduce((sum, i) => sum + (i.count || 0), 0)
              const maxQuestions = isPremium ? 15 : 3
              
              return (
                <div key={index} className="flex flex-wrap gap-3 items-end p-3 bg-white border border-gray-300 rounded-lg">
                  <div className="flex-1 min-w-[120px]">
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Marks
                    </label>
                    <select
                      value={item.marks}
                      onChange={(e) => updateDistributionItem(index, 'marks', parseInt(e.target.value))}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    >
                      <option value="1">1 mark</option>
                      <option value="2">2 marks</option>
                      <option value="3">3 marks</option>
                      <option value="5">5 marks</option>
                      <option value="10">10 marks</option>
                    </select>
                  </div>
                  
                  <div className="flex-1 min-w-[120px]">
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Count
                    </label>
                    <input
                      type="number"
                      min="1"
                      max={maxQuestions - totalQuestions + (item.count || 0)}
                      value={item.count}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 1
                        const max = maxQuestions - totalQuestions + (item.count || 0)
                        if (val > max) {
                          toast.error(`Cannot exceed total limit of ${maxQuestions} questions`)
                          updateDistributionItem(index, 'count', max)
                        } else if (val < 1) {
                          updateDistributionItem(index, 'count', 1)
                        } else {
                          updateDistributionItem(index, 'count', val)
                        }
                      }}
                      onBlur={(e) => {
                        const val = parseInt(e.target.value) || 1
                        const totalQuestions = customDistribution.reduce((sum, i) => sum + (i.count || 0), 0)
                        const currentItemCount = item.count || 0
                        const max = maxQuestions - totalQuestions + currentItemCount
                        if (val > max) {
                          toast.error(`Cannot exceed total limit of ${maxQuestions} questions`)
                          updateDistributionItem(index, 'count', max)
                        } else if (val < 1) {
                          updateDistributionItem(index, 'count', 1)
                        }
                      }}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    />
                  </div>
                  
                  <div className="flex-1 min-w-[120px]">
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Type
                    </label>
                    <input
                      value={deriveTypeFromMarks(item.marks)}
                      readOnly
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 text-gray-700"
                    />
                    <p className="text-[10px] text-gray-500 mt-1">Auto-set from marks</p>
                  </div>
                  
                  <button
                    onClick={() => removeDistributionItem(index)}
                    className="px-3 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                    disabled={customDistribution.length <= 1}
                  >
                    Remove
                  </button>
                </div>
              )
            })}
          </div>
          
          <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <span className="text-sm font-medium text-gray-700">
              Total Questions: <span className="text-blue-600 font-bold">
                {customDistribution.reduce((sum, item) => sum + (item.count || 0), 0)}
              </span> / {isPremium ? 15 : 3}
            </span>
            <span className="text-xs text-gray-600">
              {customDistribution.map((item, idx) => (
                <span key={idx}>
                  {idx > 0 && ' + '}
                  {item.count} × {item.marks} mark{item.marks !== 1 ? 's' : ''} ({item.type})
                </span>
              ))}
            </span>
          </div>
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

        {!useCustomDistribution && (
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
        )}

        {!useCustomDistribution && (
          <div>
            <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
              Number of Questions
            </label>
            <div className="relative group">
              <input
                type="number"
                min="1"
                max={isPremium ? 15 : 3}
                value={settings.num_questions}
                onChange={(e) => {
                  const val = e.target.value === '' ? '' : parseInt(e.target.value)
                  if (val === '') {
                    setSettings({ ...settings, num_questions: '' })
                    return
                  }
                  const max = isPremium ? 15 : 3
                  if (val > max) {
                    toast.error(`Maximum ${max} questions allowed for ${isPremium ? 'premium' : 'free'} users`)
                    setSettings({ ...settings, num_questions: max })
                  } else if (val < 1) {
                    setSettings({ ...settings, num_questions: 1 })
                  } else {
                    setSettings({ ...settings, num_questions: val })
                  }
                }}
                onBlur={(e) => {
                  const val = parseInt(e.target.value) || 1
                  const max = isPremium ? 15 : 3
                  if (val < 1) {
                    setSettings({ ...settings, num_questions: 1 })
                  } else if (val > max) {
                    setSettings({ ...settings, num_questions: max })
                    toast.error(`Maximum ${max} questions allowed`)
                  } else {
                    setSettings({ ...settings, num_questions: val })
                  }
                }}
                className="w-full px-4 py-2 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={`1-${isPremium ? 15 : 3}`}
              />
              {/* Hover tooltip showing max limit */}
              <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-[100]">
                <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl whitespace-nowrap relative">
                  Max: {isPremium ? 15 : 3} questions
                  <div className="absolute left-1/2 -translate-x-1/2 -top-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
              </div>
            </div>
            <p className="text-xs md:text-sm text-gray-500 mt-1">
              Type any number from 1 to {isPremium ? 15 : 3} (hover input to see limit)
            </p>
          </div>
        )}

        {!useCustomDistribution && (
          <div>
            <label className="block text-sm md:text-sm font-medium text-gray-700 mb-2">
              Marks Pattern
            </label>
            <select
              value={settings.marks}
              onChange={(e) => {
                const val = e.target.value
                setSettings(prev => ({
                  ...prev,
                  marks: val,
                  qna_type: deriveTypeFromMarks(val)
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
        )}

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
          <select
            value={settings.target_language}
            onChange={(e) => setSettings({ ...settings, target_language: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="english">English</option>
            <option value="tamil">Tamil (தமிழ்)</option>
            <option value="hindi">Hindi (हिंदी)</option>
            <option value="arabic">Arabic (العربية)</option>
            <option value="spanish">Spanish (Español)</option>
            <option value="telugu">Telugu (తెలుగు)</option>
            <option value="kannada">Kannada (ಕನ್ನಡ)</option>
            <option value="malayalam">Malayalam (മലയാളം)</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            All questions and answers will be generated in the selected language
          </p>
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={generating || (!settings.upload_id && !settings.part_ids)}
        className="w-full md:w-auto px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {generating ? 'Generating...' : 'Generate Q/A'}
      </button>

      {/* Results */}
      {renderPreview()}
    </div>
  )
}

export default QnAGenerator
