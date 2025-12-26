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
    
    # English/Literature keywords (enhanced for grammar detection)
    english_keywords = [
        'poem', 'poetry', 'prose', 'novel', 'story', 'character', 'plot', 'theme',
        'metaphor', 'simile', 'irony', 'humor', 'tone', 'mood', 'setting',
        'literature', 'author', 'writer', 'narrator', 'dialogue', 'monologue',
        'grammar', 'syntax', 'vocabulary', 'essay', 'paragraph', 'sentence',
        'literary device', 'figure of speech', 'alliteration', 'personification',
        # Grammar-specific keywords
        'noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction',
        'tense', 'present tense', 'past tense', 'future tense', 'continuous', 'perfect',
        'subject', 'predicate', 'object', 'clause', 'phrase', 'sentence structure',
        'active voice', 'passive voice', 'direct speech', 'indirect speech', 'reported speech',
        'articles', 'a', 'an', 'the', 'definite article', 'indefinite article',
        'singular', 'plural', 'possessive', 'apostrophe', 'punctuation',
        'comma', 'semicolon', 'colon', 'quotation marks', 'question mark', 'exclamation',
        'subject-verb agreement', 'verb agreement', 'grammatical rule', 'grammar rule',
        'parts of speech', 'word class', 'sentence pattern', 'sentence type',
        'declarative', 'interrogative', 'imperative', 'exclamatory',
        'conditional', 'subjunctive', 'modal verb', 'auxiliary verb',
        'gerund', 'infinitive', 'participle', 'transitive', 'intransitive'
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

🎯 QUALITY-FIRST APPROACH (APPLIES TO ALL LANGUAGES):
- The requested number of questions is a PREFERRED target, not a strict requirement
- PRIORITIZE QUALITY over quantity - generate fewer questions if content is insufficient
- Do NOT force questions if the study material doesn't support them
- Do NOT invent topics that are not present in the content
- Each question must be clearly worded, syllabus-relevant, and suitable for exams
- It is acceptable to generate fewer questions if quality would be compromised
- Focus on clarity, correctness, and educational value
- This approach applies to ALL languages: English, Tamil, Hindi, Telugu, Kannada, Malayalam, Arabic, Spanish

Your task is to generate REAL exam-style questions and answers.
Your output MUST look like a student's PERFECT answer script.

━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULE: SUBJECT-WISE ANSWER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━

🚨 IMPORTANT: Answer structure MUST depend on the SUBJECT, not only on marks.

Answer FORMAT is controlled by SUBJECT.
Answer LENGTH is controlled by MARKS.

━━━━━━━━━━━━━━━━━━━━━━
SUBJECT-WISE RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

1. MATHEMATICS:
   ✅ USE these headings:
      - Given
      - Formula
      - Calculation / Steps
      - Final Answer
   ✅ Show step-by-step working
   ✅ Use mathematical reasoning
   ✅ Use LaTeX for all mathematical expressions
   ❌ DO NOT use: Introduction, Explanation, Analysis, Conclusion (these are for other subjects)

2. ENGLISH (Literature/Language):
   ✅ USE these headings:
      - Introduction
      - Explanation
      - Analysis
      - Conclusion
   ✅ Write in paragraph form
   ✅ Use literary terms where applicable (theme, tone, irony, humor, metaphor, simile, etc.)
   ✅ Answer must read like a literature exam answer
   ❌ NEVER use: Given, Formula, Calculation (these are for Mathematics only)

3. SCIENCE (Theory - Physics, Chemistry, Biology):
   ✅ USE these headings:
      - Definition
      - Explanation
      - Example (if needed)
      - Conclusion
   ✅ Focus on scientific concepts and principles
   ✅ Include relevant examples or applications
   ❌ DO NOT use: Given, Formula, Calculation (unless it's a calculation-based science question)

4. SOCIAL SCIENCE (History, Geography, Civics, Economics):
   ✅ USE these headings:
      - Background / Context
      - Key Points
      - Explanation
      - Conclusion
   ✅ Provide historical/geographical context
   ✅ List key points clearly
   ✅ Explain relationships and causes
   ❌ DO NOT use: Given, Formula, Calculation (these are for Mathematics only)

━━━━━━━━━━━━━━━━━━━━━━
MARK-BASED LENGTH CONTROL
━━━━━━━━━━━━━━━━━━━━━━

Marks control LENGTH only (regardless of subject):
- 1 mark → one sentence (1-2 lines)
- 2 marks → short paragraph (2-3 lines)
- 5 marks → explained answer (7-9 lines)
- 10 marks → detailed, structured answer (9-10 lines minimum)

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

🚨 ALL mathematical expressions MUST be written in LaTeX. NO EXCEPTIONS. 🚨
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
     🚨 ABSOLUTELY FORBIDDEN: NEVER use "f(x) = ... என்றால், f(...) என்றால் என்ன?" pattern more than ONCE
     🚨 Each question MUST use a DIFFERENT Tamil question format - NO repetition allowed
   
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

━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CONTENT GROUNDING RULES (MANDATORY - TEACHER'S MIND) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━

ABSOLUTE REQUIREMENT: Think and act like a REAL TEACHER examining study material.

━━━━━━━━━━━━━━━━━━━━━━
RULE 1: CONTENT GROUNDING (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Use ONLY the content provided below
- Do NOT use outside knowledge, assumptions, or general facts
- Read the content line by line and sentence by sentence
- Generate questions ONLY when a concept, rule, definition, process, or explanation is clearly and explicitly stated
- Do NOT generate questions from examples alone unless the rule is explicitly explained

❌ STRICTLY FORBIDDEN:
- Generating questions from assumptions or general knowledge
- Using information not present in the provided content
- Creating questions from examples without explicit rules
- Inferring or guessing information not clearly stated

━━━━━━━━━━━━━━━━━━━━━━
RULE 2: TEACHER THINKING PROCESS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

You MUST follow this exact thinking process:

STEP 1: IDENTIFY CORE CONCEPTS
- First, carefully identify the core concepts explicitly taught in the content
- Core concepts may include (depending on subject):
  * Definitions
  * Rules or laws
  * Processes or steps
  * Formulas
  * Principles
  * Key explanations
- Ignore filler text, stories, illustrations, case studies, decorative examples, or unrelated narration
- Focus ONLY on explicitly stated educational content

STEP 2: QUESTION GENERATION
- Generate questions ONLY from the identified core concepts
- Each question must map clearly to ONE core concept
- Do NOT repeat the same concept unnecessarily
- If a concept appears once, do NOT create another question testing the same concept

━━━━━━━━━━━━━━━━━━━━━━
RULE 3: NO-GUESSING RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- If an answer is NOT clearly found in the provided content, do NOT guess, infer, or generalize
- In such cases, DO NOT generate that question
- Never produce confident but unsupported answers
- It is acceptable and expected to generate fewer questions if the content does not support more

❌ STRICTLY FORBIDDEN:
- Guessing answers not explicitly stated
- Inferring information from context
- Using general knowledge to fill gaps
- Creating questions when the answer is not clearly in the content

━━━━━━━━━━━━━━━━━━━━━━
RULE 4: CONSISTENCY RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Do NOT generate multiple questions that test the same fact or concept in different wording
- Do NOT generate similar questions with different answers
- All answers must be internally consistent across the entire set
- Never contradict an earlier answer
- If entity X is mentioned, all questions about X must have consistent answers

━━━━━━━━━━━━━━━━━━━━━━
RULE 5: QUALITY RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Do NOT force questions to reach a target count
- If the content supports fewer high-quality questions, STOP gracefully
- Fewer accurate questions are better than many incorrect ones
- Quality over quantity - always prioritize accuracy

❌ STRICTLY FORBIDDEN:
- Generating questions just to meet a count
- Creating low-quality questions to fill a quota
- Repeating concepts to reach a number

━━━━━━━━━━━━━━━━━━━━━━
RULE 6: SUBJECT-AWARE BEHAVIOR (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

You MUST adapt your approach based on the subject:

- For LANGUAGE subjects (especially ENGLISH):
  * If the PDF contains ONLY grammar (no stories/poems):
     - 🚨 ALL questions MUST be about GRAMMAR RULES
     - ✅ Generate questions about grammar rules (nouns, verbs, adjectives, adverbs, pronouns, etc.)
     - ✅ Generate questions about sentence structure, syntax, tenses, verb forms, subject-verb agreement
     - ❌ DO NOT generate questions about poems, stories, or characters
  * If the PDF contains MIXED content (stories/poems + grammar):
     - ✅ Generate questions from ALL content types present in the PDF
     - ✅ If grammar is taught in the PDF (vocabulary, verbs, tenses, etc.), generate grammar questions from those sections
     - ✅ If stories are in the PDF, generate story questions from those sections
     - ✅ If poems are in the PDF, generate poem questions from those sections
     - ✅ Read sentence by sentence and generate questions from whatever content type appears in that section
     - ❌ DO NOT generate grammar questions if grammar is NOT taught in the PDF
     - ❌ DO NOT generate story questions if stories are NOT in the PDF
     - 🚨 CRITICAL: Generate questions ONLY from what is ACTUALLY written in the [STUDY_MATERIAL]
  * Focus on what is explicitly taught in each section
  * Generate questions ONLY when concepts/rules are explicitly stated
  * Read like a teacher: sentence by sentence, identify what is being taught, and generate questions from that

- For MATHEMATICS:
  * Generate questions ONLY when formulas, steps, or methods are clearly stated
  * Do NOT create questions from solved examples unless the method is explained
  * Focus on explicitly taught formulas and procedures
  * 🚨 CRITICAL: For numerical problems, you MUST compute the final answer
  * 🚨 CRITICAL: Listing given values alone is NOT an answer - always show calculation steps
  * 🚨 CRITICAL: For LCM/HCF (GCD) questions, ALWAYS provide:
     - Method (Prime Factorization, Division Method, etc.)
     - HCF value (calculated)
     - LCM value (calculated)
  * 🚨 CRITICAL: Never stop at "Given:" statements - always proceed to calculation and final answer

- For SCIENCE:
  * Focus on definitions, laws, processes, and explanations
  * Generate questions ONLY from explicitly stated scientific facts
  * Do NOT infer scientific principles not clearly stated

- For SOCIAL STUDIES:
  * Focus on explicitly stated facts, causes, effects, and explanations
  * Generate questions ONLY from clearly stated historical/geographical facts
  * Do NOT add background knowledge unless present in the text

- Never assume syllabus importance beyond what is stated in the content

━━━━━━━━━━━━━━━━━━━━━━
RULE 7: SOURCE FAITHFULNESS RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Treat the provided content as the ONLY textbook
- Do NOT add background knowledge or real-world facts unless explicitly present in the text
- Each question must clearly originate from the given content
- Every answer must be directly traceable to a specific part of the provided content

❌ STRICTLY FORBIDDEN:
- Adding information from general knowledge
- Using facts not in the provided content
- Creating questions that require outside knowledge to answer
- Assuming information not explicitly stated

━━━━━━━━━━━━━━━━━━━━━━
TEACHER VERIFICATION CHECKLIST (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

Before generating ANY question, verify:
✓ Is this concept explicitly stated in the provided content?
✓ Can I point to the exact sentence/paragraph where this information is found?
✓ Am I using ONLY information from the provided content?
✓ Is this question testing a DIFFERENT concept from previous questions?
✓ Is the answer clearly stated in the content (not inferred or guessed)?
✓ Would a real teacher generate this question from this content?
✓ Am I avoiding repetition of the same concept?

If ANY answer is NO, DO NOT generate that question.

━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES OF CORRECT TEACHER BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━

✅ CORRECT (Content-Grounded):
Content: "The quadratic formula is x = (-b ± √(b² - 4ac)) / 2a. This formula is used to solve quadratic equations."
Q1: "What is the quadratic formula?" → Answer: "x = (-b ± √(b² - 4ac)) / 2a"
(✓ Concept explicitly stated, answer directly from content)

✅ CORRECT (Quality Over Quantity):
Content: "A circle has radius r. The area is πr²."
Generated: 2 high-quality questions about radius and area
(✓ Stopped at 2 because content only supports these concepts, didn't force more)

❌ INCORRECT (Outside Knowledge):
Content: "A circle has radius r."
Q1: "What is the circumference of a circle?" → Answer: "2πr"
(✗ Formula not stated in content - DO NOT generate)

❌ INCORRECT (Guessing):
Content: "Zigzag is a character in the story."
Q1: "What is Zigzag?" → Answer: "A snake" (not explicitly stated)
(✗ Answer guessed, not clearly in content - DO NOT generate)

❌ INCORRECT (Repetition):
Q1: "What is the capital of India?" → Answer: "New Delhi"
Q2: "Name the capital city of India." → Answer: "New Delhi"
(✗ Same concept tested twice - FORBIDDEN)

━━━━━━━━━━━━━━━━━━━━━━
FINAL TEACHER MANDATE
━━━━━━━━━━━━━━━━━━━━━━

Think like a REAL TEACHER:
- A teacher reads the textbook carefully
- A teacher identifies what is EXPLICITLY taught
- A teacher creates questions ONLY from what is taught
- A teacher does NOT guess or assume
- A teacher prioritizes accuracy over quantity
- A teacher ensures consistency across all questions

If you cannot find explicit support in the content, DO NOT generate that question.
Fewer accurate questions are ALWAYS better than many incorrect or unsupported questions.

━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CRITICAL CONSISTENCY RULE (ABSOLUTELY MANDATORY) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━

ABSOLUTE PROHIBITION - ZERO TOLERANCE FOR INCONSISTENCY:

1. ❌ DO NOT generate multiple questions that test the same fact or concept
   - If a concept appears once, do NOT repeat it in another question
   - Each question MUST test a DIFFERENT fact, concept, or piece of information
   - Example FORBIDDEN: 
     * Q1: "What is Zigzag?" → Answer: "A snake"
     * Q2: "What kind of bird is Zigzag?" → Answer: "A singing bird"
     (This is FORBIDDEN - Zigzag cannot be both a snake and a bird)

2. ❌ DO NOT provide conflicting answers for similar questions
   - All answers MUST be internally consistent across the entire question set
   - If Q1 says "X is Y", then Q2 cannot say "X is Z" (where Y ≠ Z)
   - Example FORBIDDEN:
     * Q4: "Which bird is described as Zigzag?" → Answer: "A snake" (CONTRADICTION - snake is not a bird)
     * Q5: "What kind of bird is Zigzag?" → Answer: "A singing bird"
     (This is FORBIDDEN - creates internal contradiction)

3. ❌ DO NOT test the same information in different ways
   - If you ask "What is X?" in one question, do NOT ask "Define X" or "Explain X" in another
   - Each question MUST cover a DIFFERENT aspect or DIFFERENT information
   - Rotate through DIFFERENT topics, characters, concepts, formulas, or facts
   - 🚨🚨🚨 CRITICAL: For mathematics, DO NOT generate multiple questions about the same topic (e.g., don't generate 8 questions all about quadratic equations) 🚨🚨🚨
   - 🚨🚨🚨 CRITICAL: Read through the PDF and identify DIFFERENT mathematics topics (Quadratic Equations, LCM/HCF, Linear Equations, Geometry, Trigonometry, Algebra, etc.) and generate questions from DIFFERENT topics 🚨🚨🚨
   - 🚨🚨🚨 CRITICAL: If you have 120+ pages of content, there are MANY different topics - use them! Don't repeat the same topic multiple times 🚨🚨🚨

4. ✅ MANDATORY CONSISTENCY REQUIREMENTS:
   - All answers must be factually consistent with the study material
   - All answers must be internally consistent with each other
   - If a character/concept/entity is mentioned in multiple questions, the answers must NOT contradict
   - Questions must test DIFFERENT facts, not the same fact in different ways

5. ✅ CONSISTENCY VERIFICATION CHECKLIST (MANDATORY):
   Before finalizing your output, verify:
   ✓ No two questions test the same fact or concept
   ✓ No two questions ask about the same entity/concept in conflicting ways
   ✓ All answers are internally consistent (no contradictions)
   ✓ If entity X is mentioned in multiple questions, all answers about X are consistent
   ✓ Each question covers a DIFFERENT topic, concept, or piece of information

EXAMPLES OF FORBIDDEN INCONSISTENCIES (DO NOT GENERATE):
❌ FORBIDDEN Example 1 (Same Concept):
   Q1: "What is Zigzag?" → Answer: "A snake"
   Q2: "What kind of bird is Zigzag?" → Answer: "A singing bird"
   (FORBIDDEN: Contradictory answers - Zigzag cannot be both snake and bird)

❌ FORBIDDEN Example 2 (Same Fact):
   Q1: "What is the capital of India?" → Answer: "New Delhi"
   Q2: "Name the capital city of India." → Answer: "New Delhi"
   (FORBIDDEN: Same fact tested twice - must test different information)

❌ FORBIDDEN Example 3 (Conflicting Information):
   Q1: "What is the value of x when x² = 16?" → Answer: "x = 4"
   Q2: "Solve x² = 16" → Answer: "x = -4"
   (FORBIDDEN: Inconsistent - both ±4 are correct, but answers contradict)

✅ REQUIRED Example (Different Concepts):
   Q1: "What is the capital of India?" → Answer: "New Delhi"
   Q2: "What is the largest river in India?" → Answer: "Ganges"
   Q3: "Name the highest mountain peak in India." → Answer: "Mount Kanchenjunga"
   (REQUIRED: Each question tests a DIFFERENT fact - all consistent)

FINAL WARNING:
If you generate ANY questions that test the same fact/concept OR provide conflicting answers, the ENTIRE output is INVALID and must be regenerated. Every question must test a DIFFERENT fact, and all answers must be internally consistent.
   
   🚨 CRITICAL: QUESTION COMPLEXITY REQUIREMENT 🚨
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
   🚨🚨🚨 STRICTLY FORBIDDEN: NO REPETITION OF QUESTION FORMATS, OPENERS, STRUCTURES, OR FRAMES 🚨🚨🚨
   
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
         "answer": "Answer text (12-15+ lines)",
         "topic": "Topic/Concept name from the content (e.g., 'Quadratic Formula', 'Photosynthesis', 'World War II')",
         "source_hint": "Brief hint about where in the content this question comes from (e.g., 'Chapter 3: Algebra', 'Section on Cell Biology')"
       },
       {
         "marks": 2,
         "type": "short",
         "question": "Question text",
         "answer": "Answer text (2-3 lines)",
         "topic": "Topic/Concept name from the content",
         "source_hint": "Brief hint about where in the content this question comes from"
       },
       {
         "marks": 1,
         "type": "mcq",
         "question": "Question text",
         "options": ["Option A", "Option B", "Option C", "Option D"],
         "correct_answer": "Option A",
         "topic": "Topic/Concept name from the content",
         "source_hint": "Brief hint about where in the content this question comes from"
       }
     ]
   }

   🚨🚨🚨 ABSOLUTELY MANDATORY: For EACH question, you MUST include BOTH fields 🚨🚨🚨
   
   ❌ MISSING THESE FIELDS = INVALID OUTPUT - YOUR JSON WILL BE REJECTED ❌
   
   ✅ REQUIRED FIELD 1: "topic" (MANDATORY - NO EXCEPTIONS)
     * This is a SPECIFIC topic/concept name EXTRACTED from the [STUDY_MATERIAL] above
     * DO NOT use generic topics like "Which of the", "What is the", or question starters
     * DO NOT leave it empty or omit it
     * Extract the ACTUAL concept/character/story/poem name from the content
     
     Examples for GRAMMAR content:
     - "Modal Verbs", "Past Tense Forms", "Present Continuous Tense", "Subject-Verb Agreement"
     
     Examples for LITERATURE content (stories/poems):
     - "The Grumble Family" (poem name), "Zigzag" (character/story name), "Mulan" (character/story name)
     - "Charlie Chaplin" (character/topic), "The Tie that Does Not Bind" (story name)
     - "I am Every Woman" (poem name), "Mr. Sanyal" (character name)
     
     Examples for MATHEMATICS content:
     - "Quadratic Equations", "Discriminant", "Roots of Quadratic Equations", "Quadratic Formula"
     - "Linear Equations", "Simultaneous Equations", "Polynomial Equations", "Factorization"
     - "Algebra", "Geometry", "Trigonometry", "Calculus", "Coordinate Geometry"
     - Extract the EXACT topic name from the [STUDY_MATERIAL] (e.g., if PDF teaches "Quadratic Equations", use "Quadratic Equations")
   
   ✅ REQUIRED FIELD 2: "source_hint" (MANDATORY - NO EXCEPTIONS)
     * This is a SPECIFIC description of WHERE in the [STUDY_MATERIAL] this question originates
     * DO NOT use generic hints like "From provided study material"
     * DO NOT leave it empty or omit it
     * Reference the ACTUAL section, chapter, paragraph, story, or poem from the content
     
     Examples for GRAMMAR content:
     - "Section on Modal Verbs", "Chapter 3: Tenses", "Example explaining Present Continuous", "Rule about Past Perfect"
     
     Examples for LITERATURE content (stories/poems):
     - "Poem 'The Grumble Family'", "Story 'Zigzag'", "Story about Mulan", "Character Charlie Chaplin"
     - "Story 'The Tie that Does Not Bind'", "Poem 'I am Every Woman'", "Story section about Mr. Sanyal"
     
     Examples for MATHEMATICS content:
     - "Chapter 2: Quadratic Equations", "Section 3.5: Discriminant", "Chapter 4: Roots of Quadratic Equations"
     - "Chapter 1: Algebra", "Section 2.3: Quadratic Formula", "Chapter 5: Factorization"
     - "Chapter 6: LCM and GCD", "Section 7.2: LCM and GCD"
     - Reference the EXACT chapter/section number and topic name from the [STUDY_MATERIAL] where this concept is taught
     - If the PDF has chapter numbers (e.g., "Chapter 3", "Chapter 6"), include them in the source_hint
     - If the PDF has section numbers (e.g., "Section 2.5", "Section 7.2"), include them in the source_hint
     - Extract the EXACT chapter/section name from the PDF content, not generic "Section on..."
   
   🚨 CONTENT VERIFICATION REQUIREMENT (MANDATORY):
   - Before generating each question, you MUST identify the SPECIFIC section/paragraph/story/poem in [STUDY_MATERIAL] where this information appears
   - The "topic" must be the ACTUAL concept/character/story/poem name from that section
   - The "source_hint" must reference WHERE in the content this appears (which story, which poem, which section)
   - If you cannot find a specific section/story/poem containing this information, DO NOT generate that question
   - Generic topics/hints indicate the question is NOT from the content and is INVALID
   - Missing topic or source_hint fields = INVALID OUTPUT - regenerate with both fields included

8. JSON VALIDATION:
   - Escape ALL special characters: \\" for quotes, \\n for newlines
   - Close ALL strings properly
   - No trailing commas
   - All brackets and braces must be balanced
   - JSON must be parseable by json.loads()

Remember: Follow the distribution EXACTLY. Never exceed limits. Match answer lengths precisely. Output ONLY valid JSON. No duplicated questions."""

def _validate_exam_quality(questions: List[Dict[str, Any]], difficulty: str, target_language: str = "english") -> tuple[List[Dict[str, Any]], bool]:
    """
    Auto-check exam quality based on strict marks-based rules.
    Validates answer structure, length, LaTeX formatting, required elements, format variation, and language.
    Returns (validated_questions_list, has_format_repetition: bool)
    """
    validated_questions = []
    has_repetition = False
    has_hard_mode_violation = False  # Track hard mode violations
    
    # Track question formats for variation check
    question_starters = []
    question_structures = []
    question_phrases = []  # Track full question phrasing patterns
    
    # Import language detection function
    from app.font_manager import detect_language
    
    # Track language violations
    language_violations = []
    
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
        
        # Rule 1: Marks-based line count validation (LENIENT - quality-first approach)
        if marks == 10:
            # Accept 7+ lines (more lenient for quality-first approach)
            if answer_lines < 7:
                # Only mark as invalid if very short (< 7 lines)
                is_valid = False
                issues.append(f"10-mark answer should have at least 7 lines, got {answer_lines}. Very short answers may need more detail.")
            elif answer_lines < 10:
                # 7-9 lines: Accept but log as warning (quality-first approach)
                print(f"⚠️  10-mark answer has {answer_lines} lines (target: 10-15). Accepting for quality-first approach.")
                # Don't mark as invalid - accept it
            
            # Check for mandatory parts (STRICT - all must be present)
            # For structured format, check dictionary keys directly
            if isinstance(answer, dict):
                has_given = "given" in answer and answer.get("given")
                has_definition = "definition" in answer and answer.get("definition")
                has_formula = "formula" in answer and answer.get("formula") and str(answer.get("formula")).strip() != ""
                has_steps = "steps" in answer and isinstance(answer.get("steps"), list) and len(answer.get("steps", [])) > 0
                has_function_values = "function_values" in answer and isinstance(answer.get("function_values"), list) and len(answer.get("function_values", [])) > 0
                has_explanation = has_steps and len(answer.get("steps", [])) >= 3  # Multiple steps imply explanation
                has_conclusion = "final" in answer and answer.get("final")
            else:
                # For string format, check text content
                has_given = any(word in answer_lower for word in ["given", "கொடுக்கப்பட்டது", "दिया गया", "given:", "provided"])
                has_definition = any(word in answer_lower for word in ["definition", "define", "வரையறை", "परिभाषा"]) or any(word in answer_lower for word in ["concept", "term", "meaning"])
                has_formula = any(word in answer_lower for word in ["formula", "சூத்திரம்", "सूत्र", "formula:", "theorem", "theorem:"]) or "=" in answer_text or "D =" in answer_text
                has_steps = any(word in answer_lower for word in ["step", "படி", "चरण", "step 1", "step 2", "calculation"]) or any(char.isdigit() for char in answer_text.split('\n')[0] if len(answer_text.split('\n')) > 5)
                has_explanation = any(word in answer_lower for word in ["explain", "reasoning", "therefore", "hence", "thus", "because", "விளக்கம்", "व्याख्या"]) or answer_lines >= 8
                has_conclusion = any(word in answer_lower for word in ["conclusion", "final answer", "therefore", "thus", "hence", "முடிவு", "निष्कर्ष"]) or "final answer:" in answer_lower or "\\boxed" in answer_text or "boxed" in answer_lower
            
            missing_parts = []
            if not has_given:
                missing_parts.append("Given")
            if not has_definition and not has_formula:  # Definition OR formula (definition is optional if formula is present)
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
                # LENIENT: Only mark as invalid if critical parts are missing (Given and Formula/Steps)
                # For quality-first approach, accept if it has Given and some working
                critical_missing = [p for p in missing_parts if p in ["Given", "Formula/Theorem", "Step-by-step working"]]
                if critical_missing and len(critical_missing) >= 2:
                    # Missing 2+ critical parts - mark as invalid
                    is_valid = False
                    issues.append(f"10-mark answer missing critical parts: {', '.join(critical_missing)}. Must include: Given, Formula/Theorem, Step-by-step working.")
                else:
                    # Missing only non-critical parts - accept but log warning
                    print(f"⚠️  10-mark answer missing some parts: {', '.join(missing_parts)}. Accepting for quality-first approach.")
                    # Don't mark as invalid
            
            # Check for boxed answer
            if isinstance(answer, dict):
                final_answer = answer.get("final", "")
                has_boxed = "\\boxed" in str(final_answer) or "boxed" in str(final_answer).lower()
            else:
                has_boxed = "\\boxed" in answer_text or "boxed" in answer_lower
            
            # Check for final answer (either "Final Answer:" prefix or boxed format)
            # LENIENT: Accept if answer has conclusion or final statement
            has_final_answer = "final answer:" in answer_lower or "\\boxed" in answer_text or "boxed" in answer_lower
            has_conclusion_statement = any(word in answer_lower for word in ["conclusion", "therefore", "thus", "hence", "final", "answer", "முடிவு", "निष्कर्ष"])
            if not has_final_answer and not has_conclusion_statement:
                # Only mark as invalid if completely missing conclusion
                print(f"⚠️  10-mark answer missing explicit final answer. Accepting for quality-first approach.")
                # Don't mark as invalid - accept it
        
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
        
        # Log validation results (QUALITY-FIRST: Accept questions even with minor issues)
        if not is_valid:
            # For quality-first approach, accept questions with warnings instead of rejecting
            print(f"⚠️  Question validation warning (Marks: {marks}, Lines: {answer_lines}):")
            for issue in issues:
                print(f"   - {issue}")
            # Use answer_text for preview (works for both string and dict formats)
            preview = answer_text[:200] if answer_text and len(answer_text) > 200 else answer_text
            print(f"   Answer preview: {preview}...")
            print(f"   ✅ Accepting question anyway (quality-first approach - minor issues acceptable)")
            # Reset is_valid to True to accept the question
            is_valid = True
        else:
            print(f"✅ Question validated (Marks: {marks}, Lines: {answer_lines})")
        
        # Track question format for variation check
        question_text = q.get("question", "").strip()
        
        # LANGUAGE VALIDATION: Check if question is in the correct target language
        if question_text and target_language.lower() == "tamil":
            # Detect the language of the question
            detected_lang = detect_language(question_text, default_language="english")
            if detected_lang != "tamil":
                # Question is not in Tamil - log warning
                language_violations.append({
                    "question_num": idx + 1,
                    "question": question_text[:100],  # First 100 chars
                    "detected_lang": detected_lang,
                    "expected_lang": "tamil"
                })
                print(f"⚠️  LANGUAGE VIOLATION: Question {idx + 1} is in {detected_lang}, but Tamil was requested. Question: {question_text[:100]}")
                # Accept it anyway (quality-first approach), but log the issue
        
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
        print(f"🚨 CRITICAL: Detected {tamil_pattern_count} questions with repetitive Tamil pattern 'f(x) = ... என்றால், f(...) என்றால் என்ன?'")
        print(f"   This pattern MUST NOT be repeated. Each question must use a DIFFERENT format.")
        return validated_questions, True  # Return True to trigger regeneration
    
    # Check for phrase pattern repetition (LENIENT - quality-first approach)
    # For small question sets (≤5), be more lenient - only flag if 4+ questions share same phrase
    # For larger sets, flag if 3+ questions share same phrase (more lenient)
    min_repetition_count = 4 if len(validated_questions) <= 5 else 3
    
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
            print(f"🚨 CRITICAL WARNING: Found {len(repeated_starters)} question opener(s) repeated across the set. Each question MUST have a UNIQUE opener!")
        elif consecutive_same > 0:
            print(f"⚠️  WARNING: Found {consecutive_same} consecutive question(s) with same opener. Questions should vary in format/phrasing.")
    
    # Check for structure repetition (LENIENT - quality-first approach)
    # For small question sets (≤5), only flag if 5+ questions share same structure
    # For larger sets, flag if 4+ questions share same structure (more lenient)
    min_structure_repetition = 5 if len(validated_questions) <= 5 else 4
    
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
        
        # Check consecutive repetition (LENIENT - only flag if 3+ consecutive)
        consecutive_same_structure = 0
        consecutive_count = 1
        for i in range(1, len(question_structures)):
            if question_structures[i] == question_structures[i-1]:
                consecutive_count += 1
                if consecutive_count >= 3:  # Only flag if 3+ consecutive
                    consecutive_same_structure += 1
                    print(f"⚠️  CONSECUTIVE STRUCTURE REPETITION: Questions {i-1}, {i}, and {i+1} use '{question_structures[i]}' structure")
                    has_repetition = True
            else:
                consecutive_count = 1
        
        if repeated_structures:
            print(f"🚨 CRITICAL WARNING: Found {len(repeated_structures)} question structure(s) repeated across the set. Each question MUST have a UNIQUE structure!")
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
    
    # QUALITY-FIRST: Accept all questions, no retries
    # Even if hard mode violations or format repetition detected, accept questions
    if has_hard_mode_violation:
        print(f"⚠️  HARD MODE VIOLATIONS DETECTED - Accepting questions anyway (quality-first approach)")
    
    if has_repetition:
        print(f"⚠️  FORMAT REPETITION DETECTED - Accepting questions anyway (quality-first approach)")
    
    # Report language violations if any
    if language_violations:
        print(f"⚠️  LANGUAGE VIOLATIONS DETECTED: {len(language_violations)} question(s) are not in the target language ({target_language})")
        for violation in language_violations:
            print(f"   - Question {violation['question_num']}: Detected as {violation['detected_lang']}, expected {violation['expected_lang']}")
            print(f"     Preview: {violation['question'][:80]}...")
        print(f"   ⚠️  All questions should be in {target_language}. Please regenerate with correct language.")
    
    # Never trigger regeneration - accept what we have
    return validated_questions, False  # Return False to prevent retries

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

    is_single_image: bool = False  # Flag for single image uploads (mobile)

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
    
    # Filter out items with count 0 (they won't be used anyway)
    distribution_list = [item for item in distribution_list if item.get("count", 0) > 0]
    
    if len(distribution_list) == 0:
        raise ValueError("distribution_list cannot be empty after filtering (all items have count 0)")
    
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
    
    # SPECIAL HANDLING: Single image uploads (mobile) - EXACTLY 5 MCQs + 1 five-mark (NO ten-mark)
    if is_single_image:
        print("📸 Single image upload detected - using fixed distribution: 5 MCQs + 1 five-mark")
        distribution_list = [
            {"marks": 1, "count": 5, "type": "mcq"},
            {"marks": 5, "count": 1, "type": "descriptive"}
        ]
        num_questions = 6  # Override to 6 total
        print(f"✅ Overridden distribution for single image: {distribution_list}")
    
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

🚨 CRITICAL: This is MATHEMATICS - Follow these rules STRICTLY:

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

5. SUBJECT-SPECIFIC STRICT RULE (MATHEMATICS):
   🚨 CRITICAL: For numerical problems, you MUST compute the final answer
   🚨 CRITICAL: Listing given values alone is NOT an answer
   🚨 CRITICAL: Show necessary steps suitable for the given marks
   🚨 CRITICAL: Never stop at "Given:" statements - always proceed to calculation and final answer
   
   📐 FOR LCM/HCF (GCD) QUESTIONS - MANDATORY REQUIREMENTS:
   ✅ ALWAYS provide ALL of the following:
      1) Method: Explain the method used (Prime Factorization, Division Method, etc.)
      2) HCF value: Calculate and state the HCF (Highest Common Factor/GCD)
      3) LCM value: Calculate and state the LCM (Least Common Multiple)
   ✅ Show complete working with all steps
   ✅ Never leave the answer incomplete - always provide both HCF and LCM values
   ✅ Example structure for LCM/HCF questions:
      - Given: Numbers (e.g., 24 and 36)
      - Method: Prime Factorization Method (or Division Method)
      - Calculation/Steps: Show step-by-step working
      - Final Answer: HCF = [value], LCM = [value]
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
    
<<<<<<< HEAD
    # Define newline character to avoid backslash in f-string expressions
    nl = '\n'
    
    # Extract large conditional strings to avoid backslashes in f-string expressions
    math_formatting_rules = """[CRITICAL] USE EXAM-FRIENDLY STUDENT-WRITTEN NOTATION. NO LaTeX COMMANDS. [CRITICAL]

STRICT RULES FOR 10-MARK ANSWERS:
1. Use ONLY exam-friendly mathematical notation (NO LaTeX commands like \\frac, \\sqrt, \\times, \\boxed)
2. Use simple symbols written normally: +, -, x, /, sqrt
3. Write exactly as a student would write in an exam for 10 marks
4. Structure the answer clearly under these headings:
   - Given
   - Formula
   - Calculation / Steps
   - Nature of roots (if applicable)
   - Final Answer
5. Show every intermediate step clearly
6. Do NOT skip substitution steps
7. The final answer must be fully numerical and clearly stated"""
    
    other_subject_formatting = f"""For {detected_subject.upper()} subjects:
- Follow the subject-specific answer structure as specified above
- Use appropriate terminology and formatting for the subject
- Write in exam-appropriate style for {detected_subject}""" if detected_subject != "mathematics" else ""
    
    exam_friendly_examples = """EXAM-FRIENDLY NOTATION EXAMPLES (MATHEMATICS ONLY):
   [X] LaTeX: \\( \\frac{{a}}{{b}} \\) -> [OK] Exam: a/b or (a)/(b)
   [X] LaTeX: \\( \\sqrt{{x}} \\) -> [OK] Exam: sqrt(x) or sqrt(x)
   [X] LaTeX: \\( x^2 \\) -> [OK] Exam: x^2 or x^2
   [X] LaTeX: \\( \\times \\) -> [OK] Exam: x
   [X] LaTeX: \\( \\boxed{{x = 5}} \\) -> [OK] Exam: [x = 5] or Final Answer: x = 5
   [X] LaTeX: \\( D = b^2 - 4ac \\) -> [OK] Exam: D = b^2 - 4ac or D = b^2 - 4ac

FOR 1-5 MARK QUESTIONS (MATHEMATICS):
- Can use simple notation: x = 5, f(x) = 2x^2 + 3x + 1
- Fractions: a/b or (a)/(b)
- Powers: x^2 or x^2
- Roots: sqrt(x) or sqrt(x)

FOR 10-MARK QUESTIONS (MATHEMATICS - STRICT EXAM FORMAT):
- MUST use student-written notation (NO LaTeX)
- MUST have clear headings: Given, Formula, Calculation/Steps, Nature of roots, Final Answer
- MUST show every step with substitution
- Example format:
  Given: f(x) = 3x^3 - 6x^2 + 2
  
  Formula: 
  First derivative: f'(x) = 9x^2 - 12x
  Second derivative: f''(x) = 18x - 12
  
  Calculation / Steps:
  Step 1: f'(x) = 9x^2 - 12x
  Step 2: Set f'(x) = 0
          9x^2 - 12x = 0
          x(9x - 12) = 0
          x = 0 or x = 12/9 = 4/3
  Step 3: f''(x) = 18x - 12
  Step 4: f''(0) = 18(0) - 12 = -12 < 0 (local maximum)
          f''(4/3) = 18(4/3) - 12 = 24 - 12 = 12 > 0 (local minimum)
  
  Function Values:
  f(0) = 3(0)^3 - 6(0)^2 + 2 = 2
  f(4/3) = 3(4/3)^3 - 6(4/3)^2 + 2 = -14/9
  
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
   - MUST have clear final answer (NO boxed, use "Final Answer:" heading)"""
    
    math_variation_text = """
- Variation 1: Direct calculation
- Variation 2: Word problem
- Variation 3: Proof/derivation
- Variation 4: Application
- Variation 5: Comparison
- Variation 6: Analysis (e.g., nature of roots)
- Variation 7+: Continue with NEW variations, NEVER reuse
"""
    
    other_variation_text = """
- Variation 1: Definition-based questions
- Variation 2: Explanation-based questions
- Variation 3: Analysis-based questions
- Variation 4: Comparison-based questions
- Variation 5: Application-based questions
- Variation 6: Context-based questions
- Variation 7+: Continue with NEW variations, NEVER reuse
"""
    
    # Extract JSON example strings to avoid backslashes in f-string expressions
    json_example_math = ('{' + nl + '  "questions": [' + nl + '    {' + nl + '      "marks": 5,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "medium",' + nl + '      "question": "Given the function f(x) = 2x^2 + 3x + 1, find the roots using the quadratic formula.",' + nl + '      "correct_answer": {' + nl + '        "given": "f(x) = 2x^2 + 3x + 1",' + nl + '        "formula": "x = (-b ± sqrt(b^2 - 4ac)) / (2a), where D = b^2 - 4ac",' + nl + '        "coefficients": "a = 2, b = 3, c = 1",' + nl + '        "steps": [' + nl + '          "D = b^2 - 4ac = 3^2 - 4(2)(1) = 9 - 8 = 1",' + nl + '          "x = (-3 ± sqrt(1)) / 4 = (-3 ± 1) / 4",' + nl + '          "x = (-3 + 1) / 4 = -1/2 and x = (-3 - 1) / 4 = -1"' + nl + '        ],' + nl + '        "final": "Final Answer: x = -1/2, -1"' + nl + '      }' + nl + '    },' + nl + '    {' + nl + '      "marks": 10,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "hard",' + nl + '      "question": "Analyze the function f(x) = 3x^3 - 6x^2 + 2. Find the critical points and determine their nature.",' + nl + '      "correct_answer": {' + nl + '        "given": "f(x) = 3x^3 - 6x^2 + 2",' + nl + '        "definition": "Critical points occur where the first derivative is zero or undefined.",' + nl + '        "formula": "First derivative: f\'(x) = 9x^2 - 12x' + nl + 'Second derivative: f\'\'(x) = 18x - 12",' + nl + '        "steps": [' + nl + '          "Step 1: Calculate first derivative: f\'(x) = 9x^2 - 12x",' + nl + '          "Step 2: Set first derivative to zero: f\'(x) = 9x^2 - 12x = 0",' + nl + '          "Step 3: Factor the equation: x(9x - 12) = 0",' + nl + '          "Step 4: Find critical points: x = 0 or x = 12/9 = 4/3",' + nl + '          "Step 5: Calculate second derivative: f\'\'(x) = 18x - 12",' + nl + '          "Step 6: Apply second derivative test: f\'\'(0) = -12 < 0 (local maximum), f\'\'(4/3) = 12 > 0 (local minimum)"' + nl + '        ],' + nl + '        "function_values": [' + nl + '          "f(0) = 3(0)^3 - 6(0)^2 + 2 = 2",' + nl + '          "f(4/3) = 3(4/3)^3 - 6(4/3)^2 + 2 = -14/9"' + nl + '        ],' + nl + '        "final": "Final Answer: Local maximum at (0, 2), Local minimum at (4/3, -14/9)"' + nl + '      }' + nl + '    },' + nl)
    
    json_example_other = ('{' + nl + '  "questions": [' + nl + '    {' + nl + '      "marks": 3,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "medium",' + nl + '      "question": "Describe the main character\'s development in the story.",' + nl + '      "correct_answer": "The main character undergoes significant growth throughout the narrative. Initially, they are portrayed as naive and inexperienced. As the story progresses, they face various challenges that test their resolve. These experiences shape their personality and worldview. By the end, they emerge as a more mature and understanding individual."' + nl + '    },' + nl + '    {' + nl + '      "marks": 5,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "medium",' + nl + '      "question": "Explain the theme of the poem and analyze its literary devices.",' + nl + '      "correct_answer": {' + nl + '        "introduction": "The poem explores themes of nature and human connection, using vivid imagery to create emotional resonance.",' + nl + '        "explanation": "The poet uses vivid imagery to depict natural scenes, creating a sense of harmony between humans and the environment. The language choices emphasize the interconnectedness of all living things.",' + nl + '        "analysis": "Literary devices such as metaphor and personification enhance the emotional impact. The metaphor of nature as a teacher allows readers to connect deeply with the poet\'s message about learning from the natural world.",' + nl + '        "conclusion": "The poem effectively conveys the relationship between humans and nature through its masterful use of language and imagery, leaving readers with a profound appreciation for the natural world."' + nl + '      }' + nl + '    },' + nl + '    {' + nl + '      "marks": 10,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "hard",' + nl + '      "question": "Comprehensively analyze the historical significance of the event and its impact.",' + nl + '      "correct_answer": {' + nl + '        "background": "The event occurred during a period of significant change in society, marking a transition from traditional to modern approaches.",' + nl + '        "key_points": ["First, the event marked a turning point in political structures", "Second, it influenced subsequent economic developments", "Third, it changed social relationships and cultural norms"],' + nl + '        "explanation": "The event\'s significance lies in its transformative nature. It challenged existing power structures and created new opportunities for different social groups. The immediate consequences were felt across multiple sectors of society.",' + nl + '        "conclusion": "The event had lasting impact on society, shaping the course of history for generations to come. Its legacy continues to influence contemporary discussions and policies."' + nl + '      }' + nl + '    },' + nl)
    
    json_example_general = ('{' + nl + '  "questions": [' + nl + '    {' + nl + '      "marks": 5,' + nl + '      "type": "descriptive",' + nl + '      "difficulty": "medium",' + nl + '      "question": "Explain the concept and provide examples.",' + nl + '      "correct_answer": "Definition: The concept is defined as... Explanation: It involves several key aspects... Example: For instance... Conclusion: In summary..."' + nl + '    },' + nl)
    
    # Special instructions for single image uploads
    single_image_instructions = ""
    if is_single_image:
        single_image_instructions = f"""
━━━━━━━━━━━━━━━━━━━━━━
🚨 SINGLE IMAGE UPLOAD - STRICT RULES 🚨
━━━━━━━━━━━━━━━━━━━━━━

⚠️ CRITICAL: The input is a SINGLE IMAGE only (uploaded from mobile).
⚠️ The image contains LIMITED educational content.

STRICT RULES FOR SINGLE IMAGE UPLOADS:

1. EXACT DISTRIBUTION (MANDATORY):
   ✅ Generate EXACTLY:
      - 5 multiple choice questions (MCQs) - 1 mark each
      - 1 five-mark descriptive question
   ❌ DO NOT generate any ten-mark questions
   ❌ DO NOT generate more or fewer questions

2. NO HALLUCINATION (ABSOLUTELY MANDATORY):
   ❌ DO NOT invent topics that are NOT present in the image
   ❌ DO NOT add information beyond what is clearly visible
   ❌ DO NOT create questions about concepts not shown in the image
   ✅ Base questions ONLY on what is clearly present in the image
   ✅ If content is insufficient, keep questions simple and factual

3. CONTENT-BASED GENERATION:
   ✅ Generate questions based ONLY on visible text, diagrams, or content
   ✅ If the image has limited content, generate simpler questions
   ✅ Focus on what is actually shown, not what could be inferred
   ✅ Keep questions factual and directly related to visible content

4. QUALITY OVER QUANTITY:
   ✅ If content is insufficient for 5 MCQs + 1 five-mark, generate fewer but accurate questions
   ✅ Better to generate 3-4 good questions than 6 forced/invented questions
   ✅ Each question must be answerable from the visible content

━━━━━━━━━━━━━━━━━━━━━━
"""

=======
    # Calculate dynamic content limit based on number of parts
    # Base limit: 60,000 characters per part (40 pages) - increased to use more content
    # For multi-part selections, increase limit proportionally to use more content
    # Supports up to 7-8 parts for comprehensive question generation
    # Calculate total content length first to determine optimal limit
    total_content_length_preview = len(text_content)
    
    if num_parts and num_parts > 1:
        # Dynamic content limit: Automatically adjust based on actual content size
        # Token budget: ~128,000 tokens max
        # The prompt is VERY long (~120-127k tokens with all rules), leaving very little room
        # We need to be very conservative with content limits
        # Roughly 1 token = 4 characters for English, but Tamil/other languages may use more tokens
        # For safety, assume 1 token = 3.5 chars (more conservative for non-English)
        # With prompt using ~127k tokens, we have ~1k tokens left = ~3.5k chars max
        # But we need room for completion tokens, so we need to reduce content significantly
        # Strategy: Reduce content limits to ensure prompt + content + completion < 128k
        
        # More conservative limits that account for the large prompt
        # Estimate: prompt uses ~127k tokens, we need ~5-10k for completion
        # So content should use at most ~1-3k tokens = ~3.5-10k chars
        # But this is too restrictive. The real issue is the prompt is too long.
        # Better approach: Use more conservative limits that leave room
        
        # Base limits per part count (reduced significantly to account for large prompt)
        base_limits = {
            2: 80000,    # 80k for 2 parts (~23k tokens)
            3: 100000,   # 100k for 3 parts (~29k tokens) - reduced from 200k
            4: 120000,   # 120k for 4 parts (~34k tokens) - reduced from 220k
            5: 140000,   # 140k for 5 parts (~40k tokens) - reduced from 240k
            6: 160000,   # 160k for 6 parts (~46k tokens) - reduced from 260k
            7: 180000,   # 180k for 7 parts (~51k tokens) - reduced from 270k
            8: 200000    # 200k for 8 parts (~57k tokens) - reduced from 280k
        }
        
        # Get base limit for number of parts
        if num_parts <= 8:
            content_limit = base_limits.get(num_parts, 100000)
        else:
            content_limit = 200000  # Max safe limit
        
        # If total content is smaller than limit, use all of it
        if total_content_length_preview < content_limit:
            content_limit = total_content_length_preview
            print(f"📊 Content is smaller than limit - using all {content_limit:,} characters")
        
        # Final safety cap - be very conservative to avoid exceeding token limit
        # With prompt at ~127k tokens, we need to keep content very small
        content_limit = min(content_limit, 200000)
    else:
        # Single part: use 60,000 characters
        content_limit = min(60000, total_content_length_preview)
    
    # Log content limit for debugging
    total_content_length = len(text_content)
    
    # Smart content coverage: Preserve part boundaries and sample from each part
    # This ensures questions come from the actual selected parts, not arbitrary sections
    if total_content_length > content_limit:
        # Strategy: If content has part markers (--- Part X (Pages Y-Z) ---), sample from each part
        # Otherwise, use evenly-spaced windows but preserve structure
        part_markers = []
        if "--- Part " in text_content:
            # Content has part markers - extract and preserve them
            import re
            # Find all part markers and their positions
            for match in re.finditer(r'--- Part (\d+) \(Pages (\d+)-(\d+)\) ---', text_content):
                part_num = int(match.group(1))
                start_page = int(match.group(2))
                end_page = int(match.group(3))
                part_markers.append({
                    'part_number': part_num,
                    'start_page': start_page,
                    'end_page': end_page,
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
        
        if part_markers and len(part_markers) > 0:
            # Sample from each part proportionally
            chars_per_part = content_limit // len(part_markers)
            sampled_parts = []
            
            for i, marker in enumerate(part_markers):
                # Find the start of this part's content (after the marker)
                part_start = marker['end_pos']
                # Find the start of the next part (or end of text)
                if i + 1 < len(part_markers):
                    part_end = part_markers[i + 1]['start_pos']
                else:
                    part_end = len(text_content)
                
                part_content = text_content[part_start:part_end]
                part_length = len(part_content)
                
                if part_length > chars_per_part:
                    # Sample from beginning, middle, and end of this part
                    sample_size = chars_per_part // 3
                    beginning = part_content[:sample_size]
                    middle_start = part_length // 2 - sample_size // 2
                    middle = part_content[middle_start:middle_start + sample_size]
                    end = part_content[-sample_size:]
                    
                    sampled_part = f"\n\n--- Part {marker['part_number']} (Pages {marker['start_page']}-{marker['end_page']}) ---\n\n"
                    sampled_part += beginning + "\n\n[... middle section ...]\n\n" + middle + "\n\n[... end section ...]\n\n" + end
                    sampled_parts.append(sampled_part)
                else:
                    # Use entire part if it fits
                    sampled_parts.append(text_content[marker['start_pos']:part_end])
            
            text_content = "".join(sampled_parts)
            content_used = len(text_content)
            print(f"Content extraction: Total={total_content_length} chars, Using={content_used} chars (sampled from {len(part_markers)} parts preserving part boundaries), Parts={num_parts or 1}")
        else:
            # No part markers - use evenly-spaced windows
            num_windows = min(5, num_parts or 3)
            marker_overhead = num_windows * 30
            available_for_content = content_limit - marker_overhead
            window_size = available_for_content // num_windows
            
            windows = []
            for i in range(num_windows):
                if num_windows == 1:
                    start_pos = 0
                else:
                    start_pos = int((i / (num_windows - 1)) * (total_content_length - window_size))
                
                end_pos = min(start_pos + window_size, total_content_length)
                window_content = text_content[start_pos:end_pos]
                
                if window_content.strip():
                    section_label = f"[Section {i+1} of {num_windows} - covering different pages]"
                    windows.append(f"\n\n{section_label}\n{window_content}")
            
            text_content = "".join(windows)
            content_used = len(text_content)
            print(f"Content extraction: Total={total_content_length} chars, Using={content_used} chars (sampled from {num_windows} evenly-spaced sections), Parts={num_parts or 1}")
    else:
        content_used = total_content_length
        print(f"Content extraction: Using all {content_used:,} chars (within limit)")
    
    # Estimate pages (assuming ~2000 chars per page on average)
    num_pages_estimate = max(1, int(total_content_length / 2000))
    questions_per_page = num_questions / max(1, num_pages_estimate) if num_pages_estimate > 0 else num_questions
    
    print(f"Content extraction: Total={total_content_length} chars, Using={content_used} chars (limit={content_limit}), Parts={num_parts or 1}, Pages~{num_pages_estimate}, Questions/page~{questions_per_page:.1f}")
    
    # Check if content is grammar-focused (but also check for stories/poems)
    grammar_keywords_check = ['grammar', 'noun', 'verb', 'tense', 'sentence', 'subject-verb', 'parts of speech']
    literature_keywords_check = ['poem', 'poetry', 'story', 'character', 'narrator', 'plot', 'theme', 'author', 'poet', 'stanza', 'verse']
    
    has_grammar_keywords = any(keyword in text_content.lower() for keyword in grammar_keywords_check)
    has_literature_keywords = any(keyword in text_content.lower() for keyword in literature_keywords_check)
    
    # Check for mixed content (both grammar and literature)
    has_mixed_content = detected_subject == "english" and has_grammar_keywords and has_literature_keywords
    
    # Only enforce grammar-only if content has grammar keywords BUT NO literature keywords
    is_grammar_content = detected_subject == "english" and has_grammar_keywords and not has_literature_keywords
    
    if is_grammar_content:
        print(f"⚠️  PURE GRAMMAR CONTENT DETECTED - Enforcing grammar-only question generation")
    elif has_mixed_content:
        print(f"📚 MIXED CONTENT DETECTED (stories/poems/prose + grammar) - Generate questions from ALL content types present in PDF")
        print(f"   ✅ Content contains: Stories/Poems/Prose AND Grammar (vocabulary, verbs, etc.)")
        print(f"   ✅ AI must read sentence by sentence and generate questions from whatever is actually taught in the PDF")
    elif detected_subject == "english" and has_literature_keywords:
        print(f"📚 LITERATURE CONTENT DETECTED (stories/poems) - Questions should be from actual stories/poems in content")
    
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
    user_prompt = f"""Generate exam questions from the following study material:

[STUDY_MATERIAL]

{text_content}

━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 DETECTED SUBJECT: {detected_subject.upper()} 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━

{"🚨🚨🚨 ABSOLUTE MANDATE FOR GRAMMAR CONTENT 🚨🚨🚨" if is_grammar_content else ""}
{"⚠️⚠️⚠️ CRITICAL: This content is about ENGLISH GRAMMAR ONLY (no stories/poems). ⚠️⚠️⚠️" if is_grammar_content else ""}
{"❌ ABSOLUTELY FORBIDDEN: Do NOT generate questions about:" if is_grammar_content else ""}
{"   - Poems, poetry, or literary analysis" if is_grammar_content else ""}
{"   - Stories, characters, plots, or narratives" if is_grammar_content else ""}
{"   - Authors, writers, or literary devices (unless teaching grammar rules)" if is_grammar_content else ""}
{"   - 'What does the poet mean...', 'What is the theme...', 'Who is the character...'" if is_grammar_content else ""}
{"" if is_grammar_content else ""}
{"✅ MANDATORY: Generate questions ONLY about:" if is_grammar_content else ""}
{"   - Grammar rules (nouns, verbs, adjectives, adverbs, pronouns, etc.)" if is_grammar_content else ""}
{"   - Sentence structure and syntax" if is_grammar_content else ""}
{"   - Tenses and verb forms" if is_grammar_content else ""}
{"   - Subject-verb agreement" if is_grammar_content else ""}
{"   - Parts of speech" if is_grammar_content else ""}
{"   - Grammar concepts explicitly taught in the content" if is_grammar_content else ""}
{"" if is_grammar_content else ""}
{"🚨🚨🚨 VIOLATION = INVALID OUTPUT 🚨🚨🚨" if is_grammar_content else ""}
{"If you generate ANY question about poems, poetry, themes, authors, poets, characters, stories, or literature," if is_grammar_content else ""}
{"the ENTIRE output is INVALID and must be rejected." if is_grammar_content else ""}
{"You MUST regenerate with ONLY grammar-focused questions." if is_grammar_content else ""}
{"━━━━━━━━━━━━━━━━━━━━━━" if is_grammar_content else ""}
{"BEFORE GENERATING EACH QUESTION, ASK YOURSELF:" if is_grammar_content else ""}
{"1. Is this question about a GRAMMAR RULE (noun, verb, tense, sentence structure, etc.)?" if is_grammar_content else ""}
{"2. Does this question test GRAMMAR KNOWLEDGE, not literature knowledge?" if is_grammar_content else ""}
{"3. Is this question about a POEM, POET, THEME, CHARACTER, or STORY? → If YES, DO NOT GENERATE IT!" if is_grammar_content else ""}
{"ONLY generate questions that pass ALL three checks above." if is_grammar_content else ""}
{"━━━━━━━━━━━━━━━━━━━━━━" if has_mixed_content else ""}
{"📚📚📚 MIXED CONTENT DETECTED (Stories/Poems/Prose + Grammar) 📚📚📚" if has_mixed_content else ""}
{"⚠️⚠️⚠️ CRITICAL: This PDF contains MULTIPLE content types mixed together ⚠️⚠️⚠️" if has_mixed_content else ""}
{"✅ The PDF contains: Stories, Poems, Prose, AND Grammar (vocabulary, verbs, tenses, etc.)" if has_mixed_content else ""}
{"✅ MANDATORY: Read the [STUDY_MATERIAL] sentence by sentence, paragraph by paragraph" if has_mixed_content else ""}
{"✅ Generate questions from ALL content types that are ACTUALLY present in the PDF:" if has_mixed_content else ""}
{"   - If a story is in the PDF → Generate questions about characters, events, plots from that story" if has_mixed_content else ""}
{"   - If a poem is in the PDF → Generate questions about themes, meanings, literary devices from that poem" if has_mixed_content else ""}
{"   - If grammar rules are taught in the PDF → Generate questions about those grammar rules (vocabulary, verbs, tenses, etc.)" if has_mixed_content else ""}
{"   - If prose is in the PDF → Generate questions about the content, themes, and concepts from that prose" if has_mixed_content else ""}
{"🚨🚨🚨 CRITICAL RULE: Generate questions ONLY from what is ACTUALLY written in the [STUDY_MATERIAL] 🚨🚨🚨" if has_mixed_content else ""}
{"❌ DO NOT use general knowledge - use ONLY what is written in the [STUDY_MATERIAL]" if has_mixed_content else ""}
{"❌ DO NOT generate questions about grammar if grammar is NOT taught in the PDF" if has_mixed_content else ""}
{"❌ DO NOT generate questions about stories if stories are NOT in the PDF" if has_mixed_content else ""}
{"✅ Read each sentence carefully and generate questions from whatever content type appears in that sentence" if has_mixed_content else ""}
{"━━━━━━━━━━━━━━━━━━━━━━" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"📚📚📚 LITERATURE CONTENT DETECTED (Stories/Poems Present) 📚📚📚" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"⚠️⚠️⚠️ CRITICAL: This content contains STORIES and POEMS. ⚠️⚠️⚠️" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"✅ MANDATORY: Generate questions from the ACTUAL stories and poems in the [STUDY_MATERIAL] above" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"✅ Read the content sentence by sentence and generate questions about:" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"   - Characters, events, and plots from the stories" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"   - Themes, meanings, and literary devices in the poems" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"   - What the poet/author says, what characters do, what happens in the stories" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}
{"❌ DO NOT use general knowledge - use ONLY what is written in the [STUDY_MATERIAL]" if detected_subject == "english" and has_literature_keywords and not is_grammar_content and not has_mixed_content else ""}

━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CONTENT GROUNDING RULES (MANDATORY - TEACHER'S MIND) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━

ABSOLUTE REQUIREMENT: Think and act like a REAL TEACHER examining study material.

🚨🚨🚨 CRITICAL: You MUST read the [STUDY_MATERIAL] above sentence by sentence, like a teacher reading a textbook 🚨🚨🚨
- You are reading ACTUAL CONTENT from a PDF/book that was uploaded
- Every question MUST come from what is EXPLICITLY written in that material
- Read the content CAREFULLY, sentence by sentence, paragraph by paragraph, line by line
- The PDF may contain MULTIPLE content types mixed together:
  * STORIES: Identify characters, events, plots, themes from those stories
  * POEMS: Identify themes, meanings, literary devices, what the poet says
  * PROSE: Identify content, themes, concepts from that prose
  * GRAMMAR RULES: Identify vocabulary, verbs, tenses, grammar concepts that are taught
- Generate questions from ALL content types that are ACTUALLY present in the PDF
- 🚨🚨🚨 CRITICAL: Generate questions from DIFFERENT topics/sections/PAGES of the PDF 🚨🚨🚨
- 🚨🚨🚨 DO NOT generate all questions from the same page - spread questions across DIFFERENT pages/sections 🚨🚨🚨
- 🚨🚨🚨 CRITICAL: Read through the ENTIRE content (beginning, middle, end) and generate questions from DIFFERENT pages/sections 🚨🚨🚨
- 🚨🚨🚨 CRITICAL: When providing source_hint, reference DIFFERENT page numbers/sections - don't use the same page for all questions 🚨🚨🚨
- 🚨🚨🚨 CRITICAL: If content has part markers (--- Part X (Pages Y-Z) ---), source_hint MUST include the actual Part number and page range 🚨🚨🚨
  * Example: If question is from "--- Part 1 (Pages 1-40) ---", source_hint should be "Part 1 (Page 3)" or "Part 1: Pages 1-40, Section on World War I"
  * Example: If question is from "--- Part 2 (Pages 41-80) ---", source_hint should be "Part 2 (Page 45)" or "Part 2: Pages 41-80, Section on Russian Revolution"
  * NEVER use generic page numbers - use the ACTUAL part number and page from the content markers
- If grammar is taught in the PDF (vocabulary, verbs, tenses, etc.), generate grammar questions from those sections
- If stories are in the PDF, generate story questions from those sections
- If poems are in the PDF, generate poem questions from those sections
- If mathematics topics are in the PDF, generate questions from DIFFERENT topics (not all from the same topic)
- If social science topics are in the PDF, generate questions from DIFFERENT topics (not all from the same topic like World War I)
- Generate questions ONLY from what you can SEE and POINT TO in the content
- For each question, you MUST be able to say: "This question is from [specific section/paragraph/page] which contains [specific content]"
- If you cannot point to where in the content this information appears, DO NOT generate that question
- DO NOT use general knowledge - use ONLY what is explicitly written in [STUDY_MATERIAL]
- Read like a teacher: sentence by sentence, identify what is being taught, and generate questions from that
- When providing "topic" and "source_hint", they MUST reference the ACTUAL content sections, not generic placeholders
- The "topic" should be the actual concept/character/theme/grammar rule from the content (e.g., "The Grumble Family", "Modal Verbs", "Character Zigzag", "Past Tense", "LCM and GCD", "World War II")
- The "source_hint" should reference where in the content this appears with DIFFERENT page numbers (e.g., "Story about Zigzag", "Poem 'The Grumble Family'", "Section on Modal Verbs", "Grammar section on Past Tense", "Chapter 6: LCM and GCD", "பக்கம் 45: World War II")
- Generic topics like "Which of the" or source hints like "From provided study material" indicate you are NOT reading the content
- 🚨🚨🚨 CRITICAL: With {total_content_length:,} chars (~{num_pages_estimate} pages), you have MANY different topics and pages - use DIFFERENT pages for different questions! 🚨🚨🚨

━━━━━━━━━━━━━━━━━━━━━━
RULE 1: CONTENT GROUNDING (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Use ONLY the content provided above in [STUDY_MATERIAL]
- Do NOT use outside knowledge, assumptions, or general facts
- Read the content line by line and sentence by sentence
- Generate questions ONLY when a concept, rule, definition, process, or explanation is clearly and explicitly stated
- Do NOT generate questions from examples alone unless the rule is explicitly explained

❌ STRICTLY FORBIDDEN:
- Generating questions from assumptions or general knowledge
- Using information not present in the provided content
- Creating questions from examples without explicit rules
- Inferring or guessing information not clearly stated

━━━━━━━━━━━━━━━━━━━━━━
RULE 2: TEACHER THINKING PROCESS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

You MUST follow this exact thinking process:

STEP 1: READ SENTENCE BY SENTENCE (Like a Teacher Reading a Textbook)
- Read the [STUDY_MATERIAL] sentence by sentence, paragraph by paragraph, like a teacher reading a textbook
- Identify what is ACTUALLY being taught in each section:
  * If a section teaches grammar (vocabulary, verbs, tenses, etc.) → This is grammar content
  * If a section contains a story → This is story content
  * If a section contains a poem → This is poem content
  * If a section contains prose → This is prose content
- The PDF may have ALL of these mixed together - that's normal and expected
- Read each sentence carefully and identify what content type it belongs to

STEP 2: IDENTIFY CORE CONCEPTS FROM EACH CONTENT TYPE
- For GRAMMAR sections: Identify vocabulary words, verb forms, tenses, grammar rules explicitly taught
- For STORY sections: Identify characters, events, plots, themes from those stories
- For POEM sections: Identify themes, meanings, literary devices, what the poet says
- For PROSE sections: Identify content, themes, concepts from that prose
- Core concepts may include (depending on content type):
  * Grammar: Definitions, rules, verb forms, tenses, vocabulary
  * Stories: Characters, events, plots, themes
  * Poems: Themes, meanings, literary devices, poet's message
  * Prose: Content, themes, concepts, explanations
- Each content type should generate questions from its own sections

STEP 3: QUESTION GENERATION
- Generate questions from ALL content types that are present in the PDF
- If grammar is taught in the PDF, generate grammar questions from those sections
- If stories are in the PDF, generate story questions from those sections
- If poems are in the PDF, generate poem questions from those sections
- Each question must map clearly to ONE specific concept/section from the content
- Do NOT repeat the same concept unnecessarily
- If a concept appears once, do NOT create another question testing the same concept
- Generate questions ONLY from what is explicitly written in the [STUDY_MATERIAL]

━━━━━━━━━━━━━━━━━━━━━━
RULE 3: NO-GUESSING RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- If an answer is NOT clearly found in the [STUDY_MATERIAL] above, do NOT guess, infer, or generalize
- In such cases, DO NOT generate that question
- Never produce confident but unsupported answers
- It is acceptable and expected to generate fewer questions if the content does not support more

❌ STRICTLY FORBIDDEN:
- Guessing answers not explicitly stated in the content
- Inferring information from context
- Using general knowledge to fill gaps
- Creating questions when the answer is not clearly in the content

━━━━━━━━━━━━━━━━━━━━━━
RULE 4: CONSISTENCY RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Do NOT generate multiple questions that test the same fact or concept in different wording
- Do NOT generate similar questions with different answers
- All answers must be internally consistent across the entire set
- Never contradict an earlier answer
- If entity X is mentioned, all questions about X must have consistent answers

━━━━━━━━━━━━━━━━━━━━━━
RULE 5: QUALITY RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Do NOT force questions to reach a target count
- If the content supports fewer high-quality questions, STOP gracefully
- Fewer accurate questions are better than many incorrect ones
- Quality over quantity - always prioritize accuracy

❌ STRICTLY FORBIDDEN:
- Generating questions just to meet a count
- Creating low-quality questions to fill a quota
- Repeating concepts to reach a number

━━━━━━━━━━━━━━━━━━━━━━
RULE 6: SUBJECT-AWARE BEHAVIOR (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

You MUST adapt your approach based on the subject:

- For LANGUAGE subjects (especially ENGLISH):
  * If the PDF contains ONLY grammar (no stories/poems):
     - 🚨 ALL questions MUST be about GRAMMAR RULES
     - ✅ Generate questions about grammar rules (nouns, verbs, adjectives, adverbs, pronouns, etc.)
     - ✅ Generate questions about sentence structure, syntax, tenses, verb forms, subject-verb agreement
     - ❌ DO NOT generate questions about poems, stories, or characters
  * If the PDF contains MIXED content (stories/poems + grammar):
     - ✅ Generate questions from ALL content types present in the PDF
     - ✅ If grammar is taught in the PDF (vocabulary, verbs, tenses, etc.), generate grammar questions from those sections
     - ✅ If stories are in the PDF, generate story questions from those sections
     - ✅ If poems are in the PDF, generate poem questions from those sections
     - ✅ Read sentence by sentence and generate questions from whatever content type appears in that section
     - ❌ DO NOT generate grammar questions if grammar is NOT taught in the PDF
     - ❌ DO NOT generate story questions if stories are NOT in the PDF
     - 🚨 CRITICAL: Generate questions ONLY from what is ACTUALLY written in the [STUDY_MATERIAL]
  * Focus on what is explicitly taught in each section
  * Generate questions ONLY when concepts/rules are explicitly stated
  * Read like a teacher: sentence by sentence, identify what is being taught, and generate questions from that

- For MATHEMATICS:
  * Generate questions ONLY when formulas, steps, or methods are clearly stated
  * Do NOT create questions from solved examples unless the method is explained
  * Focus on explicitly taught formulas and procedures
  * 🚨 CRITICAL: For numerical problems, you MUST compute the final answer
  * 🚨 CRITICAL: Listing given values alone is NOT an answer - always show calculation steps
  * 🚨 CRITICAL: For LCM/HCF (GCD) questions, ALWAYS provide:
     - Method (Prime Factorization, Division Method, etc.)
     - HCF value (calculated)
     - LCM value (calculated)
  * 🚨 CRITICAL: Never stop at "Given:" statements - always proceed to calculation and final answer

- For SCIENCE:
  * Focus on definitions, laws, processes, and explanations
  * Generate questions ONLY from explicitly stated scientific facts
  * Do NOT infer scientific principles not clearly stated

- For SOCIAL STUDIES:
  * Focus on explicitly stated facts, causes, effects, and explanations
  * Generate questions ONLY from clearly stated historical/geographical facts
  * Do NOT add background knowledge unless present in the text

- Never assume syllabus importance beyond what is stated in the content

━━━━━━━━━━━━━━━━━━━━━━
RULE 7: SOURCE FAITHFULNESS RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

✅ MANDATORY REQUIREMENTS:
- Treat the [STUDY_MATERIAL] above as the ONLY textbook
- Do NOT add background knowledge or real-world facts unless explicitly present in the text
- Each question must clearly originate from the given content
- Every answer must be directly traceable to a specific part of the provided content

❌ STRICTLY FORBIDDEN:
- Adding information from general knowledge
- Using facts not in the provided content
- Creating questions that require outside knowledge to answer
- Assuming information not explicitly stated

━━━━━━━━━━━━━━━━━━━━━━
TEACHER VERIFICATION CHECKLIST (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

Before generating ANY question, verify:
✓ Is this concept explicitly stated in the [STUDY_MATERIAL] above?
✓ Can I point to the EXACT sentence/paragraph/section where this information is found?
✓ Am I using ONLY information from the provided content?
✓ Is this question testing a DIFFERENT concept from previous questions?
✓ Is the answer clearly stated in the content (not inferred or guessed)?
✓ Would a real teacher generate this question from this content?
✓ Am I avoiding repetition of the same concept?
✓ Can I provide a SPECIFIC "topic" that names the actual concept from the content?
   * For Mathematics: Extract exact topic name (e.g., "Quadratic Equations", "Discriminant", "Roots")
   * For Literature: Extract story/poem/character name (e.g., "The Grumble Family", "Zigzag")
   * For Grammar: Extract grammar concept (e.g., "Modal Verbs", "Past Tense")
✓ Can I provide a SPECIFIC "source_hint" that references where in the content this appears?
   * For Mathematics: Reference exact chapter/section (e.g., "Chapter 2: Quadratic Equations")
   * For Literature: Reference story/poem (e.g., "Poem 'The Grumble Family'")
   * For Grammar: Reference section (e.g., "Section on Modal Verbs")

🚨🚨🚨 CRITICAL: If you cannot provide a SPECIFIC topic and source_hint that references the actual content, the question is INVALID. 🚨🚨🚨
🚨🚨🚨 MISSING topic OR source_hint = INVALID OUTPUT - You MUST regenerate with both fields included 🚨🚨🚨
🚨🚨🚨 Generic topic OR source_hint = INVALID OUTPUT - You MUST extract specific names from the content 🚨🚨🚨
🚨🚨🚨 For MATHEMATICS: Extract the EXACT topic name from the PDF (e.g., "Quadratic Equations", "Discriminant", "LCM and GCD") 🚨🚨🚨
🚨🚨🚨 For MATHEMATICS: Reference the EXACT chapter/section number from the PDF (e.g., "Chapter 2: Quadratic Equations", "Section 3.5: Discriminant", "Chapter 6: LCM and GCD") 🚨🚨🚨
🚨🚨🚨 If the PDF mentions "Chapter 6" or "Section 2.5", include that EXACT number in the source_hint 🚨🚨🚨
🚨🚨🚨 EVERY question MUST include BOTH "topic" and "source_hint" fields in the JSON - NO EXCEPTIONS 🚨🚨🚨

If ANY answer is NO, DO NOT generate that question.

━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES OF CORRECT TEACHER BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━

✅ CORRECT (Content-Grounded):
Content: "The quadratic formula is x = (-b ± √(b² - 4ac)) / 2a. This formula is used to solve quadratic equations."
Q1: "What is the quadratic formula?" → Answer: "x = (-b ± √(b² - 4ac)) / 2a"
(✓ Concept explicitly stated, answer directly from content)

✅ CORRECT (Quality Over Quantity):
Content: "A circle has radius r. The area is πr²."
Generated: 2 high-quality questions about radius and area
(✓ Stopped at 2 because content only supports these concepts, didn't force more)

❌ INCORRECT (Outside Knowledge):
Content: "A circle has radius r."
Q1: "What is the circumference of a circle?" → Answer: "2πr"
(✗ Formula not stated in content - DO NOT generate)

❌ INCORRECT (Guessing):
Content: "Zigzag is a character in the story."
Q1: "What is Zigzag?" → Answer: "A snake" (not explicitly stated)
(✗ Answer guessed, not clearly in content - DO NOT generate)

❌ INCORRECT (Repetition):
Q1: "What is the capital of India?" → Answer: "New Delhi"
Q2: "Name the capital city of India." → Answer: "New Delhi"
(✗ Same concept tested twice - FORBIDDEN)

━━━━━━━━━━━━━━━━━━━━━━
FINAL TEACHER MANDATE
━━━━━━━━━━━━━━━━━━━━━━

Think like a REAL TEACHER:
- A teacher reads the textbook carefully
- A teacher identifies what is EXPLICITLY taught
- A teacher creates questions ONLY from what is taught
- A teacher does NOT guess or assume
- A teacher prioritizes accuracy over quantity
- A teacher ensures consistency across all questions

If you cannot find explicit support in the [STUDY_MATERIAL] above, DO NOT generate that question.
Fewer accurate questions are ALWAYS better than many incorrect or unsupported questions.

━━━━━━━━━━━━━━━━━━━━━━
QUESTION GENERATION PARAMETERS
━━━━━━━━━━━━━━━━━━━━━━

{single_image_instructions}

Maximum Questions Allowed Per Upload: {remaining_questions}
Remaining Questions Allowed: {remaining_questions}

Question Distribution (Strict):
{distribution_string}

🎯 PREFERRED DISTRIBUTION BREAKDOWN - TARGET (not strict):
{chr(10).join([f"  • Target: {item.get('count', 0)} questions of {item.get('marks', 0)} marks (type: {item.get('type', 'descriptive')})" for item in distribution_list])}
🎯 TOTAL TARGET: {actual_num_questions} questions (sum of all above)
🎯 QUALITY-FIRST GENERATION PROCESS:
  1. Generate high-quality questions from the study material
  2. Try to match the distribution, but prioritize quality
  3. If content is sufficient, generate as close to {actual_num_questions} as possible
  4. If content is limited, generate fewer questions to maintain quality
  5. DO NOT force questions if the study material doesn't support them
  6. Verify each question is clearly worded and syllabus-relevant
  7. Output when you have generated the best possible questions from the content

{subject_instruction}

━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL: QUESTION COMPLEXITY REQUIREMENT 🚨
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

🚨 DETECTED SUBJECT: {detected_subject.upper()}

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

🚨🚨🚨 CRITICAL: STRICTLY FORBIDDEN - NO REPETITION OF QUESTION FORMATS OR FRAMES 🚨🚨🚨

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

━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CRITICAL CONSISTENCY RULE (ABSOLUTELY MANDATORY) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━

ABSOLUTE PROHIBITION - ZERO TOLERANCE FOR INCONSISTENCY:

1. ❌ DO NOT generate multiple questions that test the same fact or concept
   - If a concept appears once, do NOT repeat it in another question
   - Each question MUST test a DIFFERENT fact, concept, or piece of information
   - Example FORBIDDEN: 
     * Q1: "What is Zigzag?" → Answer: "A snake"
     * Q2: "What kind of bird is Zigzag?" → Answer: "A singing bird"
     (This is FORBIDDEN - Zigzag cannot be both a snake and a bird)

2. ❌ DO NOT provide conflicting answers for similar questions
   - All answers MUST be internally consistent across the entire question set
   - If Q1 says "X is Y", then Q2 cannot say "X is Z" (where Y ≠ Z)
   - Example FORBIDDEN:
     * Q4: "Which bird is described as Zigzag?" → Answer: "A snake" (CONTRADICTION - snake is not a bird)
     * Q5: "What kind of bird is Zigzag?" → Answer: "A singing bird"
     (This is FORBIDDEN - creates internal contradiction)

3. ❌ DO NOT test the same information in different ways
   - If you ask "What is X?" in one question, do NOT ask "Define X" or "Explain X" in another
   - Each question MUST cover a DIFFERENT aspect or DIFFERENT information
   - Rotate through DIFFERENT topics, characters, concepts, formulas, or facts
   - 🚨🚨🚨 CRITICAL: For mathematics, DO NOT generate multiple questions about the same topic (e.g., don't generate 8 questions all about quadratic equations) 🚨🚨🚨
   - 🚨🚨🚨 CRITICAL: Read through the PDF and identify DIFFERENT mathematics topics (Quadratic Equations, LCM/HCF, Linear Equations, Geometry, Trigonometry, Algebra, etc.) and generate questions from DIFFERENT topics 🚨🚨🚨
   - 🚨🚨🚨 CRITICAL: If you have 120+ pages of content, there are MANY different topics - use them! Don't repeat the same topic multiple times 🚨🚨🚨

4. ✅ MANDATORY CONSISTENCY REQUIREMENTS:
   - All answers must be factually consistent with the study material
   - All answers must be internally consistent with each other
   - If a character/concept/entity is mentioned in multiple questions, the answers must NOT contradict
   - Questions must test DIFFERENT facts, not the same fact in different ways

5. ✅ CONSISTENCY VERIFICATION CHECKLIST (MANDATORY):
   Before finalizing your output, verify:
   ✓ No two questions test the same fact or concept
   ✓ No two questions ask about the same entity/concept in conflicting ways
   ✓ All answers are internally consistent (no contradictions)
   ✓ If entity X is mentioned in multiple questions, all answers about X are consistent
   ✓ Each question covers a DIFFERENT topic, concept, or piece of information

EXAMPLES OF FORBIDDEN INCONSISTENCIES (DO NOT GENERATE):
❌ FORBIDDEN Example 1 (Same Concept):
   Q1: "What is Zigzag?" → Answer: "A snake"
   Q2: "What kind of bird is Zigzag?" → Answer: "A singing bird"
   (FORBIDDEN: Contradictory answers - Zigzag cannot be both snake and bird)

❌ FORBIDDEN Example 2 (Same Fact):
   Q1: "What is the capital of India?" → Answer: "New Delhi"
   Q2: "Name the capital city of India." → Answer: "New Delhi"
   (FORBIDDEN: Same fact tested twice - must test different information)

❌ FORBIDDEN Example 3 (Conflicting Information):
   Q1: "What is the value of x when x² = 16?" → Answer: "x = 4"
   Q2: "Solve x² = 16" → Answer: "x = -4"
   (FORBIDDEN: Inconsistent - both ±4 are correct, but answers contradict)

✅ REQUIRED Example (Different Concepts):
   Q1: "What is the capital of India?" → Answer: "New Delhi"
   Q2: "What is the largest river in India?" → Answer: "Ganges"
   Q3: "Name the highest mountain peak in India." → Answer: "Mount Kanchenjunga"
   (REQUIRED: Each question tests a DIFFERENT fact - all consistent)

FINAL CONSISTENCY WARNING:
If you generate ANY questions that test the same fact/concept OR provide conflicting answers, the ENTIRE output is INVALID and must be regenerated. Every question must test a DIFFERENT fact, and all answers must be internally consistent.

{marks_structure}

=== DIFFICULTY MODE (STRICT - MUST FOLLOW) ===
Difficulty Level: {difficulty}
- Easy: Basic understanding, direct answers
- Medium: Application of concepts, step-wise solutions
- Hard: Deep understanding, full derivations

🚨🚨🚨 CRITICAL: HARD MODE RESTRICTIONS 🚨🚨🚨
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

{"=== MATHEMATICS FORMATTING RULES (CRITICAL - MANDATORY - ONLY FOR MATHEMATICS) ===" if detected_subject == "mathematics" else "=== FORMATTING RULES (SUBJECT-SPECIFIC) ==="}

{math_formatting_rules if detected_subject == "mathematics" else other_subject_formatting}

{exam_friendly_examples if detected_subject == "mathematics" else ""}

=== BOARD EXAM QUESTION FRAMING (MANDATORY - FOLLOW EXAM PATTERNS) ===
🚨🚨🚨 CRITICAL: Generate questions EXACTLY as they appear in board exams 🚨🚨🚨

BOARD EXAM QUESTION PATTERNS (MANDATORY TO FOLLOW):

1. QUESTIONS MUST BE CLEAR AND UNDERSTANDABLE:
   ✅ Use simple, direct language that students can easily understand
   ✅ Avoid complex sentence structures - keep questions straightforward
   ✅ Each question should test ONE specific concept or fact
   ✅ Questions should be self-contained (no ambiguity)

2. QUESTION FRAMING FOR DIFFERENT SUBJECTS:

   FOR SOCIAL SCIENCE / HISTORY:
   ✅ Use clear, factual questions: "முதல் உலகப் போர் எப்போது தொடங்கியது?" (When did World War I begin?)
   ✅ For 2-mark questions: "முதல் உலகப் போரின் முக்கிய காரணங்களை குறிப்பிடவும்" (List the main causes of World War I)
   ✅ For 3-mark questions: "முதல் உலகப் போரின் பின்னணி மற்றும் அதன் முக்கிய அம்சங்களை விளக்குக" (Explain the background and main features of World War I)
   ✅ For 5-mark questions: "முதல் உலகப் போரின் காரணங்கள் மற்றும் விளைவுகளை முழுமையாக விவரிக்கவும்" (Describe the causes and effects of World War I in detail)
   ❌ AVOID: Vague questions, overly complex phrasing, ambiguous wording

   FOR MATHEMATICS:
   ✅ Use clear problem statements: "x² - 4 = 0 என்ற சமன்பாட்டின் மூலங்களை கண்டறியவும்" (Find the roots of the equation x² - 4 = 0)
   ✅ For 10-mark questions: Provide complete step-by-step solutions with clear headings
   ✅ Show all calculations and intermediate steps

   FOR SCIENCE:
   ✅ Use clear, concept-based questions: "பிரகாசத்தின் வேகம் என்ன?" (What is the speed of light?)
   ✅ For descriptive questions: Ask for explanations with examples

3. QUESTION STRUCTURE REQUIREMENTS:
   ✅ 1-mark MCQ: Clear question with 4 distinct options
   ✅ 2-mark Short Answer: Direct question requiring brief explanation (2-3 sentences)
   ✅ 3-mark Descriptive: Question requiring explanation with examples (4-6 sentences)
   ✅ 5-mark Descriptive: Comprehensive question requiring detailed explanation (8-12 sentences with introduction, body, conclusion)
   ✅ 10-mark Descriptive: Very detailed question requiring complete analysis (15-20 sentences with multiple sections)

4. LANGUAGE AND CLARITY:
   ✅ Use proper grammar and correct terminology
   ✅ Questions should be in the target language (Tamil/English/etc.) as specified
   ✅ Avoid jargon unless it's part of the curriculum
   ✅ Each question should be independently answerable

5. SOURCE HINT REQUIREMENTS:
   ✅ MUST reference actual part numbers: "Part 1 (Page 3)", "Part 2 (Page 15)"
   ✅ MUST reference actual page numbers from the content: "பக்கம் 3", "பக்கம் 15"
   ✅ MUST reference actual sections: "Section on World War I", "Chapter 2: Quadratic Equations"
   ❌ NEVER use generic hints like "From provided study material" or "பக்கம் 31" for all questions
   ✅ Each question's source_hint should be UNIQUE and reference DIFFERENT pages/sections

6. EXAMPLES OF GOOD BOARD EXAM QUESTIONS:

   ✅ GOOD (1-mark MCQ):
      "முதல் உலகப் போர் எப்போது தொடங்கியது?"
      Options: A. 1912, B. 1914, C. 1916, D. 1918
      Answer: 1914
      Source: Part 1 (Page 3)

   ✅ GOOD (2-mark Short Answer):
      "முதல் உலகப் போரின் முக்கிய காரணங்களை குறிப்பிடவும்."
      Answer: "முதல் உலகப் போரின் முக்கிய காரணங்கள்: 1. காலனிய ஆட்சிகள், 2. தேசியத்துவம், 3. இராணுவ ஒப்பந்தங்கள்"
      Source: Part 1 (Page 5)

   ✅ GOOD (5-mark Descriptive):
      "முதல் உலகப் போரின் காரணங்கள் மற்றும் விளைவுகளை முழுமையாக விவரிக்கவும்."
      Answer: [Detailed explanation with introduction, main points, and conclusion]
      Source: Part 2 (Page 20)

7. EXAMPLES OF BAD QUESTIONS (AVOID):

   ❌ BAD: "முதல் உலகப் போரின் வெடிவின் காரணங்களில் ஒன்று என்ன?" (Unclear phrasing - "வெடிவின்" is awkward)
   ✅ GOOD: "முதல் உலகப் போரின் முக்கிய காரணங்களில் ஒன்று என்ன?" (Clear and direct)

   ❌ BAD: "இங்கிலாந்து மற்றும் பிரான்சின் மத்திய ஆட்சியின் பெயர் என்ன?" (Confusing - what is "மத்திய ஆட்சி"?)
   ✅ GOOD: "முதல் உலகப் போரில் இங்கிலாந்து மற்றும் பிரான்ஸ் சேர்ந்த கூட்டணியின் பெயர் என்ன?" (Clear and specific)

   ❌ BAD: Generic source hints like "பக்கம் 31" for all questions
   ✅ GOOD: Specific source hints like "Part 1 (Page 3): World War I Causes" or "Part 2 (Page 15): Russian Revolution"

CRITICAL REQUIREMENTS:
- Every question MUST be framed like a real board exam question
- Questions MUST be clear, understandable, and unambiguous
- Source hints MUST reference actual part numbers and pages from the content
- Questions MUST follow the exact mark distribution requested
- Language MUST be appropriate for board exams (formal, clear, correct)

=== QUESTION FORMAT VARIATION (ABSOLUTELY MANDATORY - ZERO TOLERANCE) ===
[CRITICAL] STRICTLY FORBIDDEN: NO REPETITION OF QUESTION FORMATS, OPENERS, STRUCTURES, OR FRAMES [CRITICAL]

ABSOLUTE PROHIBITION RULES:
- [X] NEVER use the same opener for ANY two questions (even non-consecutive)
- [X] NEVER use the same structure for ANY two questions (even non-consecutive)
- [X] NEVER use the same frame/template for ANY two questions
- [OK] EVERY question MUST be TOTALLY DIFFERENT from ALL others in format, structure, and framing

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

{"MATH-SPECIFIC VARIATION (EACH MUST BE UNIQUE - ONLY FOR MATHEMATICS):" if detected_subject == "mathematics" else "SUBJECT-SPECIFIC VARIATION (EACH MUST BE UNIQUE):"}
{math_variation_text if detected_subject == "mathematics" else other_variation_text}

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
   🚨🚨🚨 CRITICAL: You MUST generate questions for ALL marks values in the distribution 🚨🚨🚨
   🚨🚨🚨 If distribution includes 10 marks, you MUST generate 10-mark questions 🚨🚨🚨
   🚨🚨🚨 If distribution includes 5 marks, you MUST generate 5-mark questions 🚨🚨🚨
   🚨🚨🚨 DO NOT skip any marks values - generate questions for ALL requested marks 🚨🚨🚨
3. Use correct question types:
   - MCQ → 4 options + correct_answer field (ONLY for 1-2 marks)
   - Short Answer (1–2 marks) → type: "short"
   - Descriptive (1–10 marks) → type: "descriptive" (1 mark = 1-2 lines, 3+ marks = detailed)
4. ANSWER LENGTH RULES (STRICT - MUST FOLLOW EXACTLY):
   - 1 mark → 1–2 lines ONLY (very short, factual, direct answer - maximum 2 lines)
   - 2 marks → 2–3 lines ONLY (brief explanation, concise - exactly 2-3 lines)
   - 3 marks → 4–5 lines ONLY (short descriptive paragraph - exactly 4-5 lines)
   - 5 marks → 6–8 lines ONLY (medium descriptive with examples - exactly 6-8 lines)
   - 10 marks → 9-10 lines minimum (STRICT - board-exam answer script format)
     * Structure depends on subject:
       - Mathematics: Given → Formula → Calculation/Steps → Final Answer
       - English: Introduction → Explanation → Analysis → Conclusion
       - Science: Definition → Explanation → Example → Conclusion
       - Social Science: Background/Context → Key Points → Explanation → Conclusion
     * Short answers are INVALID
     * Treat as board-exam answer script with full working/explanation
   
   CRITICAL: Count lines carefully. Answers MUST match the specified line count for each mark value.
   CRITICAL: For mathematics, follow difficulty-based answer structure (Easy: 1-2 lines, Medium: 3-6 lines, Hard: 8-15 lines)
5. If remaining_questions is less than the requested total, DO NOT generate extra questions. Fill only up to the allowed limit.
6. All questions must come ONLY from the study material.
7. CRITICAL: NO duplicated questions - each question must be completely unique and distinct.
   - This applies to ALL languages (English, Tamil, Hindi, Telugu, Kannada, Malayalam, Arabic, Spanish)
   - Even if questions are in different languages, they must cover different topics/concepts
   - Avoid rephrasing the same question - each question must test different knowledge points
   - Ensure variety in question topics, concepts, and difficulty levels
8. MCQs must be distinct and meaningful - avoid similar or overlapping options or questions that test the same concept.
9. Output must ALWAYS follow this exact JSON format (STRUCTURED - NO \\n, NO paragraphs):

<<<<<<< HEAD
{json_example_math if detected_subject == "mathematics" else (json_example_other if detected_subject in ["english", "science", "social_science"] else json_example_general)}
=======
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
      "topic": "Calculus - Critical Points",
      "source_hint": "Chapter on Derivatives and Applications",
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
      "topic": "Character Development",
      "source_hint": "Chapter 5: Character Analysis",
      "correct_answer": "The main character undergoes significant growth throughout the narrative. Initially, they are portrayed as naive and inexperienced. As the story progresses, they face various challenges that test their resolve. These experiences shape their personality and worldview. By the end, they emerge as a more mature and understanding individual."
    }},
    {{
      "marks": 5,
      "type": "descriptive",
      "difficulty": "medium",
      "question": "Explain the theme of the poem and analyze its literary devices.",
      "topic": "Poetry Analysis",
      "source_hint": "Section on Literary Analysis",
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
      "topic": "Historical Events Analysis",
      "source_hint": "Chapter 8: Major Historical Events",
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
      "topic": "General Concept",
      "source_hint": "Relevant section from study material",
      "correct_answer": "Definition: The concept is defined as... Explanation: It involves several key aspects... Example: For instance... Conclusion: In summary..."
    }},
"""}
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
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

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
- TARGET LANGUAGE: {target_language_name}
- ALL questions MUST be written in {target_language_name} ONLY
- ALL answers MUST be written in {target_language_name} ONLY
- If target language is Tamil: EVERY question must use Tamil script (தமிழ்). NO English questions allowed.
- If target language is English: EVERY question must be in English. NO other languages allowed.
- If you generate even ONE question in the wrong language, the output is INVALID.
- Check each question before outputting: Is it in {target_language_name}? If not, rewrite it.

LANGUAGE-SPECIFIC EXAM STYLE (MANDATORY):
🚨 TARGET LANGUAGE: {target_language_name.upper()} 🚨
You MUST generate ALL content (questions, answers, options) EXCLUSIVELY in {target_language_name}. NO EXCEPTIONS.

You MUST use formal exam-style phrasing appropriate for {target_language_name}:
<<<<<<< HEAD
- Tamil (ta-IN): Use formal கல்வி மொழி Tamil. Use patterns like: "... என்றால் என்ன?", "சுருக்கமாக எழுதுக", "விளக்குக", "விவரிக்கவும்", "வேறுபாடுகளை எழுதுக". Avoid spoken Tamil. ALL questions and answers MUST be in Tamil script.
- English (en): Use formal academic tone. Use patterns like: "Define …", "Explain …", "Describe …", "Write short notes on …", "Differentiate between …"
- Hindi (hi-IN): Use शुद्ध हिन्दी / परीक्षा शैली. Use: "परिभाषित कीजिए", "समझाइए", "विवरण दीजिए", "लघु उत्तरीय प्रश्न", "दीर्घ उत्तरीय प्रश्न"
- Telugu (te-IN): Use formal textbook Telugu. Use: "అంటే ఏమిటి?", "సంక్షిప్తంగా వ్రాయండి", "వివరించండి"
- Kannada (kn-IN): Use school exam style Kannada. Use: "ಎಂದರೆ ಏನು?", "ಸಂಕ್ಷಿಪ್ತ ಉಕ್ಕಿ ಬರೆಯಿರಿ", "ವಿವರಿಸಿ"
- Malayalam (ml-IN): Use formal academic Malayalam. Use: "എന്താണ്?", "വ്യാഖ്യാനിക്കുക", "സംക്ഷിപ്തമായി എഴുതുക"
- Arabic (ar): Use Modern Standard Arabic. Use: "ما هو …؟", "اشرح", "وضح"
- Spanish (es): Use neutral academic Spanish. Use: "Defina …", "Explique …", "Describa …"
CRITICAL: All questions and answers MUST use the appropriate exam-style phrasing for {target_language_name}. DO NOT use casual or spoken language - ONLY formal exam-style phrasing.
=======
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
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)

🚨 ABSOLUTE LANGUAGE REQUIREMENT 🚨
- If target language is Tamil: ALL questions MUST be in Tamil (தமிழ் script). NO English questions allowed.
- If target language is English: ALL questions MUST be in English. NO other languages allowed.
- If target language is Hindi: ALL questions MUST be in Hindi (Devanagari script). NO other languages allowed.
- This applies to BOTH questions AND answers - they must match the target language.
- If you generate even ONE question in the wrong language, the entire output is INVALID.

<<<<<<< HEAD
🎯 QUALITY-FIRST REQUIREMENTS - READ CAREFULLY 🎯

QUESTION COUNT (PREFERRED TARGET - QUALITY OVER QUANTITY):
- 🎯 Target: Generate UP TO {actual_num_questions} high-quality questions
- 🎯 The number {actual_num_questions} is a PREFERRED target, not a strict requirement
- ✅ If content is sufficient, generate as close to {actual_num_questions} as possible
- ✅ If content is limited, generate fewer questions to maintain quality
- ✅ DO NOT force questions if the study material doesn't support them
- ✅ DO NOT invent topics that are not present in the content
- ✅ Each question must be clearly worded, syllabus-relevant, and suitable for exams
- ✅ It is acceptable to generate fewer questions if quality would be compromised
- 🎯 DISTRIBUTION PREFERENCE: Try to match this distribution: {distribution_string}
- 🎯 If you cannot generate enough questions for the full distribution, generate what you can while maintaining quality

DISTRIBUTION PREFERENCES (QUALITY-FIRST APPROACH):
- Preferred distribution: {distribution_string}
- NEVER exceed {remaining_questions} questions
- Try to match the distribution, but prioritize quality over exact count
- 🎯 DISTRIBUTION BREAKDOWN - TARGET (not strict):
{chr(10).join([f"  • Target: {item.get('count', 0)} questions of {item.get('marks', 0)} marks (type: {item.get('type', 'descriptive')})" for item in distribution_list])}
- 🎯 TOTAL TARGET: {actual_num_questions} questions (sum of all above)
- ✅ If you can generate all questions matching the distribution, do so
- ✅ If content is limited, generate fewer questions but maintain quality
- ✅ Focus on clarity, correctness, and syllabus relevance
=======
QUALITY OVER QUANTITY (HIGHEST PRIORITY):
- ✅ Generate questions ONLY if the content clearly supports them
- ✅ Do NOT force additional questions to meet a number
- ✅ If the content does not support the requested number of questions, generate the maximum number of HIGH-QUALITY questions possible
- ✅ Do NOT repeat question patterns, equations, or ideas
- ✅ Do NOT invent or stretch content to increase count
- ✅ Quality is MORE IMPORTANT than quantity
- ✅ If you can only generate fewer than {actual_num_questions} high-quality questions, generate only what you can support with the content

CONTENT ABUNDANCE DETECTION:
- 📊 This content is {total_content_length:,} characters (~{num_pages_estimate} pages estimated)
- 📊 For {actual_num_questions} questions, you need approximately {questions_per_page:.1f} questions per page
- 📊 This content is ABUNDANT and should easily support {actual_num_questions} unique, high-quality questions
- 📊 With this much content, you should be able to generate the full {actual_num_questions} questions without repetition
- 📊 Use different topics, concepts, and angles from throughout the content to ensure uniqueness

QUESTION COUNT (TARGET - STRIVE FOR FULL COUNT WHEN CONTENT IS ABUNDANT):
- 🎯 Target: Generate exactly {actual_num_questions} questions
- 🎯 The "questions" array in your JSON should contain {actual_num_questions} question objects
- 🎯 With abundant content ({total_content_length:,} chars, ~{num_pages_estimate} pages), you should be able to generate the full {actual_num_questions} questions
- 🎯 Use different sections, topics, and concepts from the content to ensure all {actual_num_questions} questions are unique
- 🎯 Spread questions across different parts/pages of the content - don't focus on just one section or page
- 🎯 Read through the ENTIRE content (beginning, middle, end) and generate questions from DIFFERENT pages/sections
- 🎯 If content has page markers (e.g., "Part 1 (Pages 1-40)", "Part 2 (Pages 41-80)"), use DIFFERENT parts/pages for different questions
- 🎯 When providing source_hint, reference DIFFERENT page numbers/sections - don't use the same page for all questions
- 🎯 If content supports fewer questions, generate only the number you can support with HIGH QUALITY
- 🎯 NEVER exceed {remaining_questions} questions
- 🎯 NEVER generate low-quality or repetitive questions just to meet the count
- 🎯 NEVER invent content or stretch material to create more questions

DISTRIBUTION REQUIREMENTS (MANDATORY - STRICT ENFORCEMENT):
🚨🚨🚨 CRITICAL: You MUST follow the distribution EXACTLY 🚨🚨🚨
- Distribution: {distribution_string}
- You MUST generate questions for ALL marks values in the distribution
- If distribution includes 10 marks, you MUST generate 10-mark questions (NO EXCEPTIONS)
- If distribution includes 5 marks, you MUST generate 5-mark questions (NO EXCEPTIONS)
- If distribution includes 3 marks, you MUST generate 3-mark questions (NO EXCEPTIONS)
- DO NOT skip any marks values - generate questions for ALL requested marks
- DO NOT generate only 1-mark and 2-mark questions if 5-mark and 10-mark are requested
- The distribution is MANDATORY - you must follow it EXACTLY
- With {total_content_length:,} chars (~{num_pages_estimate} pages), there is MORE than enough content to generate ALL requested marks
- 🚨🚨🚨 FAILURE TO GENERATE ALL MARKS VALUES = INVALID OUTPUT 🚨🚨🚨
- 🚨🚨🚨 If you skip 10-mark or 5-mark questions, the output is INVALID and must be regenerated 🚨🚨🚨
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)

QUALITY CHECK BEFORE OUTPUT:
1. Count the questions in your "questions" array
<<<<<<< HEAD
2. Verify each question is high-quality, clearly worded, and syllabus-relevant
3. Ensure no questions are invented or forced if content doesn't support them
4. If you have fewer than {actual_num_questions} questions but they are all high-quality, that is acceptable
5. Output when you have generated the best possible questions from the content
=======
2. Verify ALL marks values from the distribution are present:
   - Check: Do I have 10-mark questions if distribution requires them?
   - Check: Do I have 5-mark questions if distribution requires them?
   - Check: Do I have 3-mark questions if distribution requires them?
   - Check: Do I have all other marks values from the distribution?
3. Verify all questions are HIGH QUALITY and UNIQUE (no repetition)
4. Verify all questions are supported by the content (no invented content)
5. 🚨🚨🚨 CRITICAL: If ANY marks value from the distribution is missing, you MUST regenerate to include it 🚨🚨🚨
6. Only output when you have verified ALL marks values are present AND quality and uniqueness
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
- Output ONLY valid JSON - no markdown, no explanations, no text before/after JSON
- CRITICAL: EVERY question MUST have a "correct_answer" field - this is MANDATORY for ALL mark values (1, 2, 3, 5, 10 marks)
- For 5+ marks: Use structured format (object with subject-appropriate fields)
  * Mathematics: Use object with given, formula, steps, final
  * English/Literature: Use object with introduction, explanation, analysis, conclusion (OR string with embedded headings like "Introduction: ... Explanation: ... Analysis: ... Conclusion: ...")
  * Science: Use object with definition, explanation, example, conclusion (OR string with embedded headings)
  * Social Science: Use object with background, key_points, explanation, conclusion (OR string with embedded headings)
- For 1-3 marks: Can use simple string format, but MUST provide an answer
🚨 CRITICAL LANGUAGE REQUIREMENT 🚨
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
  
  🚨 CRITICAL FOR MATHEMATICS - SUBJECT-SPECIFIC STRICT RULE:
  - For numerical problems, you MUST compute the final answer - listing given values alone is NOT an answer
  - Show necessary steps suitable for the given marks
  - Never stop at "Given:" statements - always proceed to calculation and final answer
  
  📐 FOR LCM/HCF (GCD) QUESTIONS - MANDATORY REQUIREMENTS:
  - ALWAYS provide ALL of the following:
    1) Method: Explain the method used (Prime Factorization, Division Method, etc.)
    2) HCF value: Calculate and state the HCF (Highest Common Factor/GCD)
    3) LCM value: Calculate and state the LCM (Least Common Multiple)
  - Show complete working with all steps
  - Never leave the answer incomplete - always provide both HCF and LCM values
  - Example structure: Given → Method → Calculation/Steps → Final Answer: HCF = [value], LCM = [value]

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
  - "background" or "context": string - REQUIRED for 5+ marks
  - "key_points": string or array of strings - REQUIRED for 5+ marks
  - "explanation": string - REQUIRED for 5+ marks
  - "conclusion": string - REQUIRED for 5+ marks
  - OR can be a single string with embedded headings: "Background/Context: ... Key Points: ... Explanation: ... Conclusion: ..."

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
✓ Answer has minimum 10-15 lines (NO SHORT ANSWERS - INVALID)
✓ ALL mandatory parts present (in order):
  (i) Given - What is provided in the problem
  (ii) Definition (if applicable) - Define key terms/concepts
  (iii) Formula/Theorem - State the formula or theorem
  (iv) Step-by-step working - Numbered steps with complete calculations
  (v) Logical explanation - Explain reasoning and method
  (vi) Final conclusion statement - Summarize and state final answer
✓ Step numbering present (Step 1, Step 2, Step 3, ...)
✓ Final answer clearly stated: "Final Answer: ..." (exam-friendly format, NO LaTeX)
✓ Treated as board-exam answer script with full working
✓ NO abbreviated answers - full working is mandatory

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

🚨🚨🚨 CRITICAL FINAL REMINDER 🚨🚨🚨

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

<<<<<<< HEAD
🎯 FINAL QUALITY CHECK BEFORE OUTPUTTING JSON:
1. Generate high-quality questions from the study material (target: {actual_num_questions})
2. Count the questions: questions.length should be close to {actual_num_questions} (fewer is acceptable if quality is maintained)
3. Verify quality: Each question must be clearly worded, syllabus-relevant, and suitable for exams
4. Verify content: No invented topics - all questions must be based on the provided study material
5. If you have fewer than {actual_num_questions} questions but they are all high-quality, that is acceptable
6. Output JSON when you have generated the best possible questions from the content

✅ ACCEPTABLE: Generating fewer questions if content is insufficient or quality would be compromised
✅ FOCUS: Quality, clarity, correctness, and syllabus relevance over exact count
"""
=======
🚨 FINAL VERIFICATION BEFORE OUTPUTTING JSON:
1. Generate HIGH-QUALITY questions from the content - TARGET: {actual_num_questions} questions
2. With {total_content_length:,} characters of content (~{num_pages_estimate} pages), you should be able to generate all {actual_num_questions} questions
3. Verify all questions are UNIQUE (no repetition of patterns, equations, or ideas)
4. Verify all questions are supported by the content (no invented or stretched content)
5. Verify distribution as closely as possible (quality over exact matching)
6. Use different topics, sections, and concepts from throughout the content to ensure uniqueness
7. If content is truly insufficient (very short content), generate only what you can support with HIGH QUALITY
8. Only output JSON when you have verified quality and uniqueness
{"9. 🚨 GRAMMAR CONTENT CHECK: Verify EVERY question is about GRAMMAR RULES, NOT poems/stories/characters" if is_grammar_content else ""}
{"10. 🚨 If ANY question is about poetry, themes, authors, or literature, REJECT the entire output and regenerate" if is_grammar_content else ""}
{"11. 🚨 For EACH question, verify you can point to the SPECIFIC section in [STUDY_MATERIAL] where this concept is taught" if is_grammar_content else ""}
{"12. 🚨 For EACH question, provide a SPECIFIC topic (actual concept name) and source_hint (actual content location)" if is_grammar_content else ""}
{"13. 🚨 Generic topics like 'Which of the' or source hints like 'From provided study material' indicate you are NOT reading the content - this is INVALID" if is_grammar_content else ""}

CRITICAL: With abundant content ({total_content_length:,} chars), strive to generate the full {actual_num_questions} questions. Quality is important, but with this much content, you should be able to achieve both quality AND quantity.
{"🚨🚨🚨 FINAL GRAMMAR REMINDER: For grammar content, ONLY grammar questions are valid. Literature questions = INVALID OUTPUT." if is_grammar_content else ""}
{"🚨🚨🚨 FINAL CONTENT REMINDER: You MUST read the [STUDY_MATERIAL] and extract topics/source hints from ACTUAL content sections, not use generic placeholders." if is_grammar_content else ""}"""

    try:
        # Calculate max_tokens based on number of questions requested
        # BUT: We must ensure prompt + content + max_tokens <= 128,000 tokens
        # The prompt is already very large (~127k tokens based on error), so we have very little room
        # Estimate: ~200-300 tokens per question (including JSON structure)
        estimated_tokens_per_question = 300
        max_tokens_estimate = (num_questions * estimated_tokens_per_question) + 2000
        
        # Estimate prompt + content tokens
        # Rough estimate: 1 token ≈ 3.5 characters for non-English content (Tamil uses more tokens)
        # For Tamil/other languages, use 1 token ≈ 2.5 chars (more conservative)
        estimated_content_tokens = len(text_content) // 2.5
        estimated_prompt_tokens = (len(SYSTEM_PROMPT) + len(user_prompt)) // 2.5
        
        # Calculate available tokens for completion
        # Leave a safety margin of 2000 tokens to account for estimation errors
        total_estimated = estimated_prompt_tokens + estimated_content_tokens
        available_for_completion = max(2000, 128000 - total_estimated - 2000)
        
        # Use the smaller of: requested tokens or available tokens
        max_tokens = min(max_tokens_estimate, available_for_completion)
        
        # Cap at 16384 (GPT-4o-mini's max output tokens)
        max_tokens = min(max_tokens, 16384)
        
        # Ensure minimum of 2000 tokens for small requests
        max_tokens = max(max_tokens, 2000)
        
        print(f"📊 Token budget: Prompt~{estimated_prompt_tokens:.0f}k, Content~{estimated_content_tokens:.0f}k, Total~{total_estimated:.0f}k, Available for completion: {available_for_completion:.0f}k, Requesting: {max_tokens}k")
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
                response_format={"type": "json_object"},
                max_tokens=max_tokens
            )
        except Exception as api_error:
            # Check if it's a context length exceeded error
            error_str = str(api_error)
            if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                raise ValueError(
                    f"Content is too large for AI processing. The selected PDF parts contain too much content. "
                    f"Please try selecting fewer parts or reduce the number of questions requested. "
                    f"Error details: {error_str[:200]}"
                )
            # Re-raise other errors
            raise
        
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
        
        # Log response preview for debugging
        print(f"📥 AI Response length: {len(response_content)} characters")
        print(f"📥 Response preview (first 500 chars): {response_content[:500]}...")
        
        # Clean and fix common JSON issues
        try:
            # Remove any markdown code blocks if present
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON
            result = json.loads(response_content)
            print("✅ JSON parsed successfully")
            
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
                # Last resort: try to extract complete question objects from truncated JSON
                # Find the questions array start
                questions_start = fixed_content.find('"questions"')
                if questions_start >= 0:
                    # Find the opening bracket after "questions"
                    bracket_start = fixed_content.find('[', questions_start)
                    if bracket_start >= 0:
                        # Try to extract complete question objects one by one
                        questions_text = fixed_content[bracket_start:]
                        questions_list = []
                        current_pos = 1  # Skip the opening bracket
                        brace_count = 0
                        in_string = False
                        escape_next = False
                        question_start = -1
                        
                        # Parse character by character to find complete question objects
                        for i, char in enumerate(questions_text[1:], 1):  # Start from position 1 (after '[')
                            if escape_next:
                                escape_next = False
                                continue
                            
                            if char == '\\':
                                escape_next = True
                                continue
                            
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                            
                            if in_string:
                                continue
                            
                            if char == '{':
                                if brace_count == 0:
                                    question_start = i
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0 and question_start >= 0:
                                    # Found a complete question object
                                    question_json = questions_text[question_start:i+1]
                                    try:
                                        question_obj = json.loads(question_json)
                                        questions_list.append(question_obj)
                                        print(f"✅ Extracted question {len(questions_list)} from truncated JSON")
                    except:
                                        # Skip invalid question
                                        pass
                                    question_start = -1
                            elif char == ']' and brace_count == 0:
                                # End of questions array
                                break
                        
                        if questions_list:
                            result = {"questions": questions_list}
                            print(f"✅ Successfully extracted {len(questions_list)} questions from truncated JSON")
                        else:
                            # Sanitize error message to avoid Unicode encoding issues
                            error_preview = response_content[:200].encode('ascii', 'ignore').decode('ascii')
                        raise ValueError(
                            f"Failed to parse AI response as JSON after all fixes. "
                            f"Original error: {str(e)}. "
                            f"Fix error: {str(e2)}. "
                                f"Response appears to be truncated. Response preview: {error_preview}..."
                        )
                else:
                        # Sanitize error message to avoid Unicode encoding issues
                        error_preview = response_content[:200].encode('ascii', 'ignore').decode('ascii')
                    raise ValueError(
                        f"Failed to parse AI response as JSON. "
                        f"Error: {str(e)}. "
                        f"Error at line {e.lineno}, column {e.colno}. "
                            f"Response preview: {error_preview}..."
                        )
                else:
                    # Sanitize error message to avoid Unicode encoding issues
                    error_preview = response_content[:200].encode('ascii', 'ignore').decode('ascii')
                    raise ValueError(
                        f"Failed to parse AI response as JSON. "
                        f"Error: {str(e)}. "
                        f"Error at line {e.lineno}, column {e.colno}. "
                        f"Response preview: {error_preview}..."
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
        
        # ============================================
        # CONTENT GROUNDING RULES COMPLIANCE LOGGING
        # ============================================
        print("\n" + "="*80)
        print("📋 CONTENT GROUNDING RULES COMPLIANCE CHECK")
        print("="*80)
        print(f"Total questions generated: {len(questions)}")
        print(f"Content length: {len(text_content)} characters")
        print(f"Expected questions: {num_questions}")
        
        # Check for topic and source_hint fields
        questions_with_topic = 0
        questions_with_source_hint = 0
        questions_missing_both = 0
        topics_found = []
        
        for idx, q in enumerate(questions):
            has_topic = bool(q.get("topic"))
            has_source_hint = bool(q.get("source_hint"))
            
            if has_topic:
                questions_with_topic += 1
                topics_found.append(q.get("topic"))
            if has_source_hint:
                questions_with_source_hint += 1
            if not has_topic and not has_source_hint:
                questions_missing_both += 1
                print(f"⚠️  Q{idx+1}: Missing both 'topic' and 'source_hint' fields")
        
        print(f"\n📊 Topic/Source Tracking:")
        print(f"   ✅ Questions with 'topic': {questions_with_topic}/{len(questions)} ({questions_with_topic*100//len(questions) if questions else 0}%)")
        print(f"   ✅ Questions with 'source_hint': {questions_with_source_hint}/{len(questions)} ({questions_with_source_hint*100//len(questions) if questions else 0}%)")
        print(f"   ⚠️  Questions missing both: {questions_missing_both}/{len(questions)}")
        
        if topics_found:
            print(f"\n📚 Topics identified by AI:")
            for i, topic in enumerate(topics_found[:10], 1):  # Show first 10
                print(f"   {i}. {topic}")
            if len(topics_found) > 10:
                print(f"   ... and {len(topics_found) - 10} more")
        
        # Check for content grounding violations
        print(f"\n🔍 Content Grounding Analysis:")
        
        # Check question uniqueness (no repetition)
        question_texts = [q.get("question", "").lower().strip() for q in questions]
        unique_questions = len(set(question_texts))
        duplicate_count = len(questions) - unique_questions
        print(f"   ✅ Unique questions: {unique_questions}/{len(questions)}")
        if duplicate_count > 0:
            print(f"   ⚠️  Duplicate questions detected: {duplicate_count}")
        
        # Check for common violations
        violations = []
        
        # Check if questions seem to test different concepts
        if len(topics_found) < len(set(topics_found)):
            violations.append(f"Topic repetition detected: {len(topics_found) - len(set(topics_found))} repeated topics")
        
        # Check answer consistency (basic check)
        answers = [str(q.get("correct_answer", q.get("answer", ""))).lower() for q in questions]
        if len(answers) != len(set(answers)):
            print(f"   ⚠️  Some answers appear similar (potential consistency issue)")
        
        if violations:
            print(f"\n⚠️  Potential Content Grounding Violations:")
            for v in violations:
                print(f"   - {v}")
        else:
            print(f"   ✅ No obvious content grounding violations detected")
        
        # Subject-specific validation
        print(f"\n🎯 Subject-Specific Validation:")
        print(f"   Detected Subject: {detected_subject}")
        
        if detected_subject == "english":
            # Check if content is grammar-focused (but also check for stories/poems)
            grammar_keywords = ['grammar', 'noun', 'verb', 'tense', 'sentence', 'subject-verb', 'parts of speech', 
                              'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction', 'article']
            literature_keywords = ['poem', 'poetry', 'story', 'character', 'narrator', 'plot', 'theme', 'author', 'poet', 'stanza', 'verse']
            
            has_grammar = any(keyword in text_content.lower() for keyword in grammar_keywords)
            has_literature = any(keyword in text_content.lower() for keyword in literature_keywords)
            
            # Only validate grammar-only if content is PURELY grammar (no literature)
            is_grammar_content = has_grammar and not has_literature
            
            if is_grammar_content:
                print(f"   ⚠️  GRAMMAR CONTENT DETECTED - Validating questions are grammar-focused...")
                grammar_questions = 0
                non_grammar_questions = []
                
                for idx, q in enumerate(questions):
                    question_text = q.get('question', '').lower()
                    topic = q.get('topic', '').lower()
                    
                    # Check if question is about grammar
                    is_grammar_q = any(keyword in question_text or keyword in topic 
                                      for keyword in grammar_keywords + ['rule', 'structure', 'agreement', 'form'])
                    
                    # Check if question is about stories/characters/poetry (should NOT be for grammar content)
                    is_story_q = any(keyword in question_text 
                                    for keyword in [
                                        'character', 'story', 'narrator', 'plot', 'theme', 'author', 'poet', 'poem', 'poetry',
                                        'who was', 'what happened', 'describe the', 'tell about', 'literary device',
                                        'what does the poet', 'what is the theme', 'who is the author', 'explain the poet',
                                        'analyze how the poem', 'discuss the various ways', 'poet\'s attitude', 'poet\'s outlook',
                                        'primary theme', 'main theme', 'literary devices', 'figure of speech', 'metaphor', 'simile'
                                    ])
                    
                    if is_grammar_q and not is_story_q:
                        grammar_questions += 1
                    else:
                        non_grammar_questions.append((idx + 1, q.get('question', 'N/A')[:80]))
                
                print(f"   ✅ Grammar-focused questions: {grammar_questions}/{len(questions)}")
                if non_grammar_questions:
                    print(f"   🚨 CRITICAL VIOLATION: {len(non_grammar_questions)} non-grammar questions detected!")
                    print(f"   ⚠️  These questions violate grammar content grounding rules:")
                    for q_num, q_text in non_grammar_questions[:10]:  # Show first 10
                        print(f"      Q{q_num}: {q_text}...")
                    
                    # Calculate violation percentage
                    violation_percentage = (len(non_grammar_questions) / len(questions)) * 100
                    print(f"   ⚠️  Violation rate: {violation_percentage:.1f}% ({len(non_grammar_questions)}/{len(questions)} questions)")
                    
                    # If more than 50% are non-grammar, raise an error to force regeneration
                    if violation_percentage > 50:
                        violation_details = ", ".join([f"Q{q_num}" for q_num, _ in non_grammar_questions[:5]])
                        raise ValueError(
                            f"CRITICAL GRAMMAR VIOLATION: {violation_percentage:.1f}% of questions ({len(non_grammar_questions)}/{len(questions)}) "
                            f"are non-grammar questions for grammar content. Violating questions: {violation_details}. "
                            f"ALL questions MUST be about grammar rules (nouns, verbs, tenses, sentence structure, etc.), "
                            f"NOT about poems, stories, characters, or literature. Please regenerate with grammar-only focus."
                        )
                    elif violation_percentage > 30:
                        print(f"   🚨 CRITICAL: Over 30% of questions are non-grammar. This violates grammar content grounding rules!")
                        print(f"   ⚠️  Recommendation: Regenerate with stricter grammar-only enforcement")
        
        # Check for generic/auto-assigned topics and source hints (indicates content not being used)
        generic_topics = ["Which of the", "What is the", "Who is the", "General", "Grammar Concept", "Grammar Concept (AI should specify from content)", ""]
        generic_hints = ["From provided study material", "Grammar content section (AI should specify exact location)", ""]
        content_grounding_issues = []
        
        for idx, q in enumerate(questions):
            topic = q.get('topic', '').strip()
            source_hint = q.get('source_hint', '').strip()
            
            if topic in generic_topics or source_hint in generic_hints:
                content_grounding_issues.append((idx + 1, topic, source_hint))
        
        if content_grounding_issues:
            print(f"\n⚠️  CONTENT GROUNDING WARNING:")
            print(f"   {len(content_grounding_issues)} questions have generic/auto-assigned topics or source hints")
            print(f"   This suggests questions may NOT be properly extracted from the [STUDY_MATERIAL]")
            print(f"   Generic values indicate AI may be using general knowledge instead of reading the content:")
            for q_num, topic, hint in content_grounding_issues[:10]:
                print(f"      Q{q_num}: topic='{topic}', source_hint='{hint}'")
            print(f"   ⚠️  Recommendation: AI should read the content and extract SPECIFIC topics and source locations")
        
        # Log sample questions for manual review
        print(f"\n📝 Sample Questions (first 3) for Content Grounding Review:")
        for idx, q in enumerate(questions[:3], 1):
            print(f"\n   Q{idx}: {q.get('question', 'N/A')[:100]}...")
            topic = q.get('topic', '❌ MISSING')
            source_hint = q.get('source_hint', '❌ MISSING')
            topic_status = "⚠️ GENERIC" if topic in generic_topics else "✅"
            hint_status = "⚠️ GENERIC" if source_hint in generic_hints else "✅"
            print(f"      Topic: {topic} {topic_status}")
            print(f"      Source Hint: {source_hint} {hint_status}")
            print(f"      Marks: {q.get('marks', 'N/A')}")
        
        print("="*80 + "\n")
        actual_count = len(questions)
        
        # Check if count matches expected
        expected_count = sum(item.get("count", 0) for item in distribution_list)
        print(f"Question count check: Expected={expected_count}, Got={actual_count}, Remaining={remaining_questions}")
        
        if actual_count < expected_count:
<<<<<<< HEAD
            print(f"⚠️  INFO: AI generated {actual_count} questions (target was {expected_count})")
            print(f"   This is acceptable - quality-first approach allows fewer questions if content is limited.")
            print(f"   Distribution target: {distribution_list}")
            print(f"   Total target: {expected_count}, Generated: {actual_count}, Difference: {expected_count - actual_count}")
=======
            print(f"INFO: AI generated {actual_count} high-quality questions (requested {expected_count})")
            print(f"   This is acceptable - quality over quantity. Content may not support more questions.")
            print(f"   Distribution requested: {distribution_list}")
            print(f"   Total expected: {expected_count}, Got: {actual_count}, Difference: {expected_count - actual_count}")
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
            
            # Check distribution breakdown
            if distribution_list:
                print(f"   Distribution breakdown:")
                for dist_item in distribution_list:
                    marks = dist_item.get('marks', 0)
                    count = dist_item.get('count', 0)
                    q_type = dist_item.get('type', 'unknown')
                    actual_for_this = len([q for q in questions if q.get('marks') == marks and q.get('type', '').lower() == q_type.lower()])
<<<<<<< HEAD
                    print(f"     - {count} questions of {marks} marks ({q_type}): Target {count}, Got {actual_for_this}")
            
            print(f"   Questions received: {[q.get('question', 'N/A')[:50] for q in questions]}")
            # Accept fewer questions - quality-first approach
            # No error raised - continue with what we have
            print(f"✅ Accepting {actual_count} questions (quality-first approach)")
=======
                    print(f"     - {count} questions of {marks} marks ({q_type}): Expected {count}, Got {actual_for_this}, Difference {count - actual_for_this}")
            
            print(f"   Questions received: {[q.get('question', 'N/A')[:50] for q in questions]}")
            # Accept the result - quality over quantity. Do not retry.
            # Store the actual count for frontend notification
            result["actual_question_count"] = actual_count
            result["requested_question_count"] = expected_count
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
        
        if actual_count != expected_count and actual_count != remaining_questions:
            print(f"Question count mismatch: Expected {expected_count}, Got {actual_count}, Remaining: {remaining_questions}")
            # If we got more than allowed, truncate
            if actual_count > remaining_questions:
                print(f"Truncating questions from {actual_count} to {remaining_questions}")
                questions = questions[:remaining_questions]
                result["questions"] = questions
            # If we got fewer, log it but keep what we have
        
        # Validate distribution matches
        if distribution_list:
        distribution_validation = _validate_distribution(questions, distribution_list)
        if not distribution_validation["valid"]:
            print(f"⚠️  Distribution mismatch: {distribution_validation['message']}")
                
                # Check for critical missing marks (10 marks, 5 marks)
                missing_marks = []
                for item in distribution_list:
                    marks = item.get("marks", 0)
                    q_type = item.get("type", "").lower()
                    count = item.get("count", 0)
                    actual_count = len([q for q in questions if q.get('marks') == marks and q.get('type', '').lower() == q_type])
                    if actual_count == 0 and count > 0:
                        missing_marks.append(f"{marks} marks ({q_type})")
                
                if missing_marks:
                    print(f"🚨 CRITICAL: Missing marks values: {', '.join(missing_marks)}")
                    print(f"🚨 The AI did not generate questions for these marks values - this violates the distribution requirement!")
                
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
            
            # Ensure topic and source_hint fields exist (for content grounding verification)
            generic_topics = ["Which of the", "What is the", "Who is the", "General", "Grammar Concept", ""]
            generic_hints = ["From provided study material", ""]
            
            current_topic = q.get("topic", "").strip()
            current_hint = q.get("source_hint", "").strip()
            
            if "topic" not in q or not current_topic or current_topic in generic_topics:
                print(f"⚠️  WARNING: Question {i+1} missing or generic 'topic' field - AI should have extracted this from content!")
                print(f"   Question: {q.get('question', 'N/A')[:80]}...")
                # Try to extract a meaningful topic from the question
                question_text = q.get("question", "")
                question_lower = question_text.lower()
                
                # Look for literature content (stories/poems/characters)
                literature_patterns = [
                    (r"['\"]([^'\"]+)['\"]", "story/poem name"),  # Extract quoted names
                    (r"story ['\"]([^'\"]+)['\"]", "story name"),
                    (r"poem ['\"]([^'\"]+)['\"]", "poem name"),
                    (r"character ([A-Z][a-z]+)", "character name"),
                ]
                
                extracted_topic = None
                
                # First, try to extract story/poem/character names
                for pattern, desc in literature_patterns:
                    match = re.search(pattern, question_text, re.IGNORECASE)
                    if match:
                        extracted_topic = match.group(1).strip()
                        if len(extracted_topic) > 2:  # Valid name
                            break
                
                # If no literature name found, look for mathematics concepts first
                if not extracted_topic:
                    # Check if it's a mathematics question
                    math_indicators = ['x²', 'x³', 'equation', 'formula', 'solve', 'find', 'calculate', 'discriminant', 'root', 'quadratic', 'linear', 'polynomial', 'algebra', 'geometry']
                    is_math = any(indicator in question_lower for indicator in math_indicators)
                    
                    if is_math:
                        # Mathematics topic detection
                        math_concepts = {
                            'quadratic equation': 'Quadratic Equations',
                            'quadratic formula': 'Quadratic Formula',
                            'discriminant': 'Discriminant',
                            'roots': 'Roots of Quadratic Equations',
                            'linear equation': 'Linear Equations',
                            'simultaneous equation': 'Simultaneous Equations',
                            'polynomial': 'Polynomial Equations',
                            'factorization': 'Factorization',
                            'algebra': 'Algebra',
                            'geometry': 'Geometry',
                            'trigonometry': 'Trigonometry',
                            'coordinate geometry': 'Coordinate Geometry',
                            'calculus': 'Calculus',
                        }
                        
                        # Check for specific math concepts
                        for keyword, topic in math_concepts.items():
                            if keyword in question_lower:
                                extracted_topic = topic
                                break
                        
                        # If still no topic, try to infer from equation type
                        if not extracted_topic:
                            if 'x²' in question_text or 'quadratic' in question_lower:
                                extracted_topic = 'Quadratic Equations'
                            elif 'x³' in question_text or 'polynomial' in question_lower:
                                extracted_topic = 'Polynomial Equations'
                            elif 'discriminant' in question_lower or 'd =' in question_lower or 'd=' in question_lower:
                                extracted_topic = 'Discriminant'
                            elif 'linear' in question_lower:
                                extracted_topic = 'Linear Equations'
                            else:
                                extracted_topic = 'Algebra'  # Default for math
                    else:
                        # Look for grammar concepts
                        grammar_concepts = {
                            'modal verb': 'Modal Verbs',
                            'past form': 'Past Tense Forms',
                            'phrasal verb': 'Phrasal Verbs',
                            'future tense': 'Future Tense',
                            'present continuous': 'Present Continuous Tense',
                            'negative form': 'Negative Forms',
                            'past perfect': 'Past Perfect Tense',
                            'compound sentence': 'Compound Sentences',
                            'future perfect': 'Future Perfect Tense',
                            'present perfect': 'Present Perfect Tense',
                            'passive voice': 'Passive Voice',
                            'simple past': 'Simple Past Tense',
                            'present tense': 'Present Tense',
                            'future continuous': 'Future Continuous Tense',
                            'interrogative form': 'Interrogative Forms',
                            'present perfect continuous': 'Present Perfect Continuous Tense',
                            'past continuous': 'Past Continuous Tense'
                        }
                        for keyword, topic in grammar_concepts.items():
                            if keyword in question_lower:
                                extracted_topic = topic
                                break
                
                # If still no topic, extract from question start (first few words) - but avoid for math
                if not extracted_topic:
                    # For math, don't extract random words - use a default
                    if any(indicator in question_lower for indicator in ['x²', 'x³', 'equation', 'formula', 'solve']):
                        extracted_topic = 'Mathematics Topic'  # Generic math topic
                    else:
                        # Remove question words and extract meaningful words
                        words = question_text.split()
                        # Skip common question starters
                        skip_words = {'what', 'who', 'which', 'where', 'when', 'why', 'how', 'is', 'are', 'was', 'were', 'the', 'a', 'an'}
                        meaningful_words = [w for w in words[:5] if w.lower() not in skip_words and len(w) > 2]
                        if meaningful_words:
                            extracted_topic = ' '.join(meaningful_words[:3])  # First 3 meaningful words
                
                q["topic"] = extracted_topic or "Content Topic (AI should specify from content)"
                print(f"   → Auto-assigned topic: {q['topic']} (⚠️ AI should have extracted this from content)")
            
            if "source_hint" not in q or not current_hint or current_hint in generic_hints:
                print(f"⚠️  WARNING: Question {i+1} missing or generic 'source_hint' field - AI should have referenced specific content location!")
                print(f"   Question: {q.get('question', 'N/A')[:80]}...")
                # Set a more specific source hint based on topic
                topic = q.get("topic", "")
                question_text = q.get("question", "")
                
                # Check content type
                is_literature = any(word in question_text.lower() for word in ['story', 'poem', 'poetry', 'character', 'author', 'poet', 'narrator'])
                is_math = any(word in question_text.lower() for word in ['x²', 'x³', 'equation', 'formula', 'solve', 'discriminant', 'quadratic', 'algebra'])
                
                if topic and topic != "Content Topic (AI should specify from content)" and topic != "Mathematics Topic":
                    if is_literature:
                        # For literature, use story/poem format
                        if any(word in topic.lower() for word in ['family', 'woman', 'zigzag', 'mulan', 'chaplin', 'sanyal', 'tie']):
                            q["source_hint"] = f"Story/Poem '{topic}'"
                        else:
                            q["source_hint"] = f"Story section about {topic}"
                    elif is_math:
                        # For mathematics, use chapter/section format
                        q["source_hint"] = f"Chapter/Section on {topic}"
                    else:
                        # For grammar, use section format
                        q["source_hint"] = f"Section on {topic}"
                else:
                    if is_math:
                        q["source_hint"] = "Mathematics section (AI should specify exact chapter/topic)"
                    else:
                        q["source_hint"] = "Content section (AI should specify exact location)"
                print(f"   → Auto-assigned source_hint: {q['source_hint']} (⚠️ AI should have referenced specific content section)")
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
        questions, has_format_repetition = _validate_exam_quality(questions, difficulty, target_language)
        count_after_validation = len(questions)
        print(f"Step 2 - After validation: {count_after_validation} questions")
        
<<<<<<< HEAD
        # QUALITY-FIRST: Accept questions even if format repetition detected
        # No retries - just log and accept
        if has_format_repetition:
            # Extract starters from questions to check variation
            question_starters_list = []
            for q in questions:
                question_text = q.get("question", "").strip()
                if question_text:
                    words = question_text.split()
                    if words:
                        question_starters_list.append(words[0].lower())
            
            unique_starters = len(set(question_starters_list)) if question_starters_list else 0
            total_questions = len(questions)
            
            print(f"⚠️  Format repetition detected ({unique_starters}/{total_questions} unique starters). Accepting questions anyway (quality-first approach).")
            # Don't raise error - accept questions
=======
        # Remove duplicate questions (exact or very similar)
        questions = _remove_duplicate_questions(questions)
        count_after_dedup = len(questions)
        if count_after_dedup < count_after_validation:
            print(f"Removed {count_after_validation - count_after_dedup} duplicate question(s). Remaining: {count_after_dedup}")
        
        # Log format repetition but don't retry - accept the result
            if has_format_repetition:
            print(f"INFO: Format repetition detected but accepting questions. Quality over quantity.")
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
        
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
        
<<<<<<< HEAD
        # Final count check (QUALITY-FIRST: Accept whatever we have)
        final_count = len(questions)
        if final_count != expected_count:
            print(f"ℹ️  FINAL COUNT: Generated {final_count} questions (requested {expected_count}). Accepting for quality-first approach.")
=======
        # Final count check - accept quality questions, don't raise errors
        final_count = len(questions)
        if final_count != expected_count:
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
            if final_count < expected_count:
                print(f"INFO: Final count: Generated {final_count} quality questions (requested {expected_count})")
                print(f"   Accepting result - quality over quantity. Content may not support more questions.")
        else:
<<<<<<< HEAD
            print(f"✅ FINAL COUNT: Generated {final_count} questions (as requested)")
        
        # Never raise error for count mismatch - accept what we have (quality-first)
=======
                print(f"INFO: Final count: Generated {final_count} questions (requested {expected_count})")
                # Truncate to expected count if we got more
                questions = questions[:expected_count]
        final_count = len(questions)
        else:
            print(f"INFO: Final count: Exactly {final_count} questions (as requested)")
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
        
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
            
            # If similarity is very high (>90%), consider it a duplicate (increased from 80% to be less aggressive)
            if similarity > 0.9:
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
            
            # If similarity is very high (>90%), it's a duplicate (increased from 80% to be less aggressive)
            if similarity > 0.9:
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

