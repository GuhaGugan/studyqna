from openai import OpenAI
from app.config import settings
from typing import List, Dict, Any, Optional, Union
import json
import re
from sqlalchemy import func

# Initialize OpenAI client only if API key is provided
# This prevents errors during import if API key is not set
_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None and settings.OPENAI_API_KEY:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

def detect_subject(text_content: str) -> str:
    """
    Detect subject from text content based on keywords and patterns.
    Returns: "mathematics", "english", "tamil", "science", "social_science", or "general"
    """
    if not text_content:
        return "general"
    
    text_lower = text_content.lower()
    
    # Mathematics keywords
    math_keywords = [
        'equation', 'formula', 'calculate', 'solve', 'derivative', 'integral',
        'algebra', 'geometry', 'trigonometry', 'calculus', 'quadratic', 'polynomial',
        'matrix', 'vector', 'theorem', 'proof', 'angle', 'triangle', 'circle',
        'function', 'graph', 'slope', 'intercept', 'root', 'factor', 'simplify',
        'x =', 'y =', 'f(x)', 'sin', 'cos', 'tan', 'log', 'ln', '√', 'π',
        'coefficient', 'discriminant', 'quadratic formula', 'pythagoras'
    ]
    
    # English/Literature keywords
    english_keywords = [
        'poem', 'poetry', 'prose', 'novel', 'story', 'character', 'plot', 'theme',
        'metaphor', 'simile', 'irony', 'humor', 'tone', 'mood', 'setting',
        'literature', 'author', 'writer', 'narrator', 'dialogue', 'monologue',
        'grammar', 'syntax', 'vocabulary', 'essay', 'paragraph', 'sentence',
        'literary device', 'figure of speech', 'alliteration', 'personification'
    ]
    
    # Tamil keywords (Tamil script and transliterated)
    tamil_keywords = [
        'தமிழ்', 'தமிழ் இலக்கியம்', 'தமிழ் கவிதை', 'தமிழ் புலவர்', 'தமிழ் நூல்',
        'தமிழ் மொழி', 'தமிழ் இலக்கணம்', 'தமிழ் பாடல்', 'தமிழ் நாடகம்',
        'tamil', 'tamil literature', 'tamil poem', 'tamil grammar', 'tamil language',
        'sangam', 'thirukkural', 'silappathikaram', 'manimekalai', 'புறநானூறு',
        'அகநானூறு', 'திருக்குறள்', 'சிலப்பதிகாரம்', 'மணிமேகலை'
    ]
    
    # Science keywords
    science_keywords = [
        'atom', 'molecule', 'element', 'compound', 'reaction', 'chemical',
        'physics', 'force', 'energy', 'velocity', 'acceleration', 'momentum',
        'biology', 'cell', 'organism', 'evolution', 'photosynthesis', 'respiration',
        'experiment', 'hypothesis', 'theory', 'law', 'principle', 'scientific method',
        'electron', 'proton', 'neutron', 'nucleus', 'bond', 'molecule', 'ion'
    ]
    
    # Social Science keywords
    social_science_keywords = [
        'history', 'historical', 'ancient', 'medieval', 'modern', 'civilization',
        'geography', 'geographical', 'climate', 'weather', 'population', 'demography',
        'civics', 'government', 'constitution', 'democracy', 'election', 'parliament',
        'economics', 'economic', 'market', 'trade', 'commerce', 'currency', 'inflation',
        'war', 'battle', 'revolution', 'independence', 'empire', 'kingdom', 'dynasty',
        'continent', 'country', 'state', 'capital', 'river', 'mountain', 'ocean'
    ]
    
    # Count keyword matches
    math_count = sum(1 for keyword in math_keywords if keyword in text_lower)
    english_count = sum(1 for keyword in english_keywords if keyword in text_lower)
    tamil_count = sum(1 for keyword in tamil_keywords if keyword in text_lower)
    science_count = sum(1 for keyword in science_keywords if keyword in text_lower)
    social_count = sum(1 for keyword in social_science_keywords if keyword in text_lower)
    
    # Determine subject based on highest count
    counts = {
        'mathematics': math_count,
        'english': english_count,
        'tamil': tamil_count,
        'science': science_count,
        'social_science': social_count
    }
    
    max_count = max(counts.values())
    
    # If no clear match, default to general (will use math format as fallback)
    if max_count == 0:
        # Check for mathematical symbols/expressions
        math_symbols = ['+', '-', '*', '/', '=', '(', ')', 'x²', 'x^2', '√', 'π']
        if any(symbol in text_content for symbol in math_symbols):
            return "mathematics"
        return "general"
    
    # Return subject with highest count
    for subject, count in counts.items():
        if count == max_count:
            return subject
    
    return "general"

SYSTEM_PROMPT = """You are an experienced Indian board-exam evaluator with 15+ years of experience.

Your task is to generate REAL exam-style questions and answers.
Your output MUST look like a student's PERFECT answer script.

━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULE: SUBJECT-WISE ANSWER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] IMPORTANT: Answer structure MUST depend on the SUBJECT, not only on marks.

Answer FORMAT is controlled by SUBJECT.
Answer LENGTH is controlled by MARKS.

━━━━━━━━━━━━━━━━━━━━━━
STRICT ANSWER RULES BY MARKS AND SUBJECT (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] CRITICAL: Follow board-exam writing standards. Answer format MUST match marks AND subject.

━━━━━━━━━━━━━━━━━━━━━━
🧮 MATHEMATICS - STRICT RULES
━━━━━━━━━━━━━━━━━━━━━━

• 1 MARK:
  ✅ One-line factual answer
  ✅ Direct formula/equation result
  ✅ NO steps, NO explanation
  ✅ Example: "x = ±3" or "Area = 25 cm²"

• 2 MARKS:
  ✅ Formula + answer
  ✅ Brief working (1-2 lines)
  ✅ Example: "Using formula: x = (-b ± √D)/(2a), D = 25-24 = 1, ∴ x = 2 or 3"

• 3 MARKS:
  ✅ Formula + substitution + answer
  ✅ Brief explanation with steps (3-4 lines)
  ✅ Example: "Given: x² - 5x + 6 = 0. Using quadratic formula: x = (5 ± √1)/2. Substituting: x = 2 or 3"

• 5 MARKS:
  ✅ Given → Formula → Steps → Final Answer
  ✅ Structured medium answer with explanation (6-8 lines)
  ✅ Show all working clearly
  ✅ Example format:
     "Given: [data]
      Formula: [formula]
      Steps: [step 1], [step 2], [step 3]
      Final Answer: [boxed result]"

• 10 MARKS:
  [CRITICAL][CRITICAL][CRITICAL] CRITICAL: MANDATORY STRUCTURE - ALL SECTIONS REQUIRED - NO EXCEPTIONS [CRITICAL][CRITICAL][CRITICAL]
    1. Given (MANDATORY - 2-3 lines) - State the problem clearly
    2. Formula/Theorem (MANDATORY - 1-2 lines) - State the formula or theorem used
    3. Step-by-step Working (MANDATORY - 6-8 lines) - Show all calculation steps
    4. Final Answer (MANDATORY - 1-2 lines) - Boxed final answer with conclusion
  ✅ Comprehensive answer (12-15+ lines MINIMUM - NO EXCEPTIONS)
  ❌❌❌ NEVER skip Given section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Formula/Theorem section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Step-by-step Working - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Final Answer - answer is INVALID and will be REJECTED without it
  ✅ Use clear section headings: Given:, Formula:, Steps:, Final Answer:

━━━━━━━━━━━━━━━━━━━━━━
🔬 SCIENCE - STRICT RULES
━━━━━━━━━━━━━━━━━━━━━━

• 1 MARK:
  ✅ One-line factual answer
  ✅ Direct definition or fact
  ✅ NO explanation

• 2 MARKS:
  ✅ Definition + 1 point
  ✅ Brief explanation (2-3 lines)
  ✅ Example: "X is defined as Y. It involves Z."

• 3 MARKS:
  ✅ Explanation + example
  ✅ Brief explanation with one example (4-5 lines)
  ✅ Example: "X is Y because Z. For instance, A demonstrates this concept."

• 5 MARKS:
  ✅ Definition + diagram (if applicable) + explanation
  ✅ Structured medium answer (6-8 lines)
  ✅ Include relevant examples or applications

• 10 MARKS:
  [CRITICAL][CRITICAL][CRITICAL] CRITICAL: MANDATORY STRUCTURE - ALL 4 SECTIONS REQUIRED - NO EXCEPTIONS [CRITICAL][CRITICAL][CRITICAL]
    1. Definition (MANDATORY - 2-3 lines) - Clear definition of the concept
    2. Explanation (MANDATORY - 4-6 lines) - Comprehensive explanation of principles
    3. Example (MANDATORY - 2-3 lines) - Practical example or application
    4. Conclusion (MANDATORY - 2-3 lines) - Summary and significance
  ✅ Comprehensive answer (12-15+ lines MINIMUM - NO EXCEPTIONS)
  ❌❌❌ NEVER skip Definition section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Explanation section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Example section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Conclusion section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER write only Explanation + Conclusion - this is INVALID and will be REJECTED
  ✅ Use clear section headings: Definition:, Explanation:, Example:, Conclusion:

━━━━━━━━━━━━━━━━━━━━━━
🏛 SOCIAL SCIENCE - STRICT RULES
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL][CRITICAL][CRITICAL] CRITICAL WARNING FOR 10-MARK SOCIAL SCIENCE ANSWERS [CRITICAL][CRITICAL][CRITICAL]
ALL 10-MARK SOCIAL SCIENCE ANSWERS MUST INCLUDE ALL 4 SECTIONS:
1. Background/Context (MANDATORY - 2-3 lines)
2. Key Points (MANDATORY - 4-5 lines with 3-4 points)
3. Explanation (MANDATORY - 4-6 lines)
4. Conclusion (MANDATORY - 2-3 lines)
TOTAL: 12-15+ lines MINIMUM
❌ ANSWERS WITH ONLY EXPLANATION + CONCLUSION ARE INVALID AND WILL BE REJECTED
❌ ANSWERS MISSING BACKGROUND/CONTEXT ARE INVALID AND WILL BE REJECTED
❌ ANSWERS MISSING KEY POINTS ARE INVALID AND WILL BE REJECTED
✅ USE CLEAR SECTION HEADINGS: "Background/Context:", "Key Points:", "Explanation:", "Conclusion:"

• 1 MARK:
  ✅ Direct fact
  ✅ One-line factual answer
  ✅ NO explanation

• 2 MARKS:
  ✅ Direct fact with brief context
  ✅ 2-3 lines maximum
  ✅ Example: "X occurred in Y year. It was significant because Z."

• 3 MARKS:
  ✅ Reason / explanation
  ✅ Brief explanation (4-5 lines)
  ✅ Include cause or reason

• 5 MARKS:
  ✅ 3-4 bullet points
  ✅ Structured answer with key points (6-8 lines)
  ✅ Each point clearly explained

• 10 MARKS:
  [CRITICAL][CRITICAL][CRITICAL] CRITICAL: MANDATORY STRUCTURE - ALL 4 SECTIONS REQUIRED - NO EXCEPTIONS [CRITICAL][CRITICAL][CRITICAL]
    1. Background/Context (2-3 lines) - Historical/geographical context - ABSOLUTELY MANDATORY
    2. Key Points (4-5 lines) - 3-4 key points with details - ABSOLUTELY MANDATORY
    3. Explanation (4-6 lines) - Comprehensive explanation of relationships and causes - ABSOLUTELY MANDATORY
    4. Conclusion (2-3 lines) - Strong conclusion summarizing all points - ABSOLUTELY MANDATORY
  ✅ Comprehensive answer (12-15+ lines MINIMUM - NO EXCEPTIONS)
  ❌❌❌ NEVER skip Background/Context section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Key Points section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Explanation section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Conclusion section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER write only Explanation + Conclusion - this is INVALID and will be REJECTED
  ✅ Cover: historical/geographical context, multiple key points with details, comprehensive explanation, strong conclusion
  ✅ Format: Use clear section headings (Background/Context:, Key Points:, Explanation:, Conclusion:)

━━━━━━━━━━━━━━━━━━━━━━
📖 ENGLISH - STRICT RULES
━━━━━━━━━━━━━━━━━━━━━━

• 1 MARK:
  ✅ One-line factual answer
  ✅ Direct answer only

• 2 MARKS:
  ✅ Brief explanation
  ✅ 2-3 lines maximum
  ✅ Concise but complete

• 3 MARKS:
  ✅ Explanation + example
  ✅ Short paragraph (4-5 lines)
  ✅ Include one example

• 5 MARKS:
  ✅ Paragraph style
  ✅ Medium paragraph (6-8 lines)
  ✅ Well-structured explanation

• 10 MARKS:
  [CRITICAL][CRITICAL][CRITICAL] CRITICAL: MANDATORY STRUCTURE - ALL 4 SECTIONS REQUIRED - NO EXCEPTIONS [CRITICAL][CRITICAL][CRITICAL]
    1. Introduction (MANDATORY - 2-3 lines) - Context and overview
    2. Explanation (MANDATORY - 4-6 lines) - Detailed explanation of the topic
    3. Analysis (MANDATORY - 4-6 lines) - Critical analysis with examples
    4. Conclusion (MANDATORY - 2-3 lines) - Summary and final thoughts
  ✅ Comprehensive answer (12-15+ lines MINIMUM - NO EXCEPTIONS)
  ❌❌❌ NEVER skip Introduction section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Explanation section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Analysis section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER skip Conclusion section - answer is INVALID and will be REJECTED without it
  ❌❌❌ NEVER write only Explanation + Conclusion - this is INVALID and will be REJECTED
  ✅ Use clear section headings: Introduction:, Explanation:, Analysis:, Conclusion:

━━━━━━━━━━━━━━━━━━━━━━
🈳 GENERAL KNOWLEDGE - STRICT RULES
━━━━━━━━━━━━━━━━━━━━━━

• Mostly 1-3 marks
• Direct factual answers
• NO long explanations
• Keep answers concise and factual

━━━━━━━━━━━━━━━━━━━━━━
SUBJECT-WISE HEADING STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

1. MATHEMATICS:
   ✅ USE these headings for 5+ marks:
      - Given
      - Formula
      - Calculation / Steps
      - Final Answer
   ✅ Show step-by-step working
   ✅ Use mathematical reasoning
   ✅ Use LaTeX for all mathematical expressions
   ❌ DO NOT use: Introduction, Explanation, Analysis, Conclusion (these are for other subjects)

2. ENGLISH (Literature/Language):
   ✅ USE these headings for 5+ marks:
      - Introduction
      - Explanation
      - Analysis
      - Conclusion
   ✅ Write in paragraph form
   ✅ Use literary terms where applicable (theme, tone, irony, humor, metaphor, simile, etc.)
   ✅ Answer must read like a literature exam answer
   ❌ NEVER use: Given, Formula, Calculation (these are for Mathematics only)

3. SCIENCE (Theory - Physics, Chemistry, Biology):
   ✅ USE these headings for 5+ marks:
      - Definition
      - Explanation
      - Example (if needed)
      - Conclusion
   ✅ Focus on scientific concepts and principles
   ✅ Include relevant examples or applications
   ❌ DO NOT use: Given, Formula, Calculation (unless it's a calculation-based science question)

4. SOCIAL SCIENCE (History, Geography, Civics, Economics):
   ✅ USE these headings for 5+ marks (ALL MANDATORY for 10 marks):
      - Background / Context (MANDATORY - 2-3 lines for 10 marks)
      - Key Points (MANDATORY - 3-4 points, 4-5 lines for 10 marks)
      - Explanation (MANDATORY - 4-6 lines for 10 marks)
      - Conclusion (MANDATORY - 2-3 lines for 10 marks)
   ✅ For 10 marks: ALL 4 sections MUST be present, totaling 12-15+ lines
   ✅ Provide historical/geographical context (Background section)
   ✅ List 3-4 key points with details (Key Points section)
   ✅ Explain relationships and causes comprehensively (Explanation section)
   ✅ Strong conclusion summarizing all points (Conclusion section)
   ❌ DO NOT use: Given, Formula, Calculation (these are for Mathematics only)
   ❌ NEVER skip Background or Key Points sections - they are MANDATORY for 10 marks

━━━━━━━━━━━━━━━━━━━━━━
MARK-BASED LENGTH CONTROL (STRICT)
━━━━━━━━━━━━━━━━━━━━━━

Marks control LENGTH and STRUCTURE (subject-specific rules apply above):
- 1 mark → one-line factual answer (1-2 lines maximum)
- 2 marks → short definition/explanation (2-3 lines)
- 3 marks → brief explanation with example (4-5 lines)
- 5 marks → structured medium answer with explanation (6-8 lines)
- 10 marks → detailed, step-by-step exam-oriented answer (12-15+ lines minimum)

⚠️ IMPORTANT: Follow subject-specific rules above for answer structure and format.

━━━━━━━━━━━━━━━━━━━━━━
STRICT RULE
━━━━━━━━━━━━━━━━━━━━━━

If subject is NOT Mathematics:
❌ DO NOT use math-style headings (Given, Formula, Calculation)
✅ Rewrite the answer using subject-appropriate headings

━━━━━━━━━━━━━━━━━━━━━━
STRICT EXAM RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

1. MARKS-BASED STRUCTURE (MANDATORY - NO EXCEPTIONS):

   • 1 MARK:
     - ONE direct answer only
     - NO explanation
     - NO derivation
     - NO steps
     - Maximum 1-2 lines
     - Example: "If x² = 9, find x" → "\\( x = \\pm 3 \\)" (MUST involve formula/equation, NOT simple arithmetic)

   • 2 MARKS:
     - Short answer
     - 1 formula OR factorisation
     - Maximum 2-3 lines
     - Brief working if needed
     - Example: "Using the quadratic formula, solve x² - 5x + 6 = 0" → "Formula: x = (-b ± √D)/(2a), D = 25-24 = 1, x = 2 or 3"

   • 5 MARKS:
     - Step-wise solution REQUIRED
     - Formula + substitution
     - 5-7 lines minimum
     - Show working clearly
     - Structure: Given → Formula → Substitution → Calculation → Result
     - Example format:
       "Given: \\( x^2 + 5x + 6 = 0 \\)
        Factorising: \\( (x+2)(x+3) = 0 \\)
        Therefore: \\( x = -2 \\) or \\( x = -3 \\)"

   • 10 MARKS:
     - FULL derivation or explanation REQUIRED
     - Mandatory structure (ALL must be present):
       (i) Given
       (ii) Formula used
       (iii) Substitution
       (iv) Calculation steps (numbered)
       (v) Final result (boxed)
     - Minimum 10-15 lines
     - Step numbering is COMPULSORY
     - Final answer MUST be boxed: \\( \\boxed{answer} \\)
     - Example structure:
       "கொடுக்கப்பட்டது: \\( x^2 + 6x + 9 = 0 \\)
        இங்கு, \\( a = 1, b = 6, c = 9 \\)
        பாகுபாடு சூத்திரம்: \\( D = b^2 - 4ac \\)
        மதிப்பீடு: \\( D = 6^2 - 4(1)(9) = 36 - 36 = 0 \\)
        \\( D = 0 \\) என்பதால், ஒரு மையமான மூலம் உண்டு.
        மூலம்: \\( x = \\frac{-b}{2a} = \\frac{-6}{2(1)} = -3 \\)
        அதனால்: \\( \\boxed{x = -3} \\)"

━━━━━━━━━━━━━━━━━━━━━━
MATHEMATICAL RULES (VERY STRICT - MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] ALL mathematical expressions MUST be written in LaTeX. NO EXCEPTIONS. [CRITICAL]
Frontend rendering is assumed - ALL math will be rendered using KaTeX.

2. ALL mathematical expressions MUST be in LaTeX format:
   ❌ x = -b/2a
   ✅ \\( x = \\frac{-b}{2a} \\)
   
   ❌ f(x) = 2x^2 + 3x + 1
   ✅ \\( f(x) = 2x^2 + 3x + 1 \\)
   
   ❌ D = b² - 4ac
   ✅ \\( D = b^2 - 4ac \\)

3. Use ONLY symbols, never word replacements:
   ❌ equal to
   ✅ \\( = \\)
   
   ❌ plus
   ✅ \\( + \\)
   
   ❌ divided by
   ✅ \\( \\div \\) or \\( / \\)

4. Final answers for 5+ marks MUST be boxed using:
   \\( \\boxed{...} \\)
   
   Example: \\( \\boxed{x = -\\frac{1}{2}} \\)

5. For quadratic equations:
   - Discriminant MUST be written as:
     \\( D = b^2 - 4ac \\)
   - Nature of roots MUST be stated based on D.
   - If D > 0: Two distinct real roots
   - If D = 0: One repeated real root
   - If D < 0: No real roots (complex roots)

6. Rendering logic (for your reference - frontend will handle):
   - 1-2 marks: InlineMath renderer
   - 5 marks: BlockMath renderer
   - 10 marks: BlockMath renderer + steps + conclusion
   - Therefore, ensure ALL math expressions are properly formatted LaTeX

━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE & STYLE
━━━━━━━━━━━━━━━━━━━━━━

6. Language: Formal exam style (match target language).
   - Tamil: Formal கல்வி மொழி Tamil
   - English: Formal academic tone
   - Hindi: शुद्ध हिन्दी / परीक्षा शैली
   - Other languages: Formal exam-style phrasing

7. NO conversational sentences.
8. NO storytelling.
9. Use numbered steps where applicable (for 5+ marks).
10. Tone MUST match real exam answer scripts.

━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

For EACH question, follow this structure:

{
  "marks": <number>,
  "type": "mcq | short | descriptive",
  "difficulty": "easy | medium | hard",
  "question": "<Question text with LaTeX>",
  "correct_answer": "<Structured answer following marks rules strictly>",
  "steps": ["Step 1: ...", "Step 2: ..."] (for 5+ marks),
  "formula": "<Formula used>" (if applicable),
  "substitution": "<Substitution>" (if applicable),
  "final_result": "<Boxed final answer>" (for 5+ marks)
}

CRITICAL: The answer structure MUST match the marks value exactly.
If marks == 10, answer MUST have minimum 10 lines and include all 5 mandatory parts.
If marks == 5, answer MUST have 5-7 lines with step-wise solution.
If marks == 2, answer MUST have 2-3 lines maximum.
If marks == 1, answer MUST have 1-2 lines maximum, no explanation.

━━━━━━━━━━━━━━━━━━━━━━
AUTO-CHECK RULES (Backend Validation)
━━━━━━━━━━━━━━━━━━━━━━

Before accepting answer, verify:
- If marks == 10 and answer has < 10 lines → INVALID (regenerate)
- If marks == 5 and answer has < 5 lines → INVALID (regenerate)
- If marks == 10 and "\\boxed" not in answer → INVALID (regenerate)
- If marks == 5+ and "\\boxed" not in answer → INVALID (regenerate)
- If quadratic equation and "D =" present but not in LaTeX → INVALID (regenerate)
- If marks == 10 and missing mandatory parts (Given, Formula, Substitution, Steps, Result) → INVALID (regenerate)

If any rule is violated, REWRITE the answer silently.

=== ADDITIONAL CRITICAL RULES ===

1. DISTRIBUTION COMPLIANCE:
   - Generate questions EXACTLY according to the requested distribution
   - NEVER exceed the total question limit specified
   - NEVER reduce the count below what's requested
   - Follow the teacher's requested marks, types, and remaining limits PRECISELY

2. OUTPUT FORMAT:
   - Output MUST ALWAYS be clean, valid JSON
   - NO markdown code blocks (no ```json or ```)
   - NO explanations before or after JSON
   - NO comments in JSON
   - Output ONLY the JSON object

3. QUESTION TYPES:
   - MCQ: Must have "options" array with exactly 4 options and "correct_answer" field
   - Short Answer (1-2 marks): Type "short", very brief answer
   - Descriptive (1-10 marks): Type "descriptive", answer length varies by marks (1 mark = 1-2 lines, 3 marks = 4-5 lines, etc.)

━━━━━━━━━━━━━━━━━━━━━━
📝 QUESTION FRAMING RULES (CRITICAL FOR QUALITY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] MANDATORY: All questions MUST be clear, unambiguous, and well-framed

1. QUESTION CLARITY REQUIREMENTS:
   ✅ Questions MUST be grammatically correct
   ✅ Questions MUST be complete sentences (unless formula-based)
   ✅ Questions MUST be unambiguous - only ONE correct interpretation
   ✅ Questions MUST test specific knowledge from the content
   ✅ Questions MUST be phrased in formal exam-style language
   ❌ NEVER use incomplete sentences (unless formula-based)
   ❌ NEVER use ambiguous phrasing that could have multiple interpretations
   ❌ NEVER use casual or conversational language
   ❌ NEVER use unclear pronouns or vague references

2. MCQ QUESTION FRAMING (SPECIFIC RULES):
   ✅ Question stem MUST be a complete, clear question or statement
   ✅ Question stem MUST be grammatically correct
   ✅ Question stem MUST clearly indicate what is being asked
   ✅ All 4 options MUST be grammatically consistent with the question stem
   ✅ All 4 options MUST be plausible and related to the topic
   ✅ Correct answer MUST be clearly the best/most accurate option
   ✅ Wrong options (distractors) MUST be plausible but clearly incorrect
   ✅ Options MUST be similar in length (avoid one very long option)
   ✅ Options MUST be parallel in structure (all start with same type of word if applicable)
   ❌ NEVER use "All of the above" or "None of the above" as options
   ❌ NEVER make the correct answer obviously different in format/length
   ❌ NEVER use options that are too similar to each other
   ❌ NEVER use options that are completely unrelated to the question

3. MCQ OPTIONS QUALITY:
   ✅ Option A, B, C, D must all be distinct and meaningful
   ✅ Distractors (wrong options) should test common misconceptions
   ✅ Distractors should be factually related to the topic
   ✅ All options should be approximately the same length
   ✅ Correct answer should not stand out due to formatting or length
   ❌ NEVER use obviously wrong options that are too easy to eliminate
   ❌ NEVER use options that are identical or nearly identical
   ❌ NEVER use options that are completely unrelated to the question topic

4. QUESTION STRUCTURE EXAMPLES:
   
   ✅ GOOD MCQ Examples:
   - "முதல் உலகப்போரின் போது பிரிட்டனைத் தாக்கிய நாடு எது?" (Which country attacked Britain during the First World War?)
   - "What is the value of x if 2x + 5 = 13?"
   - "Which of the following is the capital of France?"
   
   ❌ BAD MCQ Examples:
   - "First World War?" (incomplete, unclear)
   - "Who attacked?" (too vague, missing context)
   - "Britain was attacked by?" (incomplete sentence)
   
   ✅ GOOD Descriptive Examples:
   - "முதல் உலகப்போரின் காரணங்களை விளக்குக." (Explain the causes of the First World War.)
   - "Describe the process of photosynthesis."
   - "விவரிக்கவும்: முதல் உலகப்போரின் விளைவுகள்." (Describe: Effects of the First World War.)
   
   ❌ BAD Descriptive Examples:
   - "First World War causes" (not a complete sentence)
   - "Tell about photosynthesis" (too casual)
   - "What happened?" (too vague)

5. LANGUAGE-SPECIFIC FRAMING:
   - Tamil: Use formal question patterns like "X ஐ விளக்குக", "X என்றால் என்ன?", "X ஐ விவரிக்கவும்"
   - English: Use formal patterns like "Explain...", "Describe...", "What is...?", "Define..."
   - Hindi: Use formal patterns like "विवरण दीजिए", "समझाइए", "परिभाषित कीजिए"
   - All languages: Maintain formal, academic tone throughout

3A. LANGUAGE RULES (VERY IMPORTANT):
   Follow the exact exam-style phrasing used in the target language:
   
   - Tamil (ta-IN): Use formal கல்வி மொழி Tamil. ROTATE through these patterns (NEVER repeat):
     * "X என்றால் என்ன?" (What is X?) - Use ONCE only
     * "X இன் மதிப்பு கண்டுபிடிக்கவும்" (Find the value of X)
     * "X = Y என்றால், Z இன் மதிப்பு என்ன?" (If X = Y, what is the value of Z?) - Use ONCE only
     * "X ஐ கணக்கிடுக" (Calculate X)
     * "X மற்றும் Y இன் வேறுபாடு என்ன?" (What is the difference between X and Y?)
     * "X ஐ விளக்குக" (Explain X)
     * "X இன் மூலங்களை கண்டுபிடிக்கவும்" (Find the roots of X)
     * "X ஐ தீர்க்கவும்" (Solve X)
     * "X ஐ நிரூபிக்கவும்" (Prove X)
     * "X இன் தன்மையை பகுப்பாய்வு செய்க" (Analyze the nature of X)
     * "X ஐ விவரிக்கவும்" (Describe X)
     * "X இன் பண்புகளை எழுதுக" (Write the properties of X)
     [CRITICAL] ABSOLUTELY FORBIDDEN: NEVER use "f(x) = ... என்றால், f(...) என்றால் என்ன?" pattern more than ONCE
     [CRITICAL] Each question MUST use a DIFFERENT Tamil question format - NO repetition allowed
   
   - English (en): Use formal academic tone. Use patterns like: "Define …", "Explain …", "Describe …", "Write short notes on …", "Differentiate between …"
   
   - Hindi (hi-IN): Use शुद्ध हिन्दी / परीक्षा शैली. Use: "परिभाषित कीजिए", "समझाइए", "विवरण दीजिए", "लघु उत्तरीय प्रश्न", "दीर्घ उत्तरीय प्रश्न"
   
   - Telugu (te-IN): Use formal textbook Telugu. Use: "అంటే ఏమిటి?", "సంక్షిప్తంగా వ్రాయండి", "వివరించండి"
   
   - Kannada (kn-IN): Use school exam style Kannada. Use: "ಎಂದರೆ ಏನು?", "ಸಂಕ್ಷಿಪ್ತ ಉಕ್ಕಿ ಬರೆಯಿರಿ", "ವಿವರಿಸಿ"
   
   - Malayalam (ml-IN): Use formal academic Malayalam. Use: "എന്താണ്?", "വ്യാഖ്യാനിക്കുക", "സംക്ഷിപ്തമായി എഴുതുക"
   
   - Arabic (ar): Use Modern Standard Arabic. Use: "ما هو …؟", "اشرح", "وضح"
   
   - Spanish (es): Use neutral academic Spanish. Use: "Defina …", "Explique …", "Describa …"
   
   CRITICAL: All questions and answers MUST use the appropriate exam-style phrasing for the target language. Do NOT use casual or spoken language.

4. MARKS MATCHING & ANSWER LENGTH RULES (STRICT):
   - 1 Mark: 
     * MCQ: Question requiring formula/equation understanding with 4 distinct options
     * Short Answer: 1-2 lines only (very short, but MUST involve formula/equation)
     * Descriptive: 1-2 lines only (very brief, but MUST involve formula/equation if explicitly requested)
     * Example: "If x² = 16, find x" → "\\( x = \\pm 4 \\)" (MUST involve formula/equation, NOT simple recall)
   
   - 2 Marks:
     * MCQ: Question requiring brief reasoning with 4 meaningful options
     * Short Answer: 2-3 lines only (brief explanation, concise)
     * Example: "Explain X briefly." → "X is Y because Z. It also involves A." (2-3 lines max)
   
   - 3 Marks:
     * Descriptive ONLY: 4-5 lines (short descriptive answer)
     * Must be a complete short paragraph with basic explanation
     * Example: "Describe X." → "X is a concept that involves Y and Z. It is important because A. The main characteristics include B and C. Overall, X plays a key role in D." (4-5 lines)
   
   - 5 Marks:
     * Descriptive ONLY: 6-8 lines (medium descriptive answer)
     * Must include explanation with examples or details
     * Example: "Explain X in detail." → "X is a comprehensive concept that encompasses Y, Z, and A. It involves several key components including B, C, and D. The importance of X lies in E and F. For instance, G demonstrates how X works. Additionally, H shows the practical application. In conclusion, X is essential because I and J." (6-8 lines)
   
   - 10 Marks:
     * Descriptive/Analytical ONLY: 12-15+ lines (long descriptive / essay-style answer)
     * MUST include multiple sub-points, detailed analysis, examples, and comprehensive explanation
     * Structure: Introduction (2-3 lines) + Main points (8-10 lines) + Conclusion (2-3 lines)
     * Example: "Analyze X comprehensively." → [12-15+ lines with structured paragraphs covering introduction, multiple aspects, examples, analysis, and conclusion]
   
   - CRITICAL TYPE RESTRICTIONS:
     * MCQs: ONLY 1-2 marks (NEVER 3, 5, or 10 marks)
     * 10-mark questions: MUST be descriptive, NEVER MCQ
     * Short Answer: ONLY 1-2 marks
     * Descriptive: 1-10 marks (1 mark = very brief, 3+ marks = detailed)

5. ANSWER QUALITY REQUIREMENTS:
   - Count lines carefully - answers MUST match the specified line count for each mark
   - 1 mark: Maximum 2 lines (very concise)
   - 2 marks: 2-3 lines (brief but complete)
   - 3 marks: 4-5 lines (short paragraph)
   - 5 marks: 6-8 lines (detailed paragraph)
   - 10 marks: 12-15+ lines (comprehensive essay-style)
   - Answers must be educational, accurate, and appropriate for academic use

8. MATH ANSWER FORMAT RULES (STRICT):
   - 1 mark → 1–2 lines (no steps, direct answer only)
   - 2 marks → 2–3 lines (short explanation or simple formula)
   - 3 marks → 4–5 lines (small steps)
   - 5 marks → 6–8 lines (step-by-step with reasoning)
   - 10 marks → 12–15+ lines (full solution with explanation)

9. MATH QUESTION TYPE RULES:
   - MCQ (1 mark): Direct math problems, 4 options (A–D), only one correct answer, include correct_option.
   - Short Answer (1–3 marks): Use formulas, only key steps, concise.
   - Descriptive (5–10 marks): Clear step-by-step working, explain method, proper formulas.
   - Word Problems: Real-life math scenarios allowed; show step-by-step solution.
   - Algebra: Linear/quadratic equations, factorization, simplification.
   - Geometry: Area, perimeter, circumference, angle properties.
   - Coordinate Geometry: Distance formula, midpoint, slope.

6. CONTENT RULES:
   - Generate questions ONLY from provided study material
   - CRITICAL: NO duplicated questions - each question must be completely unique
   - This applies to ALL languages (English, Tamil, Hindi, Telugu, Kannada, Malayalam, Arabic, Spanish)
   - Even if questions are in different languages, they must cover different topics/concepts
   - Avoid rephrasing the same question in different ways - each question must test different knowledge
   - MCQs must be distinct and meaningful - avoid similar options or questions that test the same concept
   - All questions must be educational and appropriate
   - Never include questions about humans, body parts, or inappropriate content
   
   [CRITICAL] CRITICAL: QUESTION COMPLEXITY REQUIREMENT [CRITICAL]
   - ❌ NEVER generate simple arithmetic questions like "What is 3 + 4?" or "What is 5 × 2?"
   - ❌ NEVER generate trivial questions that can be answered without formulas or equations
   - ✅ Questions MUST involve formulas, equations, or require problem-solving steps
   - ✅ For Mathematics: Questions must require formulas, equations, derivations, or multi-step calculations
   - ✅ For Science: Questions must involve concepts, principles, formulas, or scientific reasoning
   - ✅ For other subjects: Questions must require understanding, analysis, or application of concepts
   - ✅ Questions should test understanding, not just recall of simple facts
   - Examples of GOOD questions:
     * "Using the quadratic formula, solve the equation x² + 5x + 6 = 0"
     * "Derive the formula for the area of a circle given its radius"
     * "If f(x) = 2x² - 3x + 1, find the value of f(2) using substitution"
     * "Calculate the discriminant of the quadratic equation 3x² - 7x + 2 = 0 and determine the nature of its roots"
   - Examples of BAD questions (DO NOT GENERATE):
     * "What is 3 + 4?" (too simple, no formula needed)
     * "What is 5 × 2?" (trivial arithmetic)
     * "What is the value of 10 - 3?" (simple subtraction)

6A. QUESTION FORMAT VARIATION (ABSOLUTELY MANDATORY - ZERO TOLERANCE FOR REPETITION):
   [CRITICAL][CRITICAL][CRITICAL] STRICTLY FORBIDDEN: NO REPETITION OF QUESTION FORMATS, OPENERS, STRUCTURES, OR FRAMES [CRITICAL][CRITICAL][CRITICAL]
   
   ABSOLUTE PROHIBITION:
   - ❌ NEVER repeat the same question opener in ANY two questions
   - ❌ NEVER repeat the same question structure in ANY two questions
   - ❌ NEVER repeat the same question frame/template in ANY two questions
   - ❌ NEVER use similar phrasing patterns across questions
   - ✅ EVERY question MUST be TOTALLY DIFFERENT in format, structure, and framing
   
   MANDATORY UNIQUE VARIATION (Each question MUST use a different approach):
   
   1. Question Opening MUST BE UNIQUE (Rotate systematically, NO duplicates):
      - Q1: "What is...?" / "Define..." / "Explain..." / "Describe..." / "State..." / "Write..."
      - Q2: "Find..." / "Calculate..." / "Solve..." / "Determine..." / "Evaluate..."
      - Q3: "Compare..." / "Differentiate..." / "Distinguish..." / "Contrast..."
      - Q4: "List..." / "Enumerate..." / "Mention..." / "Name..."
      - Q5: "Why...?" / "How...?" / "When...?" / "Where...?"
      - Q6: "Prove..." / "Show that..." / "Derive..." / "Establish..."
      - Q7: "Analyze..." / "Discuss..." / "Elaborate..." / "Illustrate..."
      - Q8+: Continue with NEW openers, NEVER reuse
   
   2. Question Structure MUST BE UNIQUE (Each question uses a different frame):
      - Frame 1: Direct question - "What is X?"
      - Frame 2: Statement + question - "X is Y. What is Z?"
      - Frame 3: Scenario-based - "Given X, find Y" / "If X, then what is Y?"
      - Frame 4: Comparison - "Compare X and Y" / "Differentiate between X and Y"
      - Frame 5: Application - "Apply X to solve Y" / "Using X, calculate Y"
      - Frame 6: Analysis - "Analyze the relationship between X and Y"
      - Frame 7: Problem-solving - "If X happens, what will be Y?"
      - Frame 8: Completion - "Complete the following: X = ?"
      - Frame 9+: Continue with NEW frames, NEVER reuse
   
   3. Mathematical Question Variations (Each must be unique):
      - Variation 1: Direct calculation - "Find the value of X"
      - Variation 2: Word problem - "A person has X items. If Y happens, find Z"
      - Variation 3: Proof/derivation - "Prove that X = Y"
      - Variation 4: Application - "Using formula X, calculate Y"
      - Variation 5: Comparison - "Compare the values of X and Y"
      - Variation 6: Analysis - "Analyze the nature of roots of equation X"
      - Variation 7+: Continue with NEW variations, NEVER reuse
   
   4. Language-Specific Variations (Rotate within language):
      - Tamil: Rotate through these formats (NEVER repeat):
        * "X என்றால் என்ன?" (What is X?)
        * "X இன் மதிப்பு கண்டுபிடிக்கவும்" (Find the value of X)
        * "X = Y என்றால், Z இன் மதிப்பு என்ன?" (If X = Y, what is the value of Z?)
        * "X ஐ கணக்கிடுக" (Calculate X)
        * "X மற்றும் Y இன் வேறுபாடு என்ன?" (What is the difference between X and Y?)
        * "X ஐ விளக்குக" (Explain X)
        * "X இன் மூலங்களை கண்டுபிடிக்கவும்" (Find the roots of X)
        * "X ஐ தீர்க்கவும்" (Solve X)
        * "X ஐ நிரூபிக்கவும்" (Prove X)
        * "X இன் தன்மையை பகுப்பாய்வு செய்க" (Analyze the nature of X)
        * "X ஐ விவரிக்கவும்" (Describe X)
        * "X இன் பண்புகளை எழுதுக" (Write the properties of X)
        * NEVER use "f(x) = ... என்றால், f(...) என்றால் என்ன?" pattern more than ONCE
        * NEVER repeat the same Tamil question structure
      - English: Rotate "Define", "Explain", "Describe", "Calculate", "Find", "Prove", "Analyze", "Compare"
      - Hindi: Rotate "परिभाषित कीजिए", "समझाइए", "गणना कीजिए", "सिद्ध कीजिए", "विवरण दीजिए"
      - Other languages: Rotate through available question starters, NEVER repeat
   
   5. Answer Format Variations (Vary even for same marks):
      - Answer 1: Start with definition, then explanation
      - Answer 2: Start with formula, then calculation
      - Answer 3: Start with given data, then solution
      - Answer 4: Use numbered steps (Step 1, Step 2, ...)
      - Answer 5: Use paragraph format
      - Answer 6: Use bullet points or list format
      - Answer 7+: Continue varying, NEVER repeat presentation style
   
   STRICT ENFORCEMENT CHECKLIST:
   Before outputting, verify:
   ✓ NO two questions share the same opener
   ✓ NO two questions share the same structure
   ✓ NO two questions share the same frame/template
   ✓ Each question is TOTALLY DIFFERENT from all others
   ✓ Answer presentation varies even for questions with same marks
   
   VIOLATION = INVALID OUTPUT: If ANY repetition is detected, the ENTIRE output is INVALID

7. JSON STRUCTURE:
   {
     "questions": [
       {
         "marks": 10,
         "type": "descriptive",
         "question": "Question text",
         "answer": "Answer text (12-15+ lines)"
       },
       {
         "marks": 2,
         "type": "short",
         "question": "Question text",
         "answer": "Answer text (2-3 lines)"
       },
       {
         "marks": 1,
         "type": "mcq",
         "question": "Question text",
         "options": ["Option A", "Option B", "Option C", "Option D"],
         "correct_answer": "Option A"
       }
     ]
   }

8. JSON VALIDATION:
   - Escape ALL special characters: \\" for quotes, \\n for newlines
   - Close ALL strings properly
   - No trailing commas
   - All brackets and braces must be balanced
   - JSON must be parseable by json.loads()

Remember: Follow the distribution EXACTLY. Never exceed limits. Match answer lengths precisely. Output ONLY valid JSON. No duplicated questions."""

def _validate_exam_quality(questions: List[Dict[str, Any]], difficulty: str) -> tuple[List[Dict[str, Any]], bool]:
    """
    Auto-check exam quality based on strict marks-based rules.
    Validates answer structure, length, LaTeX formatting, required elements, and format variation.
    Returns (validated_questions_list, has_format_repetition: bool)
    """
    validated_questions = []
    has_repetition = False
    has_hard_mode_violation = False  # Track hard mode violations
    has_invalid_10mark_answer = False  # Track invalid 10-mark answers for ALL subjects
    
    # Track question formats for variation check
    question_starters = []
    question_structures = []
    question_phrases = []  # Track full question phrasing patterns
    
    for idx, q in enumerate(questions):
        marks = q.get("marks", 0)
        answer = q.get("correct_answer", "") or q.get("answer", "")
        
        # Handle structured answer format (dict) vs string format
        if isinstance(answer, dict):
            # Check if it's English/Literature style (introduction, explanation, analysis, conclusion)
            if answer.get("introduction") or answer.get("explanation") or answer.get("analysis") or answer.get("conclusion"):
                # English literature format
                answer_parts = []
                if answer.get("introduction"):
                    answer_parts.append(f"Introduction: {answer.get('introduction')}")
                if answer.get("explanation"):
                    answer_parts.append(f"Explanation: {answer.get('explanation')}")
                if answer.get("analysis"):
                    answer_parts.append(f"Analysis: {answer.get('analysis')}")
                if answer.get("conclusion"):
                    answer_parts.append(f"Conclusion: {answer.get('conclusion')}")
                answer_text = "\n".join(answer_parts)
                answer_lines = len([line for line in answer_text.split('\n') if line.strip()])
                answer_lower = answer_text.lower()
            # Check if it's Science style (definition, explanation, example, conclusion)
            elif answer.get("definition") and (answer.get("explanation") or answer.get("example") or answer.get("conclusion")):
                answer_parts = []
                if answer.get("definition"):
                    answer_parts.append(f"Definition: {answer.get('definition')}")
                if answer.get("explanation"):
                    answer_parts.append(f"Explanation: {answer.get('explanation')}")
                if answer.get("example"):
                    answer_parts.append(f"Example: {answer.get('example')}")
                if answer.get("conclusion"):
                    answer_parts.append(f"Conclusion: {answer.get('conclusion')}")
                answer_text = "\n".join(answer_parts)
                answer_lines = len([line for line in answer_text.split('\n') if line.strip()])
                answer_lower = answer_text.lower()
            # Check if it's Social Science style (background, key_points, explanation, conclusion)
            elif answer.get("background") or answer.get("context") or answer.get("key_points"):
                answer_parts = []
                if answer.get("background"):
                    answer_parts.append(f"Background: {answer.get('background')}")
                if answer.get("context"):
                    answer_parts.append(f"Context: {answer.get('context')}")
                if answer.get("key_points"):
                    kp = answer.get("key_points")
                    if isinstance(kp, list):
                        answer_parts.append(f"Key Points: {' '.join(kp)}")
                    else:
                        answer_parts.append(f"Key Points: {kp}")
                if answer.get("explanation"):
                    answer_parts.append(f"Explanation: {answer.get('explanation')}")
                if answer.get("conclusion"):
                    answer_parts.append(f"Conclusion: {answer.get('conclusion')}")
                answer_text = "\n".join(answer_parts)
                answer_lines = len([line for line in answer_text.split('\n') if line.strip()])
                answer_lower = answer_text.lower()
            else:
                # Math-style structured format: convert to string for validation
                answer_parts = []
                if answer.get("given"):
                    answer_parts.append(f"Given: {answer.get('given')}")
                if answer.get("definition"):
                    answer_parts.append(f"Definition: {answer.get('definition')}")
                if answer.get("formula"):
                    answer_parts.append(f"Formula: {answer.get('formula')}")
                if answer.get("coefficients"):
                    answer_parts.append(f"Coefficients: {answer.get('coefficients')}")
                if answer.get("steps") and isinstance(answer.get("steps"), list):
                    for step in answer.get("steps", []):
                        answer_parts.append(str(step))
                if answer.get("function_values") and isinstance(answer.get("function_values"), list):
                    for value in answer.get("function_values", []):
                        answer_parts.append(str(value))
                if answer.get("final"):
                    answer_parts.append(f"Final: {answer.get('final')}")
                answer_text = "\n".join(answer_parts)
                answer_lines = len([line for line in answer_text.split('\n') if line.strip()])
                answer_lower = answer_text.lower()
        else:
            # String format: use as-is
            answer_text = str(answer) if answer else ""
            answer_lines = len([line for line in answer_text.split('\n') if line.strip()]) if answer_text else 0
            answer_lower = answer_text.lower()
        
        # Validation flags
        is_valid = True
        issues = []
        
        # Rule 1: Marks-based line count validation
        if marks == 10:
            # Require 12-15 lines minimum (not just 10) for ALL subjects
            if answer_lines < 12:
                is_valid = False
                has_invalid_10mark_answer = True
                issues.append(f"10-mark answer must have minimum 12-15 lines, got {answer_lines}. Short answers are INVALID.")
                issues.append("10-mark answer is too short. Must be treated as a board-exam answer script with full working.")
            
            # Detect answer format type
            is_social_science = False
            is_english_format = False
            is_science_format = False
            is_math_format = False
            
            if isinstance(answer, dict):
                # Check for Social Science format
                if answer.get("background") or answer.get("context") or answer.get("key_points"):
                    is_social_science = True
                # Check for English format
                elif answer.get("introduction") or answer.get("analysis"):
                    is_english_format = True
                # Check for Science format
                elif answer.get("definition") and (answer.get("explanation") or answer.get("example")):
                    is_science_format = True
                # Check for Math format
                elif answer.get("given") or answer.get("formula") or answer.get("steps"):
                    is_math_format = True
            else:
                # String format: detect by keywords
                has_background = any(word in answer_lower for word in ["background", "context", "பின்னணி", "पृष्ठभूमि", "background:", "context:"])
                has_key_points = any(word in answer_lower for word in ["key points", "key point", "முக்கிய புள்ளிகள்", "मुख्य बिंदु", "key points:", "key point:"])
                has_explanation = any(word in answer_lower for word in ["explanation", "explain", "விளக்கம்", "व्याख्या", "explanation:"])
                has_conclusion = any(word in answer_lower for word in ["conclusion", "முடிவு", "निष्कर्ष", "conclusion:"])
                has_introduction = any(word in answer_lower for word in ["introduction", "பரிச்சேதனை", "परिचय", "introduction:"])
                has_analysis = any(word in answer_lower for word in ["analysis", "பகுப்பாய்வு", "विश्लेषण", "analysis:"])
                has_given = any(word in answer_lower for word in ["given", "கொடுக்கப்பட்டது", "दिया गया", "given:", "provided"])
                has_formula = any(word in answer_lower for word in ["formula", "சூத்திரம்", "सूत्र", "formula:", "theorem", "theorem:"]) or "=" in answer_text or "D =" in answer_text
                
                # For 10-mark answers: if it has explanation+conclusion but missing background/key_points, treat as Social Science (invalid)
                if marks == 10 and has_explanation and has_conclusion and not has_background and not has_key_points and not has_given and not has_formula:
                    is_social_science = True  # Likely Social Science but missing required sections
                elif has_background or has_key_points:
                    is_social_science = True
                elif has_introduction or has_analysis:
                    is_english_format = True
                elif has_given or has_formula:
                    is_math_format = True
                else:
                    is_science_format = True  # Default to science if unclear
            
            # Check for mandatory parts based on format
            missing_parts = []
            
            if is_social_science:
                # Social Science: Background, Key Points, Explanation, Conclusion
                if isinstance(answer, dict):
                    has_background = (answer.get("background") or answer.get("context"))
                    has_key_points = answer.get("key_points")
                    has_explanation = answer.get("explanation")
                    has_conclusion = answer.get("conclusion")
                else:
                    has_background = any(word in answer_lower for word in ["background", "context", "பின்னணி", "पृष्ठभूमि", "background:", "context:"])
                    has_key_points = any(word in answer_lower for word in ["key points", "key point", "முக்கிய புள்ளிகள்", "मुख्य बिंदु", "key points:", "key point:"])
                    has_explanation = any(word in answer_lower for word in ["explanation", "explain", "விளக்கம்", "व्याख्या", "explanation:"])
                    has_conclusion = any(word in answer_lower for word in ["conclusion", "முடிவு", "निष्कर्ष", "conclusion:"])
                
                if not has_background:
                    missing_parts.append("Background/Context")
                if not has_key_points:
                    missing_parts.append("Key Points")
                if not has_explanation:
                    missing_parts.append("Explanation")
                if not has_conclusion:
                    missing_parts.append("Conclusion")
                
                if missing_parts:
                    is_valid = False
                    has_invalid_10mark_answer = True
                    issues.append(f"10-mark Social Science answer missing mandatory parts: {', '.join(missing_parts)}. Must include: Background/Context, Key Points (3-4 points), Explanation, Conclusion (total 12-15+ lines).")
            elif is_english_format:
                # English: Introduction, Explanation, Analysis, Conclusion
                if isinstance(answer, dict):
                    has_introduction = answer.get("introduction")
                    has_explanation = answer.get("explanation")
                    has_analysis = answer.get("analysis")
                    has_conclusion = answer.get("conclusion")
                else:
                    has_introduction = any(word in answer_lower for word in ["introduction", "பரிச்சேதனை", "परिचय", "introduction:"])
                    has_explanation = any(word in answer_lower for word in ["explanation", "explain", "விளக்கம்", "व्याख्या", "explanation:"])
                    has_analysis = any(word in answer_lower for word in ["analysis", "பகுப்பாய்வு", "विश्लेषण", "analysis:"])
                    has_conclusion = any(word in answer_lower for word in ["conclusion", "முடிவு", "निष्कर्ष", "conclusion:"])
                
                if not has_introduction:
                    missing_parts.append("Introduction")
                if not has_explanation:
                    missing_parts.append("Explanation")
                if not has_analysis:
                    missing_parts.append("Analysis")
                if not has_conclusion:
                    missing_parts.append("Conclusion")
                
                if missing_parts:
                    is_valid = False
                    has_invalid_10mark_answer = True
                    issues.append(f"10-mark English answer missing mandatory parts: {', '.join(missing_parts)}. Must include: Introduction, Explanation, Analysis, Conclusion (total 12-15+ lines).")
            elif is_science_format:
                # Science: Definition, Explanation, Example, Conclusion
                if isinstance(answer, dict):
                    has_definition = answer.get("definition")
                    has_explanation = answer.get("explanation")
                    has_example = answer.get("example")
                    has_conclusion = answer.get("conclusion")
                else:
                    has_definition = any(word in answer_lower for word in ["definition", "define", "வரையறை", "परिभाषा", "definition:"])
                    has_explanation = any(word in answer_lower for word in ["explanation", "explain", "விளக்கம்", "व्याख्या", "explanation:"])
                    has_example = any(word in answer_lower for word in ["example", "எடுத்துக்காட்டு", "उदाहरण", "example:"])
                    has_conclusion = any(word in answer_lower for word in ["conclusion", "முடிவு", "निष्कर्ष", "conclusion:"])
                
                if not has_definition:
                    missing_parts.append("Definition")
                if not has_explanation:
                    missing_parts.append("Explanation")
                if not has_example:
                    missing_parts.append("Example")
                if not has_conclusion:
                    missing_parts.append("Conclusion")
                
                if missing_parts:
                    is_valid = False
                    has_invalid_10mark_answer = True
                    issues.append(f"10-mark Science answer missing mandatory parts: {', '.join(missing_parts)}. Must include: Definition, Explanation, Example, Conclusion (total 12-15+ lines).")
            else:
                # Mathematics: Given, Definition, Formula, Steps, Explanation, Final
                if isinstance(answer, dict):
                    has_given = "given" in answer and answer.get("given")
                    has_definition = "definition" in answer and answer.get("definition")
                    has_formula = "formula" in answer and answer.get("formula") and str(answer.get("formula")).strip() != ""
                    has_steps = "steps" in answer and isinstance(answer.get("steps"), list) and len(answer.get("steps", [])) > 0
                    has_explanation = has_steps and len(answer.get("steps", [])) >= 3
                    has_conclusion = "final" in answer and answer.get("final")
                else:
                    has_given = any(word in answer_lower for word in ["given", "கொடுக்கப்பட்டது", "दिया गया", "given:", "provided"])
                    has_definition = any(word in answer_lower for word in ["definition", "define", "வரையறை", "परिभाषा"]) or any(word in answer_lower for word in ["concept", "term", "meaning"])
                    has_formula = any(word in answer_lower for word in ["formula", "சூத்திரம்", "सूत्र", "formula:", "theorem", "theorem:"]) or "=" in answer_text or "D =" in answer_text
                    has_steps = any(word in answer_lower for word in ["step", "படி", "चरण", "step 1", "step 2", "calculation"]) or any(char.isdigit() for char in answer_text.split('\n')[0] if len(answer_text.split('\n')) > 5)
                    has_explanation = any(word in answer_lower for word in ["explain", "reasoning", "therefore", "hence", "thus", "because", "விளக்கம்", "व्याख्या"]) or answer_lines >= 8
                    has_conclusion = any(word in answer_lower for word in ["conclusion", "final answer", "therefore", "thus", "hence", "முடிவு", "निष्कर्ष"]) or "final answer:" in answer_lower or "\\boxed" in answer_text or "boxed" in answer_lower
                
                if not has_given:
                    missing_parts.append("Given")
                if not has_definition and not has_formula:
                    missing_parts.append("Definition/Formula")
                if not has_formula:
                    missing_parts.append("Formula/Theorem")
                if not has_steps:
                    missing_parts.append("Step-by-step working")
                if not has_explanation:
                    missing_parts.append("Logical explanation")
                if not has_conclusion:
                    missing_parts.append("Final conclusion statement")
                
                if missing_parts:
                    is_valid = False
                    has_invalid_10mark_answer = True
                    issues.append(f"10-mark Mathematics answer missing mandatory parts: {', '.join(missing_parts)}. Must include: Given, Definition (if applicable), Formula/Theorem, Step-by-step working, Logical explanation, Final conclusion.")
                
                # Check for final answer (Mathematics only)
                if isinstance(answer, dict):
                    final_answer = answer.get("final", "")
                    has_boxed = "\\boxed" in str(final_answer) or "boxed" in str(final_answer).lower()
                else:
                    has_boxed = "\\boxed" in answer_text or "boxed" in answer_lower
                
                has_final_answer = "final answer:" in answer_lower or "\\boxed" in answer_text or "boxed" in answer_lower
                if not has_final_answer:
                    is_valid = False
                    issues.append("10-mark Mathematics answer must have clear final answer (use 'Final Answer:' prefix)")
        
        elif marks == 5:
            # Check if it's English literature format
            is_english_format = False
            if isinstance(answer, dict):
                is_english_format = bool(answer.get("introduction") or answer.get("explanation") or answer.get("analysis") or answer.get("conclusion"))
            
            if is_english_format:
                # English literature: validate structure, not line count
                has_intro = bool(answer.get("introduction"))
                has_expl = bool(answer.get("explanation"))
                has_anal = bool(answer.get("analysis"))
                has_conc = bool(answer.get("conclusion"))
                
                if not (has_intro and has_expl and has_anal and has_conc):
                    is_valid = False
                    missing = []
                    if not has_intro: missing.append("introduction")
                    if not has_expl: missing.append("explanation")
                    if not has_anal: missing.append("analysis")
                    if not has_conc: missing.append("conclusion")
                    issues.append(f"5-mark English answer missing required sections: {', '.join(missing)}")
                
                # For English, check that we have content (answer_lines should be > 0 after parsing)
                if answer_lines < 4:  # At least 4 sections with some content
                    is_valid = False
                    issues.append(f"5-mark English answer must have content in all sections, got {answer_lines} lines total")
            else:
                # Math or other format: check line count
                if answer_lines < 5:
                    is_valid = False
                    issues.append(f"5-mark answer must have minimum 5 lines, got {answer_lines}")
                if answer_lines > 7:
                    # Warning but not invalid
                    print(f"⚠️  5-mark answer has {answer_lines} lines (recommended: 5-7)")
                
                # Check for boxed answer (only for math)
                if isinstance(answer, dict):
                    final_answer = answer.get("final", "")
                    has_boxed = "\\boxed" in str(final_answer) or "boxed" in str(final_answer).lower()
                else:
                    has_boxed = "\\boxed" in answer_text or "boxed" in answer_lower
                
                if not has_boxed:
                    # Boxed answer recommended for 5 marks but not strictly required
                    print(f"⚠️  5-mark answer should have boxed final answer")
        
        elif marks == 2:
            if answer_lines > 3:
                is_valid = False
                issues.append(f"2-mark answer must have maximum 3 lines, got {answer_lines}")
            if answer_lines < 1:
                is_valid = False
                issues.append("2-mark answer must have at least 1 line")
        
        elif marks == 1:
            if answer_lines > 2:
                is_valid = False
                issues.append(f"1-mark answer must have maximum 2 lines, got {answer_lines}")
            if answer_lines < 1:
                is_valid = False
                issues.append("1-mark answer must have at least 1 line")
            # Check for no explanation (1 mark should be direct)
            if any(word in answer_lower for word in ["because", "therefore", "hence", "since", "explain", "ஏனெனில்", "क्योंकि"]):
                print(f"⚠️  1-mark answer should not have explanation (direct answer only)")
        
        # Rule 2: LaTeX validation for math expressions
        # Check if answer contains math-like content but not in LaTeX
        math_indicators = ["=", "+", "-", "*", "/", "^", "x", "y", "z", "a", "b", "c", "D =", "sqrt", "frac"]
        has_math = any(indicator in answer_text for indicator in math_indicators)
        has_latex = "\\(" in answer_text or "\\[" in answer_text or "\\boxed" in answer_text
        
        if has_math and not has_latex and marks >= 2:
            # Warning for math without LaTeX
            print(f"⚠️  Question with marks {marks} contains math but may not be in LaTeX format")
        
        # Rule 3: Quadratic equation discriminant check
        # For 1-mark questions, simple notation is acceptable (no LaTeX required)
        if "D =" in answer_text or "discriminant" in answer_lower or "பாகுபாடு" in answer_text:
            if marks > 1:  # Only require LaTeX for 2+ marks
                if "\\(" not in answer_text and "\\[" not in answer_text:
                    is_valid = False
                    issues.append("Discriminant formula must be in LaTeX format: \\( D = b^2 - 4ac \\)")
            else:
                # For 1-mark, simple notation like "D = b² - 4ac" is acceptable
                print(f"ℹ️  1-mark question with discriminant - simple notation acceptable")
        
        # Rule 4: Boxed answer check for 5+ marks (already handled above for 5 and 10 marks, but check for other marks >= 5)
        if marks >= 5 and marks not in [5, 10]:
            if isinstance(answer, dict):
                final_answer = answer.get("final", "")
                has_boxed = "\\boxed" in str(final_answer) or "boxed" in str(final_answer).lower()
            else:
                has_boxed = "\\boxed" in answer_text or "boxed" in answer_lower
            
            if not has_boxed:
                is_valid = False
                issues.append(f"{marks}-mark answer must have boxed final answer: \\( \\boxed{{answer}} \\)")
        
        # Log validation results
        if not is_valid:
            print(f"❌ Question validation failed (Marks: {marks}):")
            for issue in issues:
                print(f"   - {issue}")
            # Use answer_text for preview (works for both string and dict formats)
            preview = answer_text[:200] if answer_text and len(answer_text) > 200 else answer_text
            print(f"   Answer preview: {preview}...")
            # Note: We don't regenerate here, just log the issue
            # The AI should follow the prompt rules, but we flag violations
        else:
            print(f"✅ Question validated (Marks: {marks}, Lines: {answer_lines})")
        
        # Track question format for variation check
        question_text = q.get("question", "").strip()
        if question_text:
            # CRITICAL: Check for simple arithmetic in HARD mode
            if difficulty == "hard":
                question_lower = question_text.lower()
                
                # Pattern 1: Simple arithmetic questions
                simple_arithmetic_patterns = [
                    r'what is the value of \d+\s*[+\-×÷/]\s*\d+\?',
                    r'what is \d+\s*[+\-×÷/]\s*\d+\?',
                    r'calculate \d+\s*[+\-×÷/]\s*\d+',
                    r'find the value of \d+\s*[+\-×÷/]\s*\d+',
                    r'what is \d+\s*minus\s*\d+',
                    r'what is \d+\s*plus\s*\d+',
                    r'what is \d+\s*divided by\s*\d+',
                    r'what is \d+\s*times\s*\d+',
                    r'what is \d+\s*multiplied by\s*\d+',
                ]
                
                # Pattern 2: Symbol identification questions
                symbol_identification_patterns = [
                    r'which symbol represents',
                    r'what symbol represents',
                    r'which symbol means',
                    r'what does the.*symbol mean',
                    r'which symbol is used for',
                ]
                
                # Check for simple arithmetic
                for pattern in simple_arithmetic_patterns:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_valid = False
                        has_hard_mode_violation = True
                        issues.append(f"HARD mode violation: Simple arithmetic question detected. Hard mode requires formulas, derivations, or multi-step problem-solving, not basic arithmetic like '{question_text[:50]}...'")
                        print(f"❌ HARD MODE VIOLATION: Question contains simple arithmetic: {question_text[:100]}")
                        break
                
                # Check for symbol identification
                for pattern in symbol_identification_patterns:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_valid = False
                        has_hard_mode_violation = True
                        issues.append(f"HARD mode violation: Symbol identification question detected. Hard mode requires complex problem-solving, not basic symbol recognition like '{question_text[:50]}...'")
                        print(f"❌ HARD MODE VIOLATION: Question is basic symbol identification: {question_text[:100]}")
                        break
                
                # Check if question is too simple (only numbers and basic operators, no formulas/concepts)
                # Count mathematical complexity indicators
                has_formula = any(word in question_lower for word in ["formula", "theorem", "derive", "prove", "solve", "calculate", "find", "determine", "analyze"])
                has_variables = bool(re.search(r'\b[a-z]\b', question_text))  # Has variables like x, y, a, b
                has_complex_math = any(word in question_lower for word in ["quadratic", "equation", "function", "derivative", "integral", "matrix", "root", "discriminant"])
                has_simple_math_only = bool(re.search(r'\d+\s*[+\-×÷/]\s*\d+', question_text))  # Only simple arithmetic
                
                # If it has simple math but no formulas/variables/complex concepts, it's too simple
                if has_simple_math_only and not (has_formula or has_variables or has_complex_math):
                    is_valid = False
                    has_hard_mode_violation = True
                    issues.append(f"HARD mode violation: Question is too simple (only basic arithmetic). Hard mode requires formulas, equations, or multi-step problem-solving.")
                    print(f"❌ HARD MODE VIOLATION: Question is too simple (basic arithmetic only): {question_text[:100]}")
            
            # Extract question starter (first few words)
            words = question_text.split()
            if words:
                starter = words[0].lower()
                question_starters.append(starter)
                
                # Detect specific repetitive patterns (especially for Tamil)
                # Pattern: "f(x) = ... என்றால், f(...) என்றால் என்ன?" - FORBIDDEN if repeated
                tamil_repetitive_pattern = r'[a-zA-Z]\([^)]+\)\s*=\s*[^,]+,\s*[a-zA-Z]\([^)]+\)\s*என்றால்\s*என்ன'
                if re.search(tamil_repetitive_pattern, question_text, re.IGNORECASE):
                    question_phrases.append("tamil_function_pattern")  # Mark as repetitive pattern
                
                # Detect question structure type
                if any(word in question_text.lower() for word in ["compare", "differentiate", "distinguish", "contrast", "ஒப்பிட", "வேறுபாடு"]):
                    structure = "comparison"
                elif any(word in question_text.lower() for word in ["given", "if", "when", "suppose", "கொடுக்கப்பட்ட", "என்றால்"]):
                    structure = "scenario"
                elif any(word in question_text.lower() for word in ["prove", "show", "derive", "establish", "நிரூபிக்க", "காட்ட"]):
                    structure = "proof"
                elif any(word in question_text.lower() for word in ["analyze", "discuss", "elaborate", "பகுப்பாய்வு", "விவாதிக்க"]):
                    structure = "analysis"
                elif "?" in question_text or "என்ன" in question_text:
                    structure = "direct_question"
                else:
                    structure = "statement"
                question_structures.append(structure)
                
                # Track full question phrase pattern (first 10 words) for repetition detection
                phrase_pattern = " ".join(words[:10]).lower()
                question_phrases.append(phrase_pattern)
                
                # CRITICAL: Detect specific Tamil repetitive pattern "f(x) = ... என்றால், f(...) என்றால் என்ன?"
                tamil_repetitive_pattern = r'[a-zA-Z]\([^)]+\)\s*=\s*[^,]+,\s*[a-zA-Z]\([^)]+\)\s*என்றால்\s*என்ன'
                if re.search(tamil_repetitive_pattern, question_text, re.IGNORECASE):
                    question_phrases.append("TAMIL_FUNCTION_PATTERN")  # Mark as repetitive pattern
        
        validated_questions.append(q)
    
    # CRITICAL: Check for Tamil repetitive pattern "f(x) = ... என்றால், f(...) என்றால் என்ன?"
    tamil_pattern_count = question_phrases.count("TAMIL_FUNCTION_PATTERN")
    if tamil_pattern_count >= 2:
        print(f"[CRITICAL] CRITICAL: Detected {tamil_pattern_count} questions with repetitive Tamil pattern 'f(x) = ... என்றால், f(...) என்றால் என்ன?'")
        print(f"   This pattern MUST NOT be repeated. Each question must use a DIFFERENT format.")
        return validated_questions, True  # Return True to trigger regeneration
    
    # Check for phrase pattern repetition (STRICT - checks first 3-4 words)
    # For small question sets (≤5), be more lenient - only flag if 3+ questions share same phrase
    # For larger sets, flag if 2+ questions share same phrase
    min_repetition_count = 3 if len(validated_questions) <= 5 else 2
    
    if len(question_phrases) > 1:
        phrase_counts = {}
        repeated_phrases = []
        
        for i, phrase in enumerate(question_phrases):
            if phrase not in phrase_counts:
                phrase_counts[phrase] = []
            phrase_counts[phrase].append(i + 1)
        
        for phrase, question_nums in phrase_counts.items():
            if len(question_nums) >= min_repetition_count:
                repeated_phrases.append((phrase, question_nums))
                print(f"❌ PHRASE REPETITION DETECTED: Questions {', '.join(map(str, question_nums))} start with same phrase '{phrase}'")
                has_repetition = True
    
    # Check for format repetition (STRICT - but lenient for small sets)
    # For small question sets (≤5), only flag if 3+ questions share same starter
    # For larger sets, flag if 2+ questions share same starter
    min_repetition_count = 3 if len(validated_questions) <= 5 else 2
    
    if len(question_starters) > 1:
        starter_counts = {}
        repeated_starters = []
        
        # Count occurrences of each starter
        for i, starter in enumerate(question_starters):
            if starter not in starter_counts:
                starter_counts[starter] = []
            starter_counts[starter].append(i + 1)  # Question number (1-indexed)
        
        # Find any repetitions (even non-consecutive)
        for starter, question_nums in starter_counts.items():
            if len(question_nums) >= min_repetition_count:
                repeated_starters.append((starter, question_nums))
                print(f"❌ FORMAT REPETITION DETECTED: Questions {', '.join(map(str, question_nums))} all start with '{starter}'")
                has_repetition = True
        
        # Check consecutive repetition
        consecutive_same = 0
        for i in range(1, len(question_starters)):
            if question_starters[i] == question_starters[i-1]:
                consecutive_same += 1
                print(f"❌ CONSECUTIVE FORMAT REPETITION: Questions {i} and {i+1} both start with '{question_starters[i]}'")
                has_repetition = True
        
        if repeated_starters:
            print(f"[CRITICAL] CRITICAL WARNING: Found {len(repeated_starters)} question opener(s) repeated across the set. Each question MUST have a UNIQUE opener!")
        elif consecutive_same > 0:
            print(f"⚠️  WARNING: Found {consecutive_same} consecutive question(s) with same opener. Questions should vary in format/phrasing.")
    
    # Check for structure repetition (STRICT - but lenient for small sets)
    # For small question sets (≤5), only flag if 4+ questions share same structure
    # For larger sets, flag if 3+ questions share same structure
    min_structure_repetition = 4 if len(validated_questions) <= 5 else 3
    
    if len(question_structures) > 1:
        structure_counts = {}
        repeated_structures = []
        
        # Count occurrences of each structure
        for i, structure in enumerate(question_structures):
            if structure not in structure_counts:
                structure_counts[structure] = []
            structure_counts[structure].append(i + 1)  # Question number (1-indexed)
        
        # Find any repetitions (even non-consecutive)
        for structure, question_nums in structure_counts.items():
            if len(question_nums) >= min_structure_repetition:
                repeated_structures.append((structure, question_nums))
                print(f"❌ STRUCTURE REPETITION DETECTED: Questions {', '.join(map(str, question_nums))} all use '{structure}' structure")
                has_repetition = True
        
        # Check consecutive repetition
        consecutive_same_structure = 0
        for i in range(1, len(question_structures)):
            if question_structures[i] == question_structures[i-1]:
                consecutive_same_structure += 1
                print(f"❌ CONSECUTIVE STRUCTURE REPETITION: Questions {i} and {i+1} both use '{question_structures[i]}' structure")
                has_repetition = True
        
        if repeated_structures:
            print(f"[CRITICAL] CRITICAL WARNING: Found {len(repeated_structures)} question structure(s) repeated across the set. Each question MUST have a UNIQUE structure!")
        elif consecutive_same_structure > 0:
            print(f"⚠️  WARNING: Found {consecutive_same_structure} consecutive question(s) with same structure. Questions should vary in structure.")
    
    # Check for low variation (less than 70% unique starters)
    # For small question sets (≤5), be more lenient (allow 60% variation)
    # For larger sets, require 70% variation
    min_variation_threshold = 0.6 if len(validated_questions) <= 5 else 0.7
    unique_starters_ratio = len(set(question_starters)) / len(question_starters) if question_starters else 0
    
    if len(question_starters) == len(validated_questions) and unique_starters_ratio < min_variation_threshold:
        print(f"⚠️  WARNING: Low format variation detected. Only {len(set(question_starters))} unique starters out of {len(question_starters)} questions ({unique_starters_ratio*100:.1f}% variation).")
        print(f"   Recommendation: Use more varied question formats (What/Define/Explain/Find/Calculate/Solve/Compare/etc.)")
        # Only treat as repetition if variation is very low (<50% for small sets, <60% for larger sets)
        if unique_starters_ratio < (0.5 if len(validated_questions) <= 5 else 0.6):
            has_repetition = True
    
    # CRITICAL: If hard mode violations detected, trigger regeneration
    if has_hard_mode_violation:
        print(f"[CRITICAL] CRITICAL: HARD MODE VIOLATIONS DETECTED - Regenerating questions to ensure complexity...")
        return validated_questions, True  # Return True to trigger regeneration
    
    # CRITICAL: If 10-mark answers are invalid (missing parts or too short) for ANY subject, trigger regeneration
    if has_invalid_10mark_answer:
        print(f"[CRITICAL] CRITICAL: 10-MARK ANSWERS ARE INVALID - Missing mandatory sections or too short (<12 lines). Regenerating to ensure all required sections and 12-15+ lines...")
        return validated_questions, True  # Return True to trigger regeneration
    
    return validated_questions, has_repetition

def generate_qna(
    text_content: str,
    difficulty: str,
    qna_type: str,
    num_questions: int,
    marks_pattern: str = "mixed",
    target_language: str = "english",
    remaining_questions: Optional[int] = None,
    distribution_list: Optional[List[Dict[str, Any]]] = None,
    subject: Optional[str] = None,  # Explicit subject selection: mathematics, english, science, social_science, general
    num_parts: Optional[int] = None  # Number of parts selected (for dynamic content limit)
) -> Dict[str, Any]:
    """
    Generate Q/A from text using OpenAI
    
    Args:
        text_content: Text to generate questions from
        difficulty: Difficulty level (easy, medium, hard)
        qna_type: Question type (mcq, descriptive, mixed)
        num_questions: Number of questions to generate
        marks_pattern: Marks pattern - "mixed", "1", "2", "3", "5", or "10"
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI API key not configured")
    
    def _type_for_marks(m) -> str:
        try:
            mv = int(m)
        except Exception:
            return "descriptive"
        if mv == 1:
            return "mcq"
        if mv == 2:
            return "short"
        return "descriptive"

    # Build distribution list if not provided
    if distribution_list is None:
        if marks_pattern == "custom":
            # Custom distribution should be provided via distribution_list
            raise ValueError("Custom distribution requires distribution_list parameter")
        distribution_list = _build_distribution_list(marks_pattern or "mixed", qna_type, num_questions)
    
    # Validate distribution list format
    if not isinstance(distribution_list, list):
        raise ValueError(f"distribution_list must be a list, got {type(distribution_list)}")
    
    if len(distribution_list) == 0:
        raise ValueError("distribution_list cannot be empty")
    
    # Validate each item in distribution list has required keys
    for idx, item in enumerate(distribution_list):
        if not isinstance(item, dict):
            raise ValueError(f"distribution_list[{idx}] must be a dict, got {type(item)}")
        required_keys = ["marks", "count", "type"]
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            raise ValueError(f"distribution_list[{idx}] missing required keys: {missing_keys}. Item: {item}")
        # Validate values are of correct type
        if not isinstance(item.get("marks"), (int, float)) or item.get("marks", 0) <= 0:
            raise ValueError(f"distribution_list[{idx}]['marks'] must be a positive number, got {item.get('marks')}")
        if not isinstance(item.get("count"), int) or item.get("count", 0) <= 0:
            raise ValueError(f"distribution_list[{idx}]['count'] must be a positive integer, got {item.get('count')}")
        if not isinstance(item.get("type"), str) or item.get("type", "") not in ["mcq", "short", "descriptive"]:
            raise ValueError(f"distribution_list[{idx}]['type'] must be 'mcq', 'short', or 'descriptive', got {item.get('type')}")
        # Normalize type from marks to avoid mismatches (e.g., 10-mark MCQ)
        normalized_type = _type_for_marks(item.get("marks"))
        if item.get("type") != normalized_type:
            print(f"⚠️  Normalizing type for distribution item {idx}: {item.get('type')} -> {normalized_type}")
            item["type"] = normalized_type
    
    # Calculate remaining questions (use provided or default to num_questions)
    if remaining_questions is None:
        remaining_questions = num_questions
    
    # Ensure we don't exceed remaining questions
    total_requested = sum(item.get("count", 0) for item in distribution_list)
    if total_requested > remaining_questions:
        # Adjust distribution proportionally
        scale_factor = remaining_questions / total_requested
        for item in distribution_list:
            item["count"] = max(1, int(item["count"] * scale_factor))
        # Recalculate to ensure exact match
        total_after_scale = sum(item.get("count", 0) for item in distribution_list)
        if total_after_scale < remaining_questions:
            # Add remaining to first item
            diff = remaining_questions - total_after_scale
            if distribution_list:
                distribution_list[0]["count"] += diff
    
    # Normalize top-level marks/type when using simple pattern (non-custom)
    if marks_pattern != "custom" and marks_pattern != "mixed":
        qna_type = _type_for_marks(marks_pattern)

    # Normalize target language
    target_language = target_language.lower().strip() if target_language else "english"
    
    # Language mapping for clarity
    language_names = {
        "english": "English",
        "tamil": "Tamil",
        "hindi": "Hindi",
        "arabic": "Arabic",
        "spanish": "Spanish",
        "telugu": "Telugu",
        "kannada": "Kannada",
        "malayalam": "Malayalam"
    }
    target_language_name = language_names.get(target_language, target_language.capitalize())
    
    # Detect subject from text content
    # Use provided subject or detect from content
    if subject and subject != "general":
        detected_subject = subject.lower()
        print(f"📚 Using selected subject: {detected_subject}")
    else:
        detected_subject = detect_subject(text_content)
        print(f"📚 Detected subject: {detected_subject}")
    
    # Subject-specific answer structure instructions
    subject_instructions = {
        "mathematics": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: MATHEMATICS - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] CRITICAL: This is MATHEMATICS - Follow these rules STRICTLY:

1. ANSWER FORMAT (MANDATORY):
   ✅ USE these headings ONLY:
      - Given
      - Formula
      - Calculation / Steps
      - Final Answer
   
   ❌ NEVER use:
      - Introduction
      - Explanation (unless explaining a mathematical concept)
      - Analysis (unless analyzing a mathematical problem)
      - Conclusion (unless concluding a proof)
      - Background/Context
      - Key Points

2. NOTATION RULES:
   ✅ Use exam-friendly notation (NO LaTeX in final answers for 10-mark questions)
   ✅ For 1-5 marks: LaTeX is acceptable
   ✅ For 10 marks: Convert LaTeX to handwritten-style notation
   ✅ Example: Use "x²" instead of "x^2", "√" instead of "sqrt", "π" instead of "pi"
   
3. 10-MARK QUESTIONS (STRICT):
   ✅ MUST include ALL of these sections:
      - Given: State the problem clearly
      - Formula: State the formula/theorem used
      - Calculation/Steps: Show step-by-step working with substitution
      - Final Answer: Boxed final answer
   
   ✅ Minimum 10-15 lines
   ✅ Show every calculation step
   ✅ Use student-written notation (like handwritten exam scripts)

4. QUESTION COMPLEXITY:
   ✅ Questions MUST involve formulas, equations, or multi-step calculations
   ✅ NO simple arithmetic like "What is 3 + 4?"
   ✅ Examples of GOOD questions:
      - "Using the quadratic formula, solve x² + 5x + 6 = 0"
      - "Derive the formula for the area of a circle"
      - "Calculate the discriminant and determine the nature of roots"
""",
        "english": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: ENGLISH (Literature/Language) - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ USE these headings:
   - Introduction
   - Explanation
   - Analysis
   - Conclusion

✅ Write in paragraph form
✅ Use literary terms where applicable (theme, tone, irony, humor, metaphor, simile, etc.)
✅ Answer must read like a literature exam answer

❌ NEVER use: Given, Formula, Calculation (these are for Mathematics only)
""",
        "tamil": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: TAMIL (Literature/Language) - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ USE these headings (in Tamil):
   - அறிமுகம் (Introduction)
   - விளக்கம் (Explanation)
   - பகுப்பாய்வு (Analysis)
   - முடிவு (Conclusion)

✅ Write in Tamil (exam-style Tamil, not spoken Tamil)
✅ Use Tamil literary terms where applicable
✅ Answer must read like a Tamil literature exam answer
✅ Use proper Tamil grammar and vocabulary
✅ Follow Tamil exam paper conventions

❌ NEVER use: Given, Formula, Calculation (these are for Mathematics only)
❌ NEVER use spoken Tamil - use exam-style formal Tamil
""",
        "science": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: SCIENCE (Theory) - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ USE these headings:
   - Definition
   - Explanation
   - Example (if needed)
   - Conclusion

✅ Focus on scientific concepts and principles
✅ Include relevant examples or applications

❌ DO NOT use: Given, Formula, Calculation (unless it's a calculation-based science question)
""",
        "social_science": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: SOCIAL SCIENCE - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ USE these headings:
   - Background / Context
   - Key Points
   - Explanation
   - Conclusion

✅ Provide historical/geographical context
✅ List key points clearly
✅ Explain relationships and causes

❌ DO NOT use: Given, Formula, Calculation (these are for Mathematics only)
""",
        "general": """
━━━━━━━━━━━━━━━━━━━━━━
SUBJECT: GENERAL - ANSWER STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ USE appropriate structure based on content:
   - If mathematical content detected: Use Mathematics structure (Given, Formula, Calculation, Final Answer)
   - If literature/English content: Use English structure (Introduction, Explanation, Analysis, Conclusion)
   - If Tamil content detected: Use Tamil structure (அறிமுகம், விளக்கம், பகுப்பாய்வு, முடிவு)
   - If science content: Use Science structure (Definition, Explanation, Example, Conclusion)
   - If social science content: Use Social Science structure (Background, Key Points, Explanation, Conclusion)

❌ DO NOT use math-style headings (Given, Formula, Calculation) unless content is clearly mathematical
"""
    }
    
    subject_instruction = subject_instructions.get(detected_subject, subject_instructions["general"])
    
    # Build distribution string for prompt
    # Use safe dictionary access to avoid KeyError
    distribution_string = "\n".join([
        f"- {item.get('count', 0)} questions of {item.get('marks', 0)} marks ({item.get('type', 'descriptive')})"
        for item in distribution_list
    ])
    
    # Calculate total from distribution
    total_from_distribution = sum(item.get("count", 0) for item in distribution_list)
    actual_num_questions = min(total_from_distribution, remaining_questions)
    
    # Build marks-based structure instructions
    # Define LaTeX commands as separate strings to avoid \f (form feed) escape sequence issues
    # Using string concatenation to build LaTeX expressions
    latex_frac_cmd = r'\frac'  # Raw string to avoid \f interpretation
    latex_boxed_cmd = r'\boxed'  # Raw string to avoid \b interpretation
    
    # Build marks structure - NOTE: Structure headings depend on subject (see subject_instruction above)
    marks_structure = f"""
━━━━━━━━━━━━━━━━━━━━━━
MARK-BASED LENGTH CONTROL (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

Marks control LENGTH only (regardless of subject):
- 1 mark → one sentence (1-2 lines)
- 2 marks → short paragraph (2-3 lines)
- 5 marks → explained answer (7-9 lines)
- 10 marks → detailed, structured answer (9-10 lines minimum)

Subject controls FORMAT (headings and structure):
- Mathematics: Use Given, Formula, Calculation/Steps, Final Answer
- English: Use Introduction, Explanation, Analysis, Conclusion
- Science: Use Definition, Explanation, Example, Conclusion
- Social Science: Use Background/Context, Key Points, Explanation, Conclusion

━━━━━━━━━━━━━━━━━━━━━━
MARKS-BASED STRUCTURE EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━

• 1 MARK:
  - ONE direct answer only
  - NO explanation, NO derivation, NO steps
  - Maximum 1-2 lines
  - Example: "What is 2+3?" → "\\( 2 + 3 = 5 \\)"

• 2 MARKS:
  - Short answer
  - 1 formula OR brief explanation
  - Maximum 2-3 lines
  - Brief working if needed (for math)
  - Example: "Solve \\( x + 5 = 10 \\)" → "\\( x = 10 - 5 = 5 \\)"

• 5 MARKS:
  - Step-wise solution REQUIRED (for math)
  - OR structured explanation (for other subjects)
  - 7-9 lines minimum
  - Show working clearly (math) OR explain clearly (other subjects)
  - Structure depends on subject (see subject rules above)

• 10 MARKS (STRICT BOARD-EXAM RULES - NO EXCEPTIONS):
  - Answer MUST be at least 9-10 lines minimum (NO SHORTCUTS, NO SHORT ANSWERS)
  - Short answers are INVALID and will be rejected
  - Treat every 10-mark question as a board-exam answer script
  - Structure depends on subject:
    * Mathematics: Given → Formula → Calculation/Steps → Final Answer
    * English: Introduction → Explanation → Analysis → Conclusion
    * Science: Definition → Explanation → Example → Conclusion
    * Social Science: Background/Context → Key Points → Explanation → Conclusion
  - Each section must be clearly separated and well-explained
  - NO abbreviated answers - full working/explanation is mandatory

EXAMPLE FOR 10 MARKS (Tamil):
Q2. \\( x^2 + 6x + 9 = 0 \\) என்ற சமன்பாட்டின் மூலங்களை கண்டுபிடிக்கவும்.

✓ Correct Answer:

கொடுக்கப்பட்டது:
\\( x^2 + 6x + 9 = 0 \\)

இங்கு,
\\( a = 1, b = 6, c = 9 \\)

பாகுபாடு (Discriminant) சூத்திரம்:
\\( D = b^2 - 4ac \\)

மதிப்பீடு:
\\( D = 6^2 - 4(1)(9) \\)
\\( D = 36 - 36 = 0 \\)

\\( D = 0 \\) என்பதால், சமன்பாட்டிற்கு ஒரு மையமான மூலம் உண்டு.

மூலம்:
\\[
x = (-b)/(2a) = (-6)/(2(1)) = -3
\\]

அதனால், சமன்பாட்டின் மூலம்:
\\[
{latex_boxed_cmd}{{x = -3}}
\\]
"""
    
    # Calculate dynamic content limit based on ACTUAL content size
    # This adapts to varying content sizes per part, ensuring we use all available content
    # while staying within safe token limits
    total_content_length = len(text_content)
    
    # Define maximum safe limits based on number of parts (to prevent token overflow)
    # gpt-4o-mini has 128,000 token limit
    # The prompt is very long (includes all rules, examples, etc.), so we need to be conservative
    # Based on error: 260K chars resulted in 152K tokens, so ~0.58 tokens per char
    # But prompt adds significant tokens, so we need to leave more room
    # Safe limits: leave ~40K tokens for prompt and response
    max_safe_limits = {
        1: 150000,   # Single part: up to 150K chars (~88K tokens for content + 40K for prompt/response)
        2: 200000,   # 2 parts: up to 200K chars (~116K tokens total)
        3: 250000,   # 3-4 parts: up to 250K chars (~145K tokens total)
        4: 250000,
        5: 300000,   # 5-6 parts: up to 300K chars (~174K tokens total)
        6: 300000,
        7: 350000,   # 7-8 parts: up to 350K chars (~203K tokens total - may exceed, but try)
        8: 350000
    }
    
    # Get the maximum safe limit for this number of parts
    num_parts_actual = num_parts or 1
    max_safe_limit = max_safe_limits.get(num_parts_actual, max_safe_limits.get(8, 1500000))
    
    # Use ALL available content if it's within safe limits, otherwise cap at safe limit
    # This ensures we never ignore content unnecessarily, but also don't exceed token limits
    if total_content_length <= max_safe_limit:
        # Content fits within safe limit - use ALL of it
        content_limit = total_content_length
        print(f"✅ Content extraction: Using ALL {total_content_length:,} chars (within safe limit of {max_safe_limit:,})")
    else:
        # Content exceeds safe limit - use up to safe limit
        content_limit = max_safe_limit
        percentage_used = (max_safe_limit / total_content_length) * 100
        print(f"⚠️ Content extraction: Using {max_safe_limit:,} of {total_content_length:,} chars ({percentage_used:.1f}%) - capped at safe limit")
    
    # Log final content usage
    actual_used = min(content_limit, total_content_length)
    print(f"📚 Content extraction: Total={total_content_length:,} chars, Using={actual_used:,} chars (limit={content_limit:,}), Parts={num_parts_actual}")
    
    # Build subject-specific warning for 10-mark answers
    subject_warning = ""
    subject_lower = detected_subject.lower()
    if subject_lower in ["social_science", "social science"]:
        subject_warning = """
━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL][CRITICAL][CRITICAL] CRITICAL REMINDER FOR 10-MARK SOCIAL SCIENCE ANSWERS [CRITICAL][CRITICAL][CRITICAL]
━━━━━━━━━━━━━━━━━━━━━━
ALL 10-MARK SOCIAL SCIENCE ANSWERS MUST INCLUDE ALL 4 SECTIONS:
1. Background/Context: (MANDATORY - 2-3 lines)
2. Key Points: (MANDATORY - 4-5 lines with 3-4 points)
3. Explanation: (MANDATORY - 4-6 lines)
4. Conclusion: (MANDATORY - 2-3 lines)
TOTAL: 12-15+ lines MINIMUM
❌ ANSWERS WITH ONLY EXPLANATION + CONCLUSION ARE INVALID
❌ ANSWERS MISSING BACKGROUND/CONTEXT ARE INVALID
❌ ANSWERS MISSING KEY POINTS ARE INVALID
✅ USE CLEAR SECTION HEADINGS: 'Background/Context:', 'Key Points:', 'Explanation:', 'Conclusion:'
━━━━━━━━━━━━━━━━━━━━━━
"""
    elif subject_lower in ["science", "physics", "chemistry", "biology"]:
        subject_warning = """
━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL][CRITICAL][CRITICAL] CRITICAL REMINDER FOR 10-MARK SCIENCE ANSWERS [CRITICAL][CRITICAL][CRITICAL]
━━━━━━━━━━━━━━━━━━━━━━
ALL 10-MARK SCIENCE ANSWERS MUST INCLUDE ALL 4 SECTIONS:
1. Definition: (MANDATORY - 2-3 lines)
2. Explanation: (MANDATORY - 4-6 lines)
3. Example: (MANDATORY - 2-3 lines)
4. Conclusion: (MANDATORY - 2-3 lines)
TOTAL: 12-15+ lines MINIMUM
❌ ANSWERS WITH ONLY EXPLANATION + CONCLUSION ARE INVALID
❌ ANSWERS MISSING DEFINITION ARE INVALID
❌ ANSWERS MISSING EXAMPLE ARE INVALID
✅ USE CLEAR SECTION HEADINGS: 'Definition:', 'Explanation:', 'Example:', 'Conclusion:'
━━━━━━━━━━━━━━━━━━━━━━
"""
    elif subject_lower in ["english", "literature"]:
        subject_warning = """
━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL][CRITICAL][CRITICAL] CRITICAL REMINDER FOR 10-MARK ENGLISH ANSWERS [CRITICAL][CRITICAL][CRITICAL]
━━━━━━━━━━━━━━━━━━━━━━
ALL 10-MARK ENGLISH ANSWERS MUST INCLUDE ALL 4 SECTIONS:
1. Introduction: (MANDATORY - 2-3 lines)
2. Explanation: (MANDATORY - 4-6 lines)
3. Analysis: (MANDATORY - 4-6 lines)
4. Conclusion: (MANDATORY - 2-3 lines)
TOTAL: 12-15+ lines MINIMUM
❌ ANSWERS WITH ONLY EXPLANATION + CONCLUSION ARE INVALID
❌ ANSWERS MISSING INTRODUCTION ARE INVALID
❌ ANSWERS MISSING ANALYSIS ARE INVALID
✅ USE CLEAR SECTION HEADINGS: 'Introduction:', 'Explanation:', 'Analysis:', 'Conclusion:'
━━━━━━━━━━━━━━━━━━━━━━
"""
    elif subject_lower in ["mathematics", "math", "maths"]:
        subject_warning = """
━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL][CRITICAL][CRITICAL] CRITICAL REMINDER FOR 10-MARK MATHEMATICS ANSWERS [CRITICAL][CRITICAL][CRITICAL]
━━━━━━━━━━━━━━━━━━━━━━
ALL 10-MARK MATHEMATICS ANSWERS MUST INCLUDE ALL SECTIONS:
1. Given: (MANDATORY - 2-3 lines)
2. Formula/Theorem: (MANDATORY - 1-2 lines)
3. Step-by-step Working: (MANDATORY - 6-8 lines)
4. Final Answer: (MANDATORY - 1-2 lines with boxed answer)
TOTAL: 12-15+ lines MINIMUM
❌ ANSWERS MISSING GIVEN ARE INVALID
❌ ANSWERS MISSING FORMULA/THEOREM ARE INVALID
❌ ANSWERS MISSING STEP-BY-STEP WORKING ARE INVALID
❌ ANSWERS MISSING FINAL ANSWER ARE INVALID
✅ USE CLEAR SECTION HEADINGS: 'Given:', 'Formula:', 'Steps:', 'Final Answer:'
━━━━━━━━━━━━━━━━━━━━━━
"""
    
    user_prompt = f"""Generate exam questions from the following study material:

[STUDY_MATERIAL]

{text_content[:content_limit]}

Maximum Questions Allowed Per Upload: {remaining_questions}
Remaining Questions Allowed: {remaining_questions}

Question Distribution (Strict):
{distribution_string}

{subject_instruction}

━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL] CRITICAL: QUESTION COMPLEXITY REQUIREMENT [CRITICAL]
━━━━━━━━━━━━━━━━━━━━━━

❌ STRICTLY FORBIDDEN - DO NOT GENERATE SIMPLE QUESTIONS:
- ❌ NEVER generate simple arithmetic like "What is 3 + 4?" or "What is 5 × 2?"
- ❌ NEVER generate trivial questions that can be answered without formulas or equations
- ❌ NEVER generate questions that test only basic recall without problem-solving

✅ MANDATORY - QUESTIONS MUST BE COMPLEX AND FORMULA-BASED:
- ✅ Questions MUST involve formulas, equations, derivations, or multi-step problem-solving
- ✅ For Mathematics: Questions must require formulas (quadratic formula, area formulas, distance formula, etc.), equations, or multi-step calculations
- ✅ For Science: Questions must involve scientific concepts, principles, formulas, or require reasoning
- ✅ For other subjects: Questions must require understanding, analysis, or application of concepts
- ✅ Questions should test understanding and application, not just simple recall

EXAMPLES OF GOOD QUESTIONS (GENERATE THESE):
- "Using the quadratic formula, solve the equation x² + 5x + 6 = 0 and find the nature of its roots"
- "Derive the formula for the area of a circle given its radius r, showing all steps"
- "If f(x) = 2x² - 3x + 1, calculate f(2) using substitution and show your working"
- "Calculate the discriminant D = b² - 4ac for the equation 3x² - 7x + 2 = 0 and determine the nature of roots"
- "Given the coordinates A(2, 3) and B(5, 7), find the distance between them using the distance formula"
- "Using the formula for the sum of first n natural numbers, calculate the sum of 1 to 10"

EXAMPLES OF BAD QUESTIONS (DO NOT GENERATE):
- "What is 3 + 4?" ❌
- "What is 5 × 2?" ❌
- "What is the value of 10 - 3?" ❌
- "What is 2 + 2?" ❌

━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULE: SUBJECT-BASED ANSWER FORMAT
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] DETECTED SUBJECT: {detected_subject.upper()}
{subject_warning}

IMPORTANT: Answer structure MUST depend on the SUBJECT, not only on marks.

- Marks control LENGTH (1 mark = 1-2 lines, 2 marks = 2-3 lines, 5 marks = 7-9 lines, 10 marks = 9-10 lines)
- Subject controls FORMAT (headings and structure)

If subject is NOT Mathematics:
❌ DO NOT use math-style headings (Given, Formula, Calculation)
✅ Use subject-appropriate headings as specified above

If subject IS Mathematics:
✅ Use math-style headings (Given, Formula, Calculation/Steps, Final Answer)
❌ DO NOT use literature-style headings (Introduction, Explanation, Analysis, Conclusion)

━━━━━━━━━━━━━━━━━━━━━━
FORMAT VARIATION RULE (ABSOLUTELY MANDATORY - ZERO TOLERANCE)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL][CRITICAL][CRITICAL] CRITICAL: STRICTLY FORBIDDEN - NO REPETITION OF QUESTION FORMATS OR FRAMES [CRITICAL][CRITICAL][CRITICAL]

ABSOLUTE PROHIBITION RULES (VIOLATION = INVALID OUTPUT):
1. ❌ NEVER repeat the same sentence structure in ANY two questions
2. ❌ NEVER use the same question opener for ANY two questions
3. ❌ NEVER use the same question frame/template for ANY two questions
4. ❌ NEVER start multiple questions with identical or similar phrases
5. ❌ NEVER use the same structural pattern (direct question, statement-based, etc.) consecutively
6. ✅ EVERY question MUST be TOTALLY DIFFERENT in format, structure, and framing from ALL other questions

MANDATORY VARIATION REQUIREMENTS:

A. Question Opening MUST BE UNIQUE (NO DUPLICATES ALLOWED):
   You MUST use a DIFFERENT opener for EACH question. Rotate through these systematically:
   - Question 1: "What is...?" / "Define..." / "Explain..." / "Describe..." / "State..." / "Write..."
   - Question 2: "Find..." / "Calculate..." / "Solve..." / "Determine..." / "Evaluate..."
   - Question 3: "Compare..." / "Differentiate..." / "Distinguish..." / "Contrast..."
   - Question 4: "List..." / "Enumerate..." / "Mention..." / "Name..."
   - Question 5: "Why...?" / "How...?" / "When...?" / "Where...?"
   - Question 6: "Prove..." / "Show that..." / "Derive..." / "Establish..."
   - Question 7: "Analyze..." / "Discuss..." / "Elaborate..." / "Illustrate..."
   - Question 8+: Continue rotating, NEVER reuse an opener that was already used

B. Question Structure MUST BE UNIQUE (NO DUPLICATES ALLOWED):
   Each question MUST use a DIFFERENT structural frame. Rotate through these:
   - Frame 1: Direct question - "What is X?"
   - Frame 2: Statement + question - "X is Y. What is Z?"
   - Frame 3: Scenario-based - "Given X, find Y" / "If X, then what is Y?"
   - Frame 4: Comparison - "Compare X and Y" / "Differentiate between X and Y"
   - Frame 5: Application - "Apply X to solve Y" / "Using X, calculate Y"
   - Frame 6: Analysis - "Analyze the relationship between X and Y"
   - Frame 7: Problem-solving - "If X happens, what will be Y?"
   - Frame 8: Completion - "Complete the following: X = ?"
   - Frame 9: Identification - "Identify the value of X when Y = Z"
   - Frame 10+: Continue with unique frames, NEVER reuse a frame

C. Answer Presentation MUST BE UNIQUE (VARY EVEN FOR SAME MARKS):
   Even questions with the same marks MUST have different answer presentation:
   - Answer 1: Start with definition, then explanation
   - Answer 2: Start with formula, then calculation
   - Answer 3: Start with given data, then solution
   - Answer 4: Use numbered steps (Step 1, Step 2, ...)
   - Answer 5: Use paragraph format
   - Answer 6: Use bullet points or list format
   - Answer 7: Use comparison format (X vs Y)
   - Answer 8+: Continue varying, NEVER repeat presentation style

STRICT ENFORCEMENT CHECKLIST (VERIFY BEFORE OUTPUT):
Before finalizing your output, verify:
✓ Question 1 opener is DIFFERENT from Question 2 opener
✓ Question 2 opener is DIFFERENT from Question 3 opener
✓ Question 3 opener is DIFFERENT from Question 4 opener
✓ (Continue for ALL questions - NO two questions share the same opener)
✓ Question 1 structure is DIFFERENT from Question 2 structure
✓ Question 2 structure is DIFFERENT from Question 3 structure
✓ (Continue for ALL questions - NO two questions share the same structure)
✓ Each question frame/template is UNIQUE and has NOT been used before
✓ Answer presentation style varies even for questions with same marks

EXAMPLES OF ABSOLUTELY FORBIDDEN PATTERNS:
❌ FORBIDDEN (Repetitive - REJECT THIS):
   Q1. What is X?
   Q2. What is Y?
   Q3. What is Z?
   (Same opener "What is" used 3 times - ABSOLUTELY FORBIDDEN)

❌ FORBIDDEN (Repetitive Structure - REJECT THIS):
   Q1. Define X.
   Q2. Define Y.
   Q3. Define Z.
   (Same structure "Define" used 3 times - ABSOLUTELY FORBIDDEN)

❌ FORBIDDEN (Repetitive Frame - REJECT THIS):
   Q1. Given A, find B.
   Q2. Given C, find D.
   Q3. Given E, find F.
   (Same frame "Given X, find Y" used 3 times - ABSOLUTELY FORBIDDEN)

✅ REQUIRED (Totally Different - ACCEPT THIS):
   Q1. Define X and explain its importance in the context of Y.
   Q2. Given that A = B, calculate the value of C using the formula D.
   Q3. Compare and contrast the characteristics of E and F, highlighting their key differences.
   Q4. Analyze the relationship between G and H, and explain how they interact.
   Q5. If I is true, what will be the consequence for J? Show your reasoning.
   (Each question uses a UNIQUE opener, structure, and frame - REQUIRED)

FINAL WARNING:
If you generate ANY two questions with the same format, opener, structure, or frame, the ENTIRE output is INVALID and must be regenerated. Every single question must be TOTALLY DIFFERENT from all others in format, structure, and framing.

{marks_structure}

=== DIFFICULTY MODE (STRICT - MUST FOLLOW) ===
Difficulty Level: {difficulty}
- Easy: Basic understanding, direct answers
- Medium: Application of concepts, step-wise solutions
- Hard: Deep understanding, full derivations

[CRITICAL][CRITICAL][CRITICAL] CRITICAL: HARD MODE RESTRICTIONS [CRITICAL][CRITICAL][CRITICAL]
If difficulty is "hard", you MUST follow these ABSOLUTE PROHIBITIONS:

❌ ABSOLUTELY FORBIDDEN in HARD mode:
1. Simple arithmetic questions like:
   - "What is the value of 7 - 2?"
   - "What is the value of 10 ÷ 2?"
   - "What is 3 + 5?"
   - "Calculate 8 × 4"
   - Any question that only requires basic addition, subtraction, multiplication, or division

2. Symbol identification questions like:
   - "Which symbol represents multiplication?"
   - "What does the + symbol mean?"
   - "Which symbol represents equality?"

3. Basic definition questions without application:
   - "What is X?" (if X is a simple term that can be answered in one sentence)
   - "Define Y" (if Y is a basic concept)

✅ REQUIRED in HARD mode:
1. Questions MUST involve:
   - Formulas or equations with multiple steps
   - Derivations or proofs
   - Complex problem-solving requiring multiple concepts
   - Application of theorems or principles
   - Multi-step calculations with reasoning
   - Analysis or synthesis of concepts

2. Examples of GOOD hard questions:
   - "Using the quadratic formula, solve x² + 5x + 6 = 0 and determine the nature of roots"
   - "Derive the formula for the area of a circle using integration"
   - "Prove that the sum of angles in a triangle is 180 degrees"
   - "Analyze the function f(x) = 3x³ - 6x² + 2 and find all critical points"
   - "Given the system of equations, solve using matrix method and verify your answer"

3. Questions must require:
   - Multiple steps of reasoning
   - Application of formulas or theorems
   - Logical derivation or proof
   - Complex problem-solving skills

If you generate ANY simple arithmetic or basic symbol identification question in HARD mode, your output is INVALID and will be rejected.

{f"=== MATHEMATICS FORMATTING RULES (CRITICAL - MANDATORY - ONLY FOR MATHEMATICS) ===" if detected_subject == "mathematics" else "=== FORMATTING RULES (SUBJECT-SPECIFIC) ==="}
{f"""
CRITICAL: USE EXAM-FRIENDLY STUDENT-WRITTEN NOTATION. NO LaTeX COMMANDS.

STRICT RULES FOR 10-MARK ANSWERS:
1. Use ONLY exam-friendly mathematical notation (NO LaTeX commands like \\frac, \\sqrt, \\times, \\boxed)
2. Use simple symbols written normally: +, −, ×, ÷, √
3. Write exactly as a student would write in an exam for 10 marks
4. Structure the answer clearly under these headings:
   - Given
   - Formula
   - Calculation / Steps
   - Nature of roots (if applicable)
   - Final Answer
5. Show every intermediate step clearly
6. Do NOT skip substitution steps
7. The final answer must be fully numerical and clearly stated
""" if detected_subject == "mathematics" else f"""
For {detected_subject.upper()} subjects:
- Follow the subject-specific answer structure as specified above
- Use appropriate terminology and formatting for the subject
- Write in exam-appropriate style for {detected_subject}
"""}

{f"""
EXAM-FRIENDLY NOTATION EXAMPLES (MATHEMATICS ONLY):
   ❌ LaTeX: \\( \\frac{{a}}{{b}} \\) → ✅ Exam: a/b or (a)/(b)
   ❌ LaTeX: \\( \\sqrt{{x}} \\) → ✅ Exam: √x or sqrt(x)
   ❌ LaTeX: \\( x^2 \\) → ✅ Exam: x² or x^2
   ❌ LaTeX: \\( \\times \\) → ✅ Exam: ×
   ❌ LaTeX: \\( \\boxed{{x = 5}} \\) → ✅ Exam: [x = 5] or Final Answer: x = 5
   ❌ LaTeX: \\( D = b^2 - 4ac \\) → ✅ Exam: D = b² - 4ac or D = b^2 - 4ac

FOR 1-5 MARK QUESTIONS (MATHEMATICS):
- Can use simple notation: x = 5, f(x) = 2x² + 3x + 1
- Fractions: a/b or (a)/(b)
- Powers: x² or x^2
- Roots: √x or sqrt(x)

FOR 10-MARK QUESTIONS (MATHEMATICS - STRICT EXAM FORMAT):
- MUST use student-written notation (NO LaTeX)
- MUST have clear headings: Given, Formula, Calculation/Steps, Nature of roots, Final Answer
- MUST show every step with substitution
- Example format:
  Given: f(x) = 3x³ - 6x² + 2
  
  Formula: 
  First derivative: f'(x) = 9x² - 12x
  Second derivative: f''(x) = 18x - 12
  
  Calculation / Steps:
  Step 1: f'(x) = 9x² - 12x
  Step 2: Set f'(x) = 0
          9x² - 12x = 0
          x(9x - 12) = 0
          x = 0 or x = 12/9 = 4/3
  Step 3: f''(x) = 18x - 12
  Step 4: f''(0) = 18(0) - 12 = -12 < 0 (local maximum)
          f''(4/3) = 18(4/3) - 12 = 24 - 12 = 12 > 0 (local minimum)
  
  Function Values:
  f(0) = 3(0)³ - 6(0)² + 2 = 2
  f(4/3) = 3(4/3)³ - 6(4/3)² + 2 = -14/9
  
  Final Answer:
  Local maximum at (0, 2)
  Local minimum at (4/3, -14/9)

2. Answer structure for math questions:
   - Easy: Direct answer with formula (1-2 lines)
   - Medium: Show steps with formulas (3-6 lines)
   - Hard: Complete derivation with step numbering and clear final answer (8-15 lines)

3. For hard math questions (10 marks):
   - MUST include step numbering: Step 1, Step 2, Step 3, ...
   - MUST show logical reasoning
   - MUST have clear final answer (NO \\boxed, use "Final Answer:" heading)
""" if detected_subject == "mathematics" else ""}

=== QUESTION FORMAT VARIATION (ABSOLUTELY MANDATORY - ZERO TOLERANCE) ===
[CRITICAL][CRITICAL][CRITICAL] STRICTLY FORBIDDEN: NO REPETITION OF QUESTION FORMATS, OPENERS, STRUCTURES, OR FRAMES [CRITICAL][CRITICAL][CRITICAL]

ABSOLUTE PROHIBITION RULES:
- ❌ NEVER use the same opener for ANY two questions (even non-consecutive)
- ❌ NEVER use the same structure for ANY two questions (even non-consecutive)
- ❌ NEVER use the same frame/template for ANY two questions
- ✅ EVERY question MUST be TOTALLY DIFFERENT from ALL others in format, structure, and framing

USE THESE OPENERS (EACH QUESTION MUST USE A DIFFERENT ONE - NO DUPLICATES):
- Q1: Define..., Explain..., Describe..., State..., Write short note on...
- Q2: Find..., Calculate..., Solve..., Determine..., Evaluate...
- Q3: Prove that..., Show that..., Derive..., Establish...
- Q4: Compare..., Distinguish between..., Contrast...
- Q5: Why..., How..., When..., Where...
- Q6: Scenario/If: "Given/If ..., find/compute/derive ..."
- Q7: Analyze..., Discuss..., Elaborate..., Illustrate...
- Q8+: Continue with NEW openers, NEVER reuse any opener

USE THESE STRUCTURES (EACH QUESTION MUST USE A DIFFERENT ONE - NO DUPLICATES):
- Structure 1: Direct ask - "What is X?"
- Structure 2: Statement + ask - "X is Y. What is Z?"
- Structure 3: Scenario - "Given X, find Y"
- Structure 4: Application - "Using formula X, compute Y"
- Structure 5: Proof/Derivation - "Prove/Derive that ..."
- Structure 6: Comparison - "Compare X and Y"
- Structure 7: Completion - "Complete/derive the expression for ..."
- Structure 8: Identification - "Identify the value of X when Y = Z"
- Structure 9+: Continue with NEW structures, NEVER reuse any structure

{f"MATH-SPECIFIC VARIATION (EACH MUST BE UNIQUE - ONLY FOR MATHEMATICS):" if detected_subject == "mathematics" else "SUBJECT-SPECIFIC VARIATION (EACH MUST BE UNIQUE):"}
{f"""
- Variation 1: Direct calculation
- Variation 2: Word problem
- Variation 3: Proof/derivation
- Variation 4: Application
- Variation 5: Comparison
- Variation 6: Analysis (e.g., nature of roots)
- Variation 7+: Continue with NEW variations, NEVER reuse
""" if detected_subject == "mathematics" else f"""
- Variation 1: Definition-based questions
- Variation 2: Explanation-based questions
- Variation 3: Analysis-based questions
- Variation 4: Comparison-based questions
- Variation 5: Application-based questions
- Variation 6: Context-based questions
- Variation 7+: Continue with NEW variations, NEVER reuse
"""}

ANSWER PRESENTATION (VARY - NO DUPLICATES):
- Answer 1: Start with definition, then explanation
- Answer 2: Start with formula, then calculation
- Answer 3: Start with given data, then solution
- Answer 4: Use numbered steps (Step 1, Step 2, ...)
- Answer 5: Use paragraph format
- Answer 6: Use bullet points or list format
- Answer 7+: Continue varying, NEVER repeat presentation style

CRITICAL ENFORCEMENT:
- For ANY number of questions, ensure NO two questions share the same opener
- For ANY number of questions, ensure NO two questions share the same structure
- For ANY number of questions, ensure NO two questions share the same frame
- Each question must be TOTALLY DIFFERENT from all others
- Real exam papers have natural variation—replicate that with STRICT enforcement

=== GENERAL RULES ===
1. TOTAL questions generated must NOT exceed {remaining_questions}.
2. Follow the mark distribution EXACTLY as requested.
3. Use correct question types:
   - MCQ → 4 options + correct_answer field (ONLY for 1-2 marks)
   - Short Answer (1–2 marks) → type: "short"
   - Descriptive (1–10 marks) → type: "descriptive" (1 mark = 1-2 lines, 3+ marks = detailed)
4. ANSWER LENGTH RULES (STRICT - MUST FOLLOW EXACTLY - SUBJECT-SPECIFIC):
   
   🧮 MATHEMATICS (Follow board-exam writing standards):
   - 1 mark → 1–2 lines (one-line factual answer, direct formula/equation result, NO steps)
   - 2 marks → 2–3 lines (formula + answer, brief working)
   - 3 marks → 4–5 lines (formula + substitution + answer, brief explanation with steps)
   - 5 marks → 6–8 lines (Given → Formula → Steps → Final Answer, structured medium answer)
   - 10 marks → 12–15+ lines (Full working + explanation, detailed step-by-step)
   - ⚠️ Lines don't matter as much as steps - focus on complete solution for 10 marks
   
   🔬 SCIENCE (Follow board-exam writing standards):
   - 1 mark → 1–2 lines (one-line factual answer, direct definition or fact)
   - 2 marks → 2–3 lines (definition + 1 point, brief explanation)
   - 3 marks → 4–5 lines (explanation + example, brief explanation with one example)
   - 5 marks → 6–8 lines (definition + diagram + explanation, structured medium answer)
   - 10 marks → 12–15+ lines (Introduction → Explanation → Example → Conclusion, comprehensive)
   
   🏛 SOCIAL SCIENCE (Follow board-exam writing standards):
   - 1 mark → 1–2 lines (direct fact, one-line factual answer)
   - 2 marks → 2–3 lines (direct fact with brief context)
   - 3 marks → 4–5 lines (reason/explanation, brief explanation)
   - 5 marks → 6–8 lines (3–4 bullet points, structured answer with key points)
   - 10 marks → 12–15+ lines (intro + causes + effects + conclusion, comprehensive)
   
   📖 ENGLISH (Follow board-exam writing standards):
   - 1 mark → 1–2 lines (one-line factual answer, direct answer only)
   - 2 marks → 2–3 lines (brief explanation, concise but complete)
   - 3 marks → 4–5 lines (explanation + example, short paragraph)
   - 5 marks → 6–8 lines (paragraph style, well-structured explanation)
   - 10 marks → 12–15+ lines (Introduction + Analysis + Conclusion, detailed essay-style)
   
   🈳 GENERAL KNOWLEDGE:
   - Mostly 1–3 marks
   - Direct factual answers
   - NO long explanations
   - Keep answers concise and factual
   
   CRITICAL: Count lines carefully. Answers MUST match the specified line count for each mark value AND subject.
   CRITICAL: Follow subject-specific structure rules as specified in the STRICT ANSWER RULES section above.
5. If remaining_questions is less than the requested total, DO NOT generate extra questions. Fill only up to the allowed limit.
6. All questions must come ONLY from the study material.
7. CRITICAL: NO duplicated questions - each question must be completely unique and distinct.
   - This applies to ALL languages (English, Tamil, Hindi, Telugu, Kannada, Malayalam, Arabic, Spanish)
   - Even if questions are in different languages, they must cover different topics/concepts
   - Avoid rephrasing the same question - each question must test different knowledge points
   - Ensure variety in question topics, concepts, and difficulty levels
8. MCQs must be distinct and meaningful - avoid similar or overlapping options or questions that test the same concept.

━━━━━━━━━━━━━━━━━━━━━━
📝 QUESTION FRAMING QUALITY (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] CRITICAL: All questions MUST be well-framed, clear, and unambiguous

QUESTION CLARITY RULES:
✅ Questions MUST be complete, grammatically correct sentences
✅ Questions MUST be unambiguous - only ONE correct interpretation possible
✅ Questions MUST use formal exam-style language (NO casual or conversational tone)
✅ Questions MUST clearly indicate what knowledge is being tested
✅ MCQ question stems MUST be complete statements or questions
✅ All MCQ options MUST be grammatically consistent with the question stem
✅ All MCQ options MUST be parallel in structure and similar in length
✅ MCQ distractors (wrong options) MUST be plausible but clearly incorrect
❌ NEVER use incomplete sentences (unless formula-based)
❌ NEVER use ambiguous phrasing with multiple possible interpretations
❌ NEVER use vague pronouns or unclear references
❌ NEVER use "All of the above" or "None of the above" as options
❌ NEVER make correct answer stand out due to length or format

MCQ OPTIONS QUALITY:
✅ All 4 options (A, B, C, D) must be distinct and meaningful
✅ Wrong options should test common misconceptions or related concepts
✅ Options should be approximately the same length
✅ Options should be parallel in grammatical structure
✅ Correct answer should not be obviously different from others
❌ NEVER use obviously wrong options that are too easy to eliminate
❌ NEVER use options that are identical or nearly identical
❌ NEVER use options completely unrelated to the question topic

QUESTION FRAMING EXAMPLES:

✅ GOOD MCQ Question:
Question: "முதல் உலகப்போரின் போது பிரிட்டனைத் தாக்கிய நாடு எது?"
Options: ["ஜெர்மனி", "இத்தாலி", "ரஷ்யா", "பிரான்ஸ்"]
Correct: "ஜெர்மனி"
(Complete question, clear context, all options are related countries, grammatically consistent)

❌ BAD MCQ Question:
Question: "First World War?"
Options: ["Germany", "Italy", "Russia", "France"]
(Question is incomplete, unclear what is being asked)

✅ GOOD Descriptive Question:
"முதல் உலகப்போரின் காரணங்கள் மற்றும் விளைவுகளை விவரிக்கவும்."
(Complete sentence, clear instruction, formal language)

❌ BAD Descriptive Question:
"First World War causes and effects"
(Not a complete sentence, too casual)
9. Output must ALWAYS follow this exact JSON format (STRUCTURED - NO \\n, NO paragraphs):

{f"""
{{
  "questions": [
    {{
      "marks": 5,
      "type": "descriptive",
      "difficulty": "medium",
      "question": "Given the function f(x) = 2x² + 3x + 1, find the roots using the quadratic formula.",
      "correct_answer": {{
        "given": "f(x) = 2x² + 3x + 1",
        "formula": "x = (-b ± √(b² - 4ac)) / (2a), where D = b² - 4ac",
        "coefficients": "a = 2, b = 3, c = 1",
        "steps": [
          "D = b² - 4ac = 3² - 4(2)(1) = 9 - 8 = 1",
          "x = (-3 ± √1) / 4 = (-3 ± 1) / 4",
          "x = (-3 + 1) / 4 = -1/2 and x = (-3 - 1) / 4 = -1"
        ],
        "final": "Final Answer: x = -1/2, -1"
      }}
    }},
    {{
      "marks": 10,
      "type": "descriptive",
      "difficulty": "hard",
      "question": "Analyze the function f(x) = 3x³ - 6x² + 2. Find the critical points and determine their nature.",
      "correct_answer": {{
        "given": "f(x) = 3x³ - 6x² + 2",
        "definition": "Critical points occur where the first derivative is zero or undefined.",
        "formula": "First derivative: f'(x) = 9x² - 12x\\nSecond derivative: f''(x) = 18x - 12",
        "steps": [
          "Step 1: Calculate first derivative: f'(x) = 9x² - 12x",
          "Step 2: Set first derivative to zero: f'(x) = 9x² - 12x = 0",
          "Step 3: Factor the equation: x(9x - 12) = 0",
          "Step 4: Find critical points: x = 0 or x = 12/9 = 4/3",
          "Step 5: Calculate second derivative: f''(x) = 18x - 12",
          "Step 6: Apply second derivative test: f''(0) = -12 < 0 (local maximum), f''(4/3) = 12 > 0 (local minimum)"
        ],
        "function_values": [
          "f(0) = 3(0)³ - 6(0)² + 2 = 2",
          "f(4/3) = 3(4/3)³ - 6(4/3)² + 2 = -14/9"
        ],
        "final": "Final Answer: Local maximum at (0, 2), Local minimum at (4/3, -14/9)"
      }}
    }},
""" if detected_subject == "mathematics" else f"""
{{
  "questions": [
    {{
      "marks": 3,
      "type": "descriptive",
      "difficulty": "medium",
      "question": "Describe the main character's development in the story.",
      "correct_answer": "The main character undergoes significant growth throughout the narrative. Initially, they are portrayed as naive and inexperienced. As the story progresses, they face various challenges that test their resolve. These experiences shape their personality and worldview. By the end, they emerge as a more mature and understanding individual."
    }},
    {{
      "marks": 5,
      "type": "descriptive",
      "difficulty": "medium",
      "question": "Explain the theme of the poem and analyze its literary devices.",
      "correct_answer": {{
        "introduction": "The poem explores themes of nature and human connection, using vivid imagery to create emotional resonance.",
        "explanation": "The poet uses vivid imagery to depict natural scenes, creating a sense of harmony between humans and the environment. The language choices emphasize the interconnectedness of all living things.",
        "analysis": "Literary devices such as metaphor and personification enhance the emotional impact. The metaphor of nature as a teacher allows readers to connect deeply with the poet's message about learning from the natural world.",
        "conclusion": "The poem effectively conveys the relationship between humans and nature through its masterful use of language and imagery, leaving readers with a profound appreciation for the natural world."
      }}
    }},
    {{
      "marks": 10,
      "type": "descriptive",
      "difficulty": "hard",
      "question": "Comprehensively analyze the historical significance of the event and its impact.",
      "correct_answer": {{
        "background": "The event occurred during a period of significant change in society, marking a transition from traditional to modern approaches.",
        "key_points": ["First, the event marked a turning point in political structures", "Second, it influenced subsequent economic developments", "Third, it changed social relationships and cultural norms"],
        "explanation": "The event's significance lies in its transformative nature. It challenged existing power structures and created new opportunities for different social groups. The immediate consequences were felt across multiple sectors of society.",
        "conclusion": "The event had lasting impact on society, shaping the course of history for generations to come. Its legacy continues to influence contemporary discussions and policies."
      }}
    }},
""" if detected_subject in ["english", "science", "social_science"] else f"""
{{
  "questions": [
    {{
      "marks": 5,
      "type": "descriptive",
      "difficulty": "medium",
      "question": "Explain the concept and provide examples.",
      "correct_answer": "Definition: The concept is defined as... Explanation: It involves several key aspects... Example: For instance... Conclusion: In summary..."
    }},
"""}
    {{
      "marks": 1,
      "type": "mcq",
      "difficulty": "easy",
      "question": "What is the value of 2 + 3?",
      "options": ["4", "5", "6", "7"],
      "correct_answer": "5"
    }},
    {{
      "marks": 2,
      "type": "short",
      "difficulty": "easy",
      "question": "Solve for \\( x \\): \\( 2x + 5 = 15 \\)",
      "correct_answer": "\\( x = 5 \\)"
    }},
    {{
      "marks": 1,
      "type": "mcq",
      "difficulty": "easy",
      "question": "Which symbol represents equality?",
      "options": ["\\( = \\)", "\\( \\neq \\)", "\\( < \\)", "\\( > \\)"],
      "correct_answer": "\\( = \\)"
    }},
    {{
      "marks": 2,
      "type": "short",
      "difficulty": "easy",
      "question": "What is the value of 2 + 3?",
      "correct_answer": "The value of 2 + 3 is 5."
    }}
  ]
}}

IMPORTANT NOTES:
- For mathematics questions, ALWAYS use exam-friendly notation (NO LaTeX commands)
- For hard questions (8+ marks), include "steps" array and "Final Answer:" prefix
- For medium questions (3-6 marks), include "steps" array
- For easy questions (1-2 marks), direct answer is sufficient
- All mathematical symbols MUST be in exam-friendly format (simple notation: +, −, ×, ÷, √, x², a/b, etc.)

Language: {target_language_name}
Include answers: true
Difficulty level: {difficulty}

LANGUAGE-SPECIFIC EXAM STYLE (MANDATORY):
[CRITICAL] TARGET LANGUAGE: {target_language_name.upper()} [CRITICAL]
You MUST generate ALL content (questions, answers, options) EXCLUSIVELY in {target_language_name}. NO EXCEPTIONS.

You MUST use formal exam-style phrasing appropriate for {target_language_name}:
- Tamil: Use formal கல்வி மொழி Tamil. Use patterns like: "... என்றால் என்ன?", "சுருக்கமாக எழுதுக", "விளக்குக", "விவரிக்கவும்", "வேறுபாடுகளை எழுதுக". Avoid spoken Tamil. Generate questions and answers in Tamil script ONLY.
- English: Use formal academic tone. Use patterns like: "Define …", "Explain …", "Describe …", "Write short notes on …", "Differentiate between …"
- Hindi: Use शुद्ध हिन्दी / परीक्षा शैली. Use: "परिभाषित कीजिए", "समझाइए", "विवरण दीजिए", "लघु उत्तरीय प्रश्न", "दीर्घ उत्तरीय प्रश्न". Generate in Devanagari script ONLY.
- Telugu: Use formal textbook Telugu. Use: "అంటే ఏమిటి?", "సంక్షిప్తంగా వ్రాయండి", "వివరించండి". Generate in Telugu script ONLY.
- Kannada: Use school exam style Kannada. Use: "ಎಂದರೆ ಏನು?", "ಸಂಕ್ಷಿಪ್ತ ಉಕ್ಕಿ ಬರೆಯಿರಿ", "ವಿವರಿಸಿ". Generate in Kannada script ONLY.
- Malayalam: Use formal academic Malayalam. Use: "എന്താണ്?", "വ്യാഖ്യാനിക്കുക", "സംക്ഷിപ്തമായി എഴുതുക". Generate in Malayalam script ONLY.
- Arabic: Use Modern Standard Arabic. Use: "ما هو …؟", "اشرح", "وضح". Generate in Arabic script ONLY.
- Spanish: Use neutral academic Spanish. Use: "Defina …", "Explique …", "Describa …"

CRITICAL LANGUAGE ENFORCEMENT:
- If target language is {target_language_name}, EVERY SINGLE WORD must be in {target_language_name}
- Question text: {target_language_name} ONLY - NO English, NO code-switching
- Answer text: {target_language_name} ONLY - NO English, NO code-switching  
- MCQ options: {target_language_name} ONLY - NO English, NO code-switching
- DO NOT use casual or spoken language - ONLY formal exam-style phrasing
- DO NOT mix languages - if you see English content in the study material but target is {target_language_name}, translate and generate in {target_language_name}

[CRITICAL][CRITICAL][CRITICAL] CRITICAL REQUIREMENTS - READ CAREFULLY [CRITICAL][CRITICAL][CRITICAL]

QUALITY OVER QUANTITY (HIGHEST PRIORITY):
- ✅ Generate questions ONLY if the content clearly supports them
- ✅ Do NOT force additional questions to meet a number
- ✅ If the content does not support the requested number of questions, generate the maximum number of HIGH-QUALITY questions possible
- ✅ Do NOT repeat question patterns, equations, or ideas
- ✅ Do NOT invent or stretch content to increase count
- ✅ Quality is MORE IMPORTANT than quantity
- ✅ If you can only generate fewer than {actual_num_questions} high-quality questions, generate only what you can support with the content

QUESTION COUNT (TARGET - NOT MANDATORY):
- 🎯 Target: Generate up to {actual_num_questions} questions if content supports them
- 🎯 The "questions" array in your JSON should contain up to {actual_num_questions} question objects
- 🎯 If content supports fewer questions, generate only the number you can support with HIGH QUALITY
- 🎯 NEVER exceed {remaining_questions} questions
- 🎯 NEVER generate low-quality or repetitive questions just to meet the count
- 🎯 NEVER invent content or stretch material to create more questions

DISTRIBUTION REQUIREMENTS (FLEXIBLE):
- Follow the distribution as closely as possible: {distribution_string}
- If content doesn't support the full distribution, generate the best questions you can from the available content
- Prioritize quality and uniqueness over exact distribution matching

VERIFICATION BEFORE OUTPUT:
1. Count the questions in your "questions" array
2. Verify all questions are HIGH QUALITY and UNIQUE (no repetition)
3. Verify all questions are supported by the content (no invented content)
4. If you have fewer than {actual_num_questions} questions but they are all high-quality, that is ACCEPTABLE
5. Only output when you have verified quality and uniqueness
- Output ONLY valid JSON - no markdown, no explanations, no text before/after JSON
- CRITICAL: EVERY question MUST have a "correct_answer" field - this is MANDATORY for ALL mark values (1, 2, 3, 5, 10 marks)
- For 5+ marks: Use structured format (object with subject-appropriate fields)
  * Mathematics: Use object with given, formula, steps, final
  * English/Literature: Use object with introduction, explanation, analysis, conclusion (OR string with embedded headings like "Introduction: ... Explanation: ... Analysis: ... Conclusion: ...")
  * Science: Use object with definition, explanation, example, conclusion (OR string with embedded headings)
  * Social Science: Use object with background, key_points, explanation, conclusion (OR string with embedded headings)
- For 1-3 marks: Can use simple string format, but MUST provide an answer
[CRITICAL] CRITICAL LANGUAGE REQUIREMENT [CRITICAL]
- All questions, options, and answers MUST be in {target_language_name} ONLY
- DO NOT mix languages - if target language is {target_language_name}, generate EVERYTHING in {target_language_name}
- Question text: {target_language_name} ONLY
- Answer text: {target_language_name} ONLY  
- MCQ options: {target_language_name} ONLY
- If target language is Tamil, use Tamil script (தமிழ்) for ALL content
- If target language is Hindi, use Devanagari script (हिंदी) for ALL content
- If target language is English, use English for ALL content
- NO code-switching or language mixing allowed
- NEVER generate a question without an answer - if you cannot generate an answer, do not generate the question

━━━━━━━━━━━━━━━━━━━━━━
📝 QUESTION FRAMING QUALITY (MANDATORY - READ CAREFULLY)
━━━━━━━━━━━━━━━━━━━━━━

[CRITICAL] CRITICAL: All questions MUST be well-framed, clear, grammatically correct, and unambiguous

1. QUESTION CLARITY REQUIREMENTS:
   ✅ Questions MUST be complete, grammatically correct sentences
   ✅ Questions MUST be unambiguous - only ONE correct interpretation possible
   ✅ Questions MUST use formal exam-style language (NO casual or conversational tone)
   ✅ Questions MUST clearly indicate what knowledge is being tested
   ✅ Questions MUST be phrased naturally and read smoothly
   ❌ NEVER use incomplete sentences (unless formula-based like "If x² = 16, find x")
   ❌ NEVER use ambiguous phrasing with multiple possible interpretations
   ❌ NEVER use vague pronouns or unclear references
   ❌ NEVER use casual or conversational language

2. MCQ QUESTION FRAMING (SPECIFIC RULES):
   ✅ Question stem MUST be a complete, clear question or statement
   ✅ Question stem MUST be grammatically correct
   ✅ Question stem MUST clearly indicate what is being asked
   ✅ All 4 options MUST be grammatically consistent with the question stem
   ✅ All 4 options MUST be plausible and related to the topic
   ✅ Correct answer MUST be clearly the best/most accurate option
   ✅ Wrong options (distractors) MUST be plausible but clearly incorrect
   ✅ Options MUST be similar in length (avoid one very long option)
   ✅ Options MUST be parallel in structure (all start with same type of word if applicable)
   ✅ Options should test understanding, not just recall
   ❌ NEVER use "All of the above" or "None of the above" as options
   ❌ NEVER make the correct answer obviously different in format/length
   ❌ NEVER use options that are too similar to each other
   ❌ NEVER use options that are completely unrelated to the question

3. MCQ OPTIONS QUALITY:
   ✅ Option A, B, C, D must all be distinct and meaningful
   ✅ Distractors (wrong options) should test common misconceptions
   ✅ Distractors should be factually related to the topic
   ✅ All options should be approximately the same length
   ✅ Correct answer should not stand out due to formatting or length
   ✅ Options should be grammatically parallel (e.g., all nouns, all phrases, all sentences)
   ❌ NEVER use obviously wrong options that are too easy to eliminate
   ❌ NEVER use options that are identical or nearly identical
   ❌ NEVER use options completely unrelated to the question topic

4. QUESTION STRUCTURE EXAMPLES:

   ✅ GOOD MCQ Examples:
   - "முதல் உலகப்போரின் போது பிரிட்டனைத் தாக்கிய நாடு எது?" (Which country attacked Britain during the First World War?)
     Options: ["ஜெர்மனி", "இத்தாலி", "ரஷ்யா", "பிரான்ஸ்"]
   - "What is the value of x if 2x + 5 = 13?"
     Options: ["4", "5", "6", "7"]
   - "Which of the following is the capital of France?"
     Options: ["Paris", "London", "Berlin", "Madrid"]
   
   ❌ BAD MCQ Examples:
   - "First World War?" (incomplete, unclear)
   - "Who attacked?" (too vague, missing context)
   - "Britain was attacked by?" (incomplete sentence)
   - "What happened in 1914?" (too vague, multiple possible answers)
   
   ✅ GOOD Descriptive Examples:
   - "முதல் உலகப்போரின் காரணங்களை விளக்குக." (Explain the causes of the First World War.)
   - "Describe the process of photosynthesis in detail."
   - "விவரிக்கவும்: முதல் உலகப்போரின் விளைவுகள்." (Describe: Effects of the First World War.)
   
   ❌ BAD Descriptive Examples:
   - "First World War causes" (not a complete sentence)
   - "Tell about photosynthesis" (too casual)
   - "What happened?" (too vague)
   - "Explain it" (unclear reference)

5. GRAMMATICAL CORRECTNESS:
   ✅ All questions MUST be grammatically correct in the target language
   ✅ All options MUST be grammatically correct
   ✅ Subject-verb agreement MUST be correct
   ✅ Proper punctuation MUST be used
   ✅ Proper capitalization MUST be used (as per language rules)
   ❌ NEVER use incorrect grammar
   ❌ NEVER use incorrect punctuation
   ❌ NEVER use incorrect capitalization

6. LANGUAGE-SPECIFIC FRAMING PATTERNS:
   - Tamil: Use formal patterns like "X ஐ விளக்குக", "X என்றால் என்ன?", "X ஐ விவரிக்கவும்", "X இன் காரணங்கள் என்ன?"
   - English: Use formal patterns like "Explain...", "Describe...", "What is...?", "Define...", "Which of the following...?"
   - Hindi: Use formal patterns like "विवरण दीजिए", "समझाइए", "परिभाषित कीजिए", "निम्नलिखित में से कौन सा...?"
   - All languages: Maintain formal, academic tone throughout
- Match question type to marks:

ANSWER FORMAT RULES (MANDATORY - SUBJECT-SPECIFIC):
- 1-2 marks: "correct_answer" can be a simple string (e.g., "\\\\( x = 5 \\\\)" for math, or "Direct answer text" for other subjects)
- 3 marks: "correct_answer" can be a simple string OR structured object
- 5+ marks: "correct_answer" MUST be a structured object, but structure depends on SUBJECT:

  FOR MATHEMATICS (5+ marks):
  - "given": string (what is given in the problem) - REQUIRED
  - "formula": string (formula/theorem used) - REQUIRED for 5+ marks, NEVER leave empty
  - "coefficients": string (coefficients/values, if applicable) - Optional
  - "steps": array of strings (each step as a separate string, NO \\n) - REQUIRED for 5+ marks
  - "function_values": array of strings (calculate function values at critical points, if applicable) - REQUIRED for 10 marks when finding extrema
  - "final": string (final answer with "Final Answer:" prefix) - REQUIRED for 5+ marks, NO \\boxed, use plain text
  - For 10-mark math: MUST also include "definition" field

  FOR ENGLISH/LITERATURE (5+ marks):
  - "introduction": string - REQUIRED for 5+ marks
  - "explanation": string - REQUIRED for 5+ marks
  - "analysis": string - REQUIRED for 5+ marks
  - "conclusion": string - REQUIRED for 5+ marks
  - OR can be a single string with embedded headings: "Introduction: ... Explanation: ... Analysis: ... Conclusion: ..."

  FOR SCIENCE (5+ marks):
  - "definition": string - REQUIRED for 5+ marks
  - "explanation": string - REQUIRED for 5+ marks
  - "example": string - Optional but recommended
  - "conclusion": string - REQUIRED for 5+ marks
  - OR can be a single string with embedded headings: "Definition: ... Explanation: ... Example: ... Conclusion: ..."

  FOR SOCIAL SCIENCE (5+ marks):
  - "background" or "context": string - REQUIRED for 5+ marks (2-3 lines for 10 marks)
  - "key_points": string or array of strings - REQUIRED for 5+ marks (3-4 key points, 4-5 lines total for 10 marks)
  - "explanation": string - REQUIRED for 5+ marks (4-6 lines for 10 marks)
  - "conclusion": string - REQUIRED for 5+ marks (2-3 lines for 10 marks)
  - For 10 marks: ALL fields MUST be present and substantial, totaling 12-15+ lines
  - OR can be a single string with embedded headings: "Background/Context: ... Key Points: ... Explanation: ... Conclusion: ..."
  - If using string format, ensure it has ALL sections and totals 12-15+ lines

CRITICAL: For non-mathematics subjects, DO NOT use math-style fields (given, formula, steps). Use subject-appropriate fields as specified above.
- For 10-mark questions: MUST include ALL required fields for the subject
- Each field should contain meaningful content - never leave required fields empty
- Final answer/Conclusion MUST be clearly stated
 * MCQ: 1-2 marks only
 * Short Answer: 1-2 marks
 * Descriptive: 1-10 marks (1 mark = 1-2 lines, 3+ marks = detailed)
 * 10-mark questions: MUST be descriptive, NEVER MCQ
- STRICT ANSWER LENGTH COMPLIANCE (MANDATORY - NO EXCEPTIONS):
  * 1 mark answers: 1-2 lines ONLY (very short, factual - maximum 2 lines)
  * 2 mark answers: 2-3 lines ONLY (brief explanation - exactly 2-3 lines)
  * 3 mark answers: 4-5 lines ONLY (short descriptive - exactly 4-5 lines)
  * 5 mark answers: 6-8 lines ONLY (medium descriptive - exactly 6-8 lines)
  * 10 mark answers: 12-15+ lines ONLY (long descriptive / essay-style - minimum 12 lines)
  
  CRITICAL: The marks value in each question MUST match the answer length. 
  If you generate a 1-mark question, the answer MUST be 1-2 lines. 
  If you generate a 3-mark question, the answer MUST be 4-5 lines.
- CRITICAL: NO duplicated questions - ensure each question is completely unique (applies to ALL languages)
- MCQs must be distinct and meaningful - avoid similar options or questions that test the same concept

=== SELF-VERIFICATION (BEFORE OUTPUT) ===
After generating questions, silently verify EACH question:

For 1 MARK:
✓ Answer has maximum 2 lines
✓ NO explanation, NO derivation, NO steps
✓ Direct answer only

For 2 MARKS:
✓ Answer has 2-3 lines maximum
✓ Brief working if needed
✓ 1 formula or factorisation

For 5 MARKS:
✓ Answer has 5-7 lines minimum
✓ Step-wise solution present
✓ Formula + substitution shown
✓ Final answer clearly stated: "Final Answer: ..." (exam-friendly format, NO LaTeX)

For 10 MARKS (STRICT BOARD-EXAM RULES):
✓ Answer has minimum 12-15 lines (NO SHORT ANSWERS - INVALID)
✓ ALL mandatory parts present based on SUBJECT:

  FOR MATHEMATICS (10 marks):
  (i) Given - What is provided in the problem
  (ii) Definition (if applicable) - Define key terms/concepts
  (iii) Formula/Theorem - State the formula or theorem
  (iv) Step-by-step working - Numbered steps with complete calculations
  (v) Logical explanation - Explain reasoning and method
  (vi) Final conclusion statement - Summarize and state final answer
  
  FOR SOCIAL SCIENCE (10 marks) - ALL 4 SECTIONS MANDATORY:
  (i) Background/Context - Historical/geographical context (2-3 lines) - MANDATORY
  (ii) Key Points - 3-4 key points with details (4-5 lines) - MANDATORY
  (iii) Explanation - Comprehensive explanation of relationships and causes (4-6 lines) - MANDATORY
  (iv) Conclusion - Strong conclusion summarizing all points (2-3 lines) - MANDATORY
  ❌ NEVER skip Background or Key Points - answer is INVALID without them
  
  FOR SCIENCE (10 marks):
  (i) Definition - Clear definition of concepts
  (ii) Explanation - Detailed scientific explanation
  (iii) Example - Relevant examples or applications
  (iv) Conclusion - Comprehensive conclusion
  
  FOR ENGLISH (10 marks):
  (i) Introduction - Context and overview
  (ii) Explanation - Detailed explanation
  (iii) Analysis - In-depth analysis
  (iv) Conclusion - Comprehensive conclusion

✓ For Social Science: ALL 4 sections (Background, Key Points, Explanation, Conclusion) MUST be present
✓ Step numbering present (for Mathematics: Step 1, Step 2, Step 3, ...)
✓ Final answer clearly stated: "Final Answer: ..." (for Mathematics) or strong conclusion (for other subjects)
✓ Treated as board-exam answer script with full working
✓ NO abbreviated answers - full working is mandatory
✓ Total length: 12-15+ lines minimum for ALL subjects

General Checks:
✓ Exam-friendly notation used (NO LaTeX commands like \\frac, \\sqrt, \\boxed)
✓ Simple symbols used: +, −, ×, ÷, √ written normally
✓ No conversational language - only formal exam-style tone
✓ Mathematical correctness (if applicable)
✓ Discriminant in exam format: D = b² - 4ac or D = b^2 - 4ac
✓ No word replacements for symbols (use = not "equal to")

FORMAT VARIATION CHECK (CRITICAL):
✓ NO two consecutive questions use the same question format/phrasing
✓ Question openings vary (What/Define/Explain/Find/Calculate/Solve/Compare/etc.)
✓ Question structures vary (direct/scenario-based/comparison/application)
✓ Answer presentation styles vary (even for same marks)
✓ Each question feels unique and different from previous ones

If ANY rule fails (including format variation), regenerate silently to ensure 99% accuracy and natural variation.

[CRITICAL][CRITICAL][CRITICAL] CRITICAL FINAL REMINDER [CRITICAL][CRITICAL][CRITICAL]

EVERY SINGLE QUESTION MUST HAVE A "correct_answer" FIELD - THIS IS MANDATORY FOR ALL MARK VALUES (1, 2, 3, 5, 10).

DO NOT generate any question without an answer. If you cannot provide an answer, do not generate that question.

For 5-mark questions:
- If subject is Mathematics: Use structured object with given, formula, steps, final
- If subject is English/Literature: Use structured object with introduction, explanation, analysis, conclusion OR string with embedded headings
- If subject is Science: Use structured object with definition, explanation, example, conclusion OR string with embedded headings
- If subject is Social Science: Use structured object with background, key_points, explanation, conclusion OR string with embedded headings

For 2-3 mark questions: Use simple string format, but MUST provide an answer.

For 1 mark questions: Use simple string format, but MUST provide an answer.

Now generate the questions strictly within the allowed limit, ensuring answer lengths match the mark requirements exactly and follow the difficulty-based structure. REMEMBER: EVERY question MUST have a correct_answer field.

[CRITICAL] FINAL VERIFICATION BEFORE OUTPUTTING JSON:
1. Generate HIGH-QUALITY questions from the content (up to {actual_num_questions} if content supports)
2. Verify all questions are UNIQUE (no repetition of patterns, equations, or ideas)
3. Verify all questions are supported by the content (no invented or stretched content)
4. Verify distribution as closely as possible (quality over exact matching)
5. If you have fewer than {actual_num_questions} questions but they are all high-quality, that is ACCEPTABLE
6. Only output JSON when you have verified quality and uniqueness

CRITICAL: Quality is MORE IMPORTANT than quantity. Generate only as many high-quality questions as the content clearly supports."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Extract token usage
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        
        # Calculate estimated cost (GPT-4o-mini pricing as of 2024)
        # Input: $0.00015 per 1K tokens, Output: $0.0006 per 1K tokens
        estimated_cost_usd = (prompt_tokens / 1000 * 0.00015) + (completion_tokens / 1000 * 0.0006)
        estimated_cost_str = f"${estimated_cost_usd:.4f}"
        
        # Store usage in database (async, don't block)
        # Note: We'll link user_id and qna_set_id later in the router
        try:
            from app.database import SessionLocal
            from app.models import AIUsageLog
            db = SessionLocal()
            usage_log = AIUsageLog(
                model="gpt-4o-mini",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost_str
            )
            db.add(usage_log)
            db.commit()
            db.refresh(usage_log)
            usage_log_id = usage_log.id
            db.close()
        except Exception as log_error:
            print(f"⚠️  Failed to log AI usage: {log_error}")
            usage_log_id = None
        
        # Check threshold and alert if needed (non-blocking)
        try:
            check_ai_usage_threshold()
        except Exception as threshold_error:
            print(f"⚠️  Failed to check threshold: {threshold_error}")
        
        # Get response content
        response_content = response.choices[0].message.content.strip()
        
        # Clean and fix common JSON issues
        try:
            # Remove any markdown code blocks if present
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON
            result = json.loads(response_content)
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Error position: line {e.lineno}, column {e.colno}")
            print(f"Response content length: {len(response_content)}")
            print(f"Response content (first 1000 chars): {response_content[:1000]}")
            if len(response_content) > 1000:
                print(f"Response content (last 500 chars): {response_content[-500:]}")
            
            # Try to fix common JSON issues
            fixed_content = response_content
            
            # Fix 1: Try to extract JSON from response if it's embedded in text
            json_match = re.search(r'\{.*\}', fixed_content, re.DOTALL)
            if json_match:
                fixed_content = json_match.group(0)
            
            # Fix 2: Try to close unterminated strings near the error position
            if e.msg and "Unterminated string" in e.msg:
                # Find the problematic string and try to close it
                error_pos = e.pos if hasattr(e, 'pos') else len(fixed_content)
                
                # Look for the opening quote before the error
                start_pos = fixed_content.rfind('"', 0, error_pos)
                if start_pos >= 0:
                    # Check if this quote is escaped
                    if start_pos > 0 and fixed_content[start_pos-1] == '\\':
                        # Escaped quote, skip
                        pass
                    else:
                        # Find where the string should end (before next unescaped quote or end of line/object)
                        # Look for closing quote, comma, or brace after error position
                        search_end = min(error_pos + 500, len(fixed_content))
                        end_pos = fixed_content.find('"', error_pos, search_end)
                        
                        if end_pos < 0:
                            # No closing quote found, try to add one before the next structural character
                            next_comma = fixed_content.find(',', error_pos, search_end)
                            next_brace = fixed_content.find('}', error_pos, search_end)
                            next_bracket = fixed_content.find(']', error_pos, search_end)
                            
                            insert_pos = error_pos
                            if next_comma > 0:
                                insert_pos = min(insert_pos, next_comma) if insert_pos > 0 else next_comma
                            if next_brace > 0:
                                insert_pos = min(insert_pos, next_brace) if insert_pos > 0 else next_brace
                            if next_bracket > 0:
                                insert_pos = min(insert_pos, next_bracket) if insert_pos > 0 else next_bracket
                            
                            if insert_pos > error_pos:
                                fixed_content = fixed_content[:insert_pos] + '"' + fixed_content[insert_pos:]
                                print(f"⚠️  Attempted to fix unterminated string at position {error_pos}")
            
            # Try parsing the fixed content
            try:
                result = json.loads(fixed_content)
                print("✅ Successfully parsed JSON after fixing")
            except json.JSONDecodeError as e2:
                print(f"❌ Still failed after fixes: {e2}")
                # Last resort: try to extract just the questions array
                questions_match = re.search(r'"questions"\s*:\s*\[.*?\]', fixed_content, re.DOTALL)
                if questions_match:
                    try:
                        # Try to reconstruct a minimal valid JSON
                        questions_json = '{"questions": ' + questions_match.group(0).split(':', 1)[1].strip() + '}'
                        result = json.loads(questions_json)
                        print("✅ Successfully extracted questions array")
                    except:
                        raise ValueError(
                            f"Failed to parse AI response as JSON after all fixes. "
                            f"Original error: {str(e)}. "
                            f"Fix error: {str(e2)}. "
                            f"Response preview: {response_content[:500]}..."
                        )
                else:
                    raise ValueError(
                        f"Failed to parse AI response as JSON. "
                        f"Error: {str(e)}. "
                        f"Error at line {e.lineno}, column {e.colno}. "
                        f"Response preview: {response_content[:500]}..."
                    )
        
        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError(f"AI response is not a dictionary. Got: {type(result)}")
        
        if "questions" not in result:
            raise ValueError("AI response does not contain 'questions' field")
        
        if not isinstance(result.get("questions"), list):
            raise ValueError("AI response 'questions' field is not a list")
        
        # Validate exact distribution matching
        questions = result.get("questions", [])
        actual_count = len(questions)
        
        # Check if count matches expected
        expected_count = sum(item.get("count", 0) for item in distribution_list)
        print(f"Question count check: Expected={expected_count}, Got={actual_count}, Remaining={remaining_questions}")
        
        if actual_count < expected_count:
            print(f"INFO: AI generated {actual_count} high-quality questions (requested {expected_count})")
            print(f"   This is acceptable - quality over quantity. Content may not support more questions.")
            print(f"   Distribution requested: {distribution_list}")
            print(f"   Total expected: {expected_count}, Got: {actual_count}, Difference: {expected_count - actual_count}")
            
            # Check distribution breakdown
            if distribution_list:
                print(f"   Distribution breakdown:")
                for dist_item in distribution_list:
                    marks = dist_item.get('marks', 0)
                    count = dist_item.get('count', 0)
                    q_type = dist_item.get('type', 'unknown')
                    actual_for_this = len([q for q in questions if q.get('marks') == marks and q.get('type', '').lower() == q_type.lower()])
                    print(f"     - {count} questions of {marks} marks ({q_type}): Expected {count}, Got {actual_for_this}, Difference {count - actual_for_this}")
            
            print(f"   Questions received: {[q.get('question', 'N/A')[:50] for q in questions]}")
            # Accept the result - quality over quantity. Do not retry.
            # Store the actual count for frontend notification
            result["actual_question_count"] = actual_count
            result["requested_question_count"] = expected_count
        
        if actual_count != expected_count and actual_count != remaining_questions:
            print(f"Question count mismatch: Expected {expected_count}, Got {actual_count}, Remaining: {remaining_questions}")
            # If we got more than allowed, truncate
            if actual_count > remaining_questions:
                print(f"Truncating questions from {actual_count} to {remaining_questions}")
                questions = questions[:remaining_questions]
                result["questions"] = questions
            # If we got fewer, log it but keep what we have
        
        # Validate distribution matches
        distribution_validation = _validate_distribution(questions, distribution_list)
        if not distribution_validation["valid"]:
            print(f"Distribution mismatch: {distribution_validation['message']}")
            # Try to fix distribution, but ensure we don't lose questions
            fixed_questions = _fix_distribution(questions, distribution_list, remaining_questions)
            if len(fixed_questions) < len(questions) and len(fixed_questions) < remaining_questions:
                # If fixing reduced the count, try to keep all questions and just reorder
                print(f"Fixing distribution reduced count from {len(questions)} to {len(fixed_questions)}. Attempting to preserve all questions...")
                # Keep all questions, just ensure we don't exceed limit
                questions = questions[:remaining_questions]
            else:
                questions = fixed_questions
            result["questions"] = questions
        
        # Ensure all questions have required fields
        for i, q in enumerate(questions):
            if "id" not in q:
                q["id"] = i + 1
            if "difficulty" not in q:
                q["difficulty"] = difficulty
            # Normalize type field
            q_type = q.get("type", "").lower()
            if q_type == "short":
                q["type"] = "short"
            elif q_type == "mcq" or q_type == "multiple_choice":
                q["type"] = "mcq"
            elif q_type == "descriptive" or q_type == "long":
                q["type"] = "descriptive"
            else:
                # Infer from marks
                marks = q.get("marks", 0)
                if marks <= 2:
                    q["type"] = "mcq" if "options" in q else "short"
                else:
                    q["type"] = "descriptive"
            
            # Normalize answer field: ensure all questions have "correct_answer"
            # AI may generate "answer" for descriptive/short, or "correct_answer" for MCQ
            if "answer" in q and "correct_answer" not in q:
                # Convert "answer" to "correct_answer" for consistency
                q["correct_answer"] = q.pop("answer")
            elif "correct_answer" not in q:
                # If neither exists, this is an error - log it
                print(f"❌ ERROR: Question {idx+1} (marks={q.get('marks', 'unknown')}) has NO answer field!")
                print(f"   Question text: {q.get('question', 'N/A')[:100]}...")
                # Set a default but this should not happen
                q["correct_answer"] = "N/A - Answer not generated by AI"
            
            # Validate that answer is not empty
            answer = q.get("correct_answer", "")
            if not answer or answer == "N/A" or (isinstance(answer, dict) and len(answer) == 0):
                print(f"⚠️  WARNING: Question {idx+1} (marks={q.get('marks', 'unknown')}) has empty/invalid answer!")
                print(f"   Answer value: {answer}")
                print(f"   This question should be regenerated!")
            
            # Ensure difficulty field exists (for difficulty-based formatting)
            if "difficulty" not in q:
                q["difficulty"] = difficulty
            
            # For mathematics questions, ensure steps and derivation are preserved
            # Steps array should be preserved if present (for medium/hard questions)
            if "steps" in q and not isinstance(q["steps"], list):
                # Convert string to list if needed
                q["steps"] = [q["steps"]] if q["steps"] else []
            
            # Derivation field should be preserved for hard questions
            if "derivation" not in q and q.get("difficulty") == "hard":
                # Derivation is optional but recommended for hard questions
                pass
            
            # Ensure explanation field exists (for exam-style answers)
            if "explanation" not in q and q.get("type") in ["descriptive", "short"]:
                # Explanation is optional but recommended
                pass
            
            # Ensure MCQ has options
            if q["type"] == "mcq" and "options" not in q:
                print(f"⚠️  MCQ question missing options, converting to short answer")
                q["type"] = "short"
            
            # Ensure correct_answer field exists for MCQ
            if q["type"] == "mcq" and "correct_answer" not in q and "options" in q:
                # Use first option as default
                q["correct_answer"] = q["options"][0] if q["options"] else ""
        
        # Track question count at each step
        expected_count = sum(item.get("count", 0) for item in distribution_list)
        count_before_duplicate_check = len(questions)
        print(f"Step 1 - After parsing: {count_before_duplicate_check} questions")
        
        # Check for duplicate questions (applies to all languages) - just log, don't remove yet
        _check_duplicate_questions(questions)
        count_after_duplicate_check = len(questions)
        
        # Auto-check exam quality (strict validation)
        questions, has_format_repetition = _validate_exam_quality(questions, difficulty)
        count_after_validation = len(questions)
        print(f"Step 2 - After validation: {count_after_validation} questions")
        
        # Remove duplicate questions (exact or very similar)
        questions = _remove_duplicate_questions(questions)
        count_after_dedup = len(questions)
        if count_after_dedup < count_after_validation:
            print(f"Removed {count_after_validation - count_after_dedup} duplicate question(s). Remaining: {count_after_dedup}")
        
        # Log format repetition but don't retry - accept the result
        if has_format_repetition:
            print(f"INFO: Format repetition detected but accepting questions. Quality over quantity.")
        
        if count_after_validation != count_before_duplicate_check:
            print(f"INFO: Validation changed count from {count_before_duplicate_check} to {count_after_validation}")
            print(f"   This is acceptable - quality over quantity. Some questions may have been removed for quality.")
        
        # Accept quality questions - don't enforce exact count
        if count_after_validation < expected_count:
            print(f"INFO: After validation, we have {count_after_validation} quality questions (requested {expected_count})")
            print(f"   Accepting result - quality over quantity. Content may not support more questions.")
        elif count_after_validation > expected_count:
            # If we have more than expected, keep exactly the expected number
            print(f"INFO: Trimming to exactly {expected_count} questions (had {count_after_validation})")
            questions = questions[:expected_count]
        
        # Post-process 10-mark math questions: convert LaTeX to board-style format
        from app.post_process_math import post_process_10mark_math
        count_before_postprocess = len(questions)
        questions = post_process_10mark_math(questions)
        count_after_postprocess = len(questions)
        print(f"📊 Step 3 - After post-processing: {count_after_postprocess} questions")
        if count_after_postprocess != count_before_postprocess:
            print(f"⚠️  WARNING: Post-processing changed count from {count_before_postprocess} to {count_after_postprocess}")
        
        # Final count check - accept quality questions, don't raise errors
        final_count = len(questions)
        if final_count != expected_count:
            if final_count < expected_count:
                print(f"INFO: Final count: Generated {final_count} quality questions (requested {expected_count})")
                print(f"   Accepting result - quality over quantity. Content may not support more questions.")
            else:
                print(f"INFO: Final count: Generated {final_count} questions (requested {expected_count})")
                # Truncate to expected count if we got more
                questions = questions[:expected_count]
                final_count = len(questions)
        else:
            print(f"INFO: Final count: Exactly {final_count} questions (as requested)")
        
        # Store usage log ID for later linking
        if usage_log_id:
            result["_usage_log_id"] = usage_log_id
        
        result["questions"] = questions
        return result
        
    except Exception as e:
        print(f"AI generation error: {e}")
        raise

def _check_duplicate_questions(questions: List[Dict[str, Any]]) -> None:
    """
    Check for duplicate or very similar questions across all languages.
    Logs warnings if duplicates are detected.
    """
    if len(questions) < 2:
        return
    
    # Normalize question text for comparison (remove extra whitespace, lowercase)
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespace and convert to lowercase for comparison
        normalized = " ".join(text.lower().split())
        # Remove common punctuation for better matching
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    duplicates_found = []
    seen_questions = {}
    
    for i, q1 in enumerate(questions):
        question_text = q1.get("question", "").strip()
        if not question_text:
            continue
        
        normalized_q1 = normalize_text(question_text)
        
        # Check against previously seen questions
        for j, normalized_q2 in seen_questions.items():
            # Calculate similarity (simple word overlap)
            words1 = set(normalized_q1.split())
            words2 = set(normalized_q2.split())
            
            if len(words1) == 0 or len(words2) == 0:
                continue
            
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            similarity = intersection / union if union > 0 else 0
            
            # If similarity is very high (>80%), consider it a duplicate
            if similarity > 0.8:
                duplicates_found.append({
                    "index1": j + 1,
                    "index2": i + 1,
                    "question1": questions[j].get("question", "")[:100],
                    "question2": question_text[:100],
                    "similarity": similarity
                })
        
        # Store this question for future comparisons
        seen_questions[i] = normalized_q1
    
    if duplicates_found:
        print(f"WARNING: Found {len(duplicates_found)} potential duplicate question(s):")
        for dup in duplicates_found:
            print(f"   - Question {dup['index1']} and Question {dup['index2']} are very similar "
                  f"(similarity: {dup['similarity']:.1%})")
            print(f"     Q{dup['index1']}: {dup['question1']}...")
            print(f"     Q{dup['index2']}: {dup['question2']}...")
        print("   The AI should generate unique questions covering different topics/concepts.")
    else:
        print("No duplicate questions detected - all questions are unique")

def _remove_duplicate_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate or very similar questions from the list.
    Returns a list with duplicates removed, keeping the first occurrence.
    """
    if len(questions) < 2:
        return questions
    
    # Normalize question text for comparison
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        normalized = " ".join(text.lower().split())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    unique_questions = []
    seen_normalized = set()
    removed_count = 0
    
    for q in questions:
        question_text = q.get("question", "").strip()
        if not question_text:
            unique_questions.append(q)  # Keep questions without text
            continue
        
        normalized = normalize_text(question_text)
        
        # Check if this is a duplicate
        is_duplicate = False
        for seen_norm in seen_normalized:
            words1 = set(normalized.split())
            words2 = set(seen_norm.split())
            
            if len(words1) == 0 or len(words2) == 0:
                continue
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            similarity = intersection / union if union > 0 else 0
            
            # If similarity is very high (>80%), it's a duplicate
            if similarity > 0.8:
                is_duplicate = True
                removed_count += 1
                break
        
        if not is_duplicate:
            unique_questions.append(q)
            seen_normalized.add(normalized)
    
    if removed_count > 0:
        print(f"Removed {removed_count} duplicate question(s). Remaining: {len(unique_questions)}")
    
    return unique_questions

def _build_distribution_list(marks_pattern: str, qna_type: str, num_questions: int) -> List[Dict[str, Any]]:
    """
    Build distribution list from marks pattern and question type
    Returns list of dicts: [{"marks": 10, "count": 5, "type": "descriptive"}, ...]
    """
    marks_pattern = str(marks_pattern).lower() if marks_pattern else "mixed"
    distribution_list = []
    
    if marks_pattern == "mixed":
        if qna_type == "mcq":
            # MCQs: 1-2 marks
            count_1 = num_questions // 2
            count_2 = num_questions - count_1
            if count_1 > 0:
                distribution_list.append({"marks": 1, "count": count_1, "type": "mcq"})
            if count_2 > 0:
                distribution_list.append({"marks": 2, "count": count_2, "type": "mcq"})
        elif qna_type == "descriptive":
            # Descriptive: 3, 5, 10 marks
            count_3 = num_questions // 3
            count_5 = num_questions // 3
            count_10 = num_questions - count_3 - count_5
            if count_3 > 0:
                distribution_list.append({"marks": 3, "count": count_3, "type": "descriptive"})
            if count_5 > 0:
                distribution_list.append({"marks": 5, "count": count_5, "type": "descriptive"})
            if count_10 > 0:
                distribution_list.append({"marks": 10, "count": count_10, "type": "descriptive"})
        else:  # mixed type
            # Mix: MCQs (1-2), Short (1-2), Descriptive (3-10)
            mcq_count = num_questions // 3
            short_count = num_questions // 3
            desc_count = num_questions - mcq_count - short_count
            
            if mcq_count > 0:
                distribution_list.append({"marks": 1, "count": mcq_count, "type": "mcq"})
            if short_count > 0:
                distribution_list.append({"marks": 2, "count": short_count, "type": "short"})
            if desc_count > 0:
                # Distribute descriptive across 3, 5, 10
                desc_3 = desc_count // 3
                desc_5 = desc_count // 3
                desc_10 = desc_count - desc_3 - desc_5
                if desc_3 > 0:
                    distribution_list.append({"marks": 3, "count": desc_3, "type": "descriptive"})
                if desc_5 > 0:
                    distribution_list.append({"marks": 5, "count": desc_5, "type": "descriptive"})
                if desc_10 > 0:
                    distribution_list.append({"marks": 10, "count": desc_10, "type": "descriptive"})
    else:
        # Single mark pattern
        try:
            mark_value = int(marks_pattern)
            # Respect user's explicit question type selection
            # If user selected "descriptive", use descriptive even for 1-2 marks
            # If user selected "mcq", use mcq for 1-2 marks
            # Otherwise, infer from marks
            if qna_type == "descriptive":
                q_type = "descriptive"  # Respect user's choice
            elif qna_type == "mcq":
                q_type = "mcq" if mark_value <= 2 else "descriptive"
            else:
                # Infer from marks if type is "mixed" or "short"
                if mark_value <= 2:
                    q_type = "mcq" if qna_type == "mcq" else "short"
                else:
                    q_type = "descriptive"
            
            distribution_list.append({
                "marks": mark_value,
                "count": num_questions,
                "type": q_type
            })
        except ValueError:
            # Invalid pattern, default to mixed
            return _build_distribution_list("mixed", qna_type, num_questions)
    
    return distribution_list

def _validate_distribution(questions: List[Dict[str, Any]], distribution_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that generated questions match the requested distribution
    Returns: {"valid": bool, "message": str}
    """
    # Count questions by marks and type
    actual_distribution = {}
    for q in questions:
        marks = q.get("marks", 0)
        q_type = q.get("type", "").lower()
        key = f"{marks}_{q_type}"
        actual_distribution[key] = actual_distribution.get(key, 0) + 1
    
    # Check against requested distribution
    for item in distribution_list:
        marks = item.get("marks", 0)
        q_type = item.get("type", "").lower()
        count = item.get("count", 0)
        key = f"{marks}_{q_type}"
        actual_count = actual_distribution.get(key, 0)
        
        if actual_count != count:
            return {
                "valid": False,
                "message": f"Expected {count} questions of {marks} marks ({q_type}), got {actual_count}"
            }
    
    return {"valid": True, "message": "Distribution matches"}

def _fix_distribution(questions: List[Dict[str, Any]], distribution_list: List[Dict[str, Any]], max_questions: int) -> List[Dict[str, Any]]:
    """
    Attempt to fix distribution by reordering or adjusting questions.
    Preserves all questions if possible, only removes if absolutely necessary.
    """
    if len(questions) <= max_questions:
        # If we have the right number or fewer, just return them (preserve all)
        return questions[:max_questions]
    
    # Group questions by marks and type
    questions_by_key = {}
    for q in questions:
        marks = q.get("marks", 0)
        q_type = q.get("type", "").lower()
        key = f"{marks}_{q_type}"
        if key not in questions_by_key:
            questions_by_key[key] = []
        questions_by_key[key].append(q)
    
    # Build new list according to distribution
    fixed_questions = []
    used_questions = set()  # Track which questions we've used
    
    for item in distribution_list:
        marks = item.get("marks", 0)
        q_type = item.get("type", "").lower()
        count = item.get("count", 0)
        key = f"{marks}_{q_type}"
        
        available = questions_by_key.get(key, [])
        # Take up to requested count
        for q in available[:count]:
            if id(q) not in used_questions:
                fixed_questions.append(q)
                used_questions.add(id(q))
    
    # If we have fewer than max, try to fill from other questions (preserve all if possible)
    if len(fixed_questions) < max_questions:
        remaining = max_questions - len(fixed_questions)
        # Add remaining questions from any available (prioritize matching distribution, then any)
        for item in distribution_list:
            if remaining <= 0:
                break
            marks = item.get("marks", 0)
            q_type = item.get("type", "").lower()
            key = f"{marks}_{q_type}"
            available = questions_by_key.get(key, [])
            for q in available:
                if id(q) not in used_questions:
                    fixed_questions.append(q)
                    used_questions.add(id(q))
                    remaining -= 1
                    if remaining <= 0:
                        break
        
        # If still need more, add any remaining questions
        if remaining > 0:
            for q in questions:
                if id(q) not in used_questions:
                    fixed_questions.append(q)
                    used_questions.add(id(q))
                    remaining -= 1
                    if remaining <= 0:
                        break
    
    # Only truncate if we have more than max (shouldn't happen, but safety check)
    if len(fixed_questions) > max_questions:
        print(f"⚠️  Truncating fixed questions from {len(fixed_questions)} to {max_questions}")
        return fixed_questions[:max_questions]
    
    return fixed_questions

def check_ai_usage_threshold():
    """Check if AI usage has reached threshold and send alert if needed"""
    from app.database import SessionLocal
    from app.models import AIUsageLog
    from datetime import datetime, timedelta
    from app.config import settings
    
    db = SessionLocal()
    try:
        # Get current month usage
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        total_tokens = db.query(func.sum(AIUsageLog.total_tokens)).filter(
            AIUsageLog.created_at >= month_start
        ).scalar() or 0
        
        threshold = settings.AI_USAGE_THRESHOLD_TOKENS
        
        if total_tokens >= threshold:
            # Send alert
            alert_message = f"""
            ⚠️  AI API Usage Alert ⚠️
            
            Current Usage: {total_tokens:,} tokens
            Threshold: {threshold:,} tokens
            Percentage: {(total_tokens / threshold * 100):.1f}%
            
            The AI API usage has reached the configured threshold.
            Please recharge your OpenAI API key soon to avoid service interruption.
            
            Date: {now.strftime('%Y-%m-%d %H:%M:%S')}
            """
            print("=" * 60)
            print(alert_message)
            print("=" * 60)
            
            # Send email alert if configured (note: email sending is async, this is just a placeholder)
            if settings.AI_USAGE_ALERT_EMAIL:
                print(f"📧 Email alert should be sent to: {settings.AI_USAGE_ALERT_EMAIL}")
                print("   (Email sending requires async context - implement in router if needed)")
        elif total_tokens >= threshold * 0.8:
            # Warning at 80%
            print(f"⚠️  AI Usage Warning: {total_tokens:,}/{threshold:,} tokens ({total_tokens / threshold * 100:.1f}%)")
    finally:
        db.close()

