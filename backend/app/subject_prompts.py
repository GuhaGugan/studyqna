"""
Subject-specific AI prompts for Q/A generation.
Each subject has its own formatting rules and answer structure requirements.
"""

# Mathematics-specific prompt rules
MATHEMATICS_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
MATHEMATICS SUBJECT RULES (MANDATORY)
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
"""

# English-specific prompt rules
ENGLISH_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
ENGLISH SUBJECT RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

🚨 CRITICAL: This is ENGLISH - Follow these rules STRICTLY:

1. ANSWER FORMAT (MANDATORY):
   ✅ USE these headings:
      - Introduction
      - Explanation
      - Analysis
      - Conclusion
   
   ❌ NEVER use:
      - Given
      - Formula
      - Calculation
      - Steps
      - Substitution

2. WRITING STYLE:
   ✅ Write in paragraph form
   ✅ Use literary terms (theme, tone, irony, humor, metaphor, simile, etc.)
   ✅ Answer must read like a literature exam answer
   ✅ Focus on interpretation, analysis, and critical thinking

3. QUESTION TYPES:
   ✅ Literature analysis questions
   ✅ Grammar and language questions
   ✅ Comprehension questions
   ✅ Essay-style questions

4. ANSWER LENGTH (by marks):
   - 1 mark: 1-2 lines (direct answer)
   - 2 marks: 2-3 lines (brief explanation)
   - 5 marks: 7-9 lines (detailed explanation with examples)
   - 10 marks: 12-15+ lines (comprehensive analysis)
"""

# Science-specific prompt rules
SCIENCE_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
SCIENCE SUBJECT RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

🚨 CRITICAL: This is SCIENCE - Follow these rules STRICTLY:

1. ANSWER FORMAT (MANDATORY):
   ✅ USE these headings:
      - Definition
      - Explanation
      - Example (if needed)
      - Conclusion
   
   ❌ NEVER use (unless calculation-based):
      - Given
      - Formula
      - Calculation
      - Steps

2. CONTENT FOCUS:
   ✅ Scientific concepts and principles
   ✅ Include relevant examples or applications
   ✅ Use scientific terminology correctly
   ✅ Explain cause-and-effect relationships

3. CALCULATION-BASED QUESTIONS:
   ✅ If question involves calculation, use:
      - Given
      - Formula
      - Substitution
      - Calculation
      - Final Answer

4. ANSWER LENGTH (by marks):
   - 1 mark: 1-2 lines (definition or direct answer)
   - 2 marks: 2-3 lines (brief explanation)
   - 5 marks: 7-9 lines (detailed explanation with examples)
   - 10 marks: 12-15+ lines (comprehensive explanation)
"""

# Social Science-specific prompt rules
SOCIAL_SCIENCE_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
SOCIAL SCIENCE SUBJECT RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

🚨 CRITICAL: This is SOCIAL SCIENCE - Follow these rules STRICTLY:

1. ANSWER FORMAT (MANDATORY):
   ✅ USE these headings:
      - Background / Context
      - Key Points
      - Explanation
      - Conclusion
   
   ❌ NEVER use:
      - Given
      - Formula
      - Calculation
      - Steps

2. CONTENT FOCUS:
   ✅ Historical/geographical context
   ✅ List key points clearly
   ✅ Explain relationships and causes
   ✅ Provide examples from history/geography/civics/economics

3. ANSWER LENGTH (by marks):
   - 1 mark: 1-2 lines (direct answer)
   - 2 marks: 2-3 lines (brief explanation)
   - 5 marks: 7-9 lines (detailed explanation with context)
   - 10 marks: 12-15+ lines (comprehensive analysis with background)
"""

# Tamil-specific prompt rules
TAMIL_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
TAMIL SUBJECT RULES (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━

🚨 CRITICAL: This is TAMIL - Follow these rules STRICTLY:

1. ANSWER FORMAT (MANDATORY):
   ✅ USE these headings:
      - அறிமுகம் (Introduction)
      - விளக்கம் (Explanation)
      - பகுப்பாய்வு (Analysis)
      - முடிவு (Conclusion)
   
   ❌ NEVER use:
      - Given
      - Formula
      - Calculation
      - Steps
      - Substitution

2. WRITING STYLE:
   ✅ Write in Tamil (exam-style Tamil, not spoken Tamil)
   ✅ Use literary terms where applicable
   ✅ Answer must read like a Tamil literature exam answer
   ✅ Focus on interpretation, analysis, and critical thinking in Tamil

3. QUESTION TYPES:
   ✅ Tamil literature analysis questions
   ✅ Grammar and language questions
   ✅ Comprehension questions
   ✅ Essay-style questions in Tamil

4. ANSWER LENGTH (by marks):
   - 1 mark: 1-2 lines (direct answer in Tamil)
   - 2 marks: 2-3 lines (brief explanation in Tamil)
   - 5 marks: 7-9 lines (detailed explanation with examples in Tamil)
   - 10 marks: 12-15+ lines (comprehensive analysis in Tamil)

5. LANGUAGE RULES:
   ✅ Use exam-style Tamil phrasing (not spoken Tamil)
   ✅ Use proper Tamil grammar and vocabulary
   ✅ Follow Tamil exam paper conventions
"""

# General subject prompt rules (fallback)
GENERAL_PROMPT_RULES = """
━━━━━━━━━━━━━━━━━━━━━━
GENERAL SUBJECT RULES
━━━━━━━━━━━━━━━━━━━━━━

For general subjects, use appropriate format based on content:
- If mathematical content detected: Use Mathematics structure
- If literature/English content: Use English structure
- If Tamil content detected: Use Tamil structure
- If science content: Use Science structure
- If social science content: Use Social Science structure
"""

def get_subject_prompt_rules(subject: str) -> str:
    """
    Get subject-specific prompt rules.
    
    Args:
        subject: Subject name (mathematics, english, tamil, science, social_science, general)
    
    Returns:
        Subject-specific prompt rules string
    """
    subject_lower = subject.lower() if subject else "general"
    
    if subject_lower == "mathematics":
        return MATHEMATICS_PROMPT_RULES
    elif subject_lower == "english":
        return ENGLISH_PROMPT_RULES
    elif subject_lower == "tamil":
        return TAMIL_PROMPT_RULES
    elif subject_lower == "science":
        return SCIENCE_PROMPT_RULES
    elif subject_lower == "social_science":
        return SOCIAL_SCIENCE_PROMPT_RULES
    else:
        return GENERAL_PROMPT_RULES

