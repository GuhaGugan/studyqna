# Subject-Wise Answer Structure Implementation

## ✅ Implementation Complete

The application now enforces **subject-specific answer structures** based on the detected subject from the uploaded content.

---

## 📚 **Subject Detection**

The system automatically detects the subject from the uploaded text content using keyword analysis:

### **Detection Logic:**
- **Mathematics**: Detects math keywords (equation, formula, calculate, solve, derivative, algebra, etc.)
- **English**: Detects literature keywords (poem, poetry, novel, character, theme, metaphor, etc.)
- **Science**: Detects science keywords (atom, molecule, physics, biology, experiment, etc.)
- **Social Science**: Detects social science keywords (history, geography, civics, economics, etc.)
- **General**: Default fallback if no clear subject detected

### **Detection Function:**
- Location: `backend/app/ai_service.py`
- Function: `detect_subject(text_content: str) -> str`
- Returns: `"mathematics"`, `"english"`, `"science"`, `"social_science"`, or `"general"`

---

## 📋 **Subject-Wise Answer Structure Rules**

### **1. MATHEMATICS**

**Headings to USE:**
- ✅ Given
- ✅ Formula
- ✅ Calculation / Steps
- ✅ Final Answer

**Format:**
- Show step-by-step working
- Use mathematical reasoning
- Use LaTeX for all mathematical expressions
- Numbered steps for 5+ marks

**Example:**
```
Given: f(x) = 2x² + 3x + 1

Formula: x = (-b ± √(b² - 4ac)) / (2a)

Calculation / Steps:
Step 1: D = b² - 4ac = 3² - 4(2)(1) = 1
Step 2: x = (-3 ± √1) / 4 = (-3 ± 1) / 4

Final Answer: x = -1/2, -1
```

**DO NOT USE:**
- ❌ Introduction, Explanation, Analysis, Conclusion (these are for other subjects)

---

### **2. ENGLISH (Literature/Language)**

**Headings to USE:**
- ✅ Introduction
- ✅ Explanation
- ✅ Analysis
- ✅ Conclusion

**Format:**
- Write in paragraph form
- Use literary terms (theme, tone, irony, humor, metaphor, simile, etc.)
- Answer must read like a literature exam answer

**Example:**
```
Introduction: The poem explores themes of nature and human connection.

Explanation: The poet uses vivid imagery to depict natural scenes, creating a sense of harmony between humans and the environment.

Analysis: Literary devices such as metaphor and personification enhance the emotional impact, allowing readers to connect deeply with the poet's message.

Conclusion: The poem effectively conveys the relationship between humans and nature through its masterful use of language and imagery.
```

**DO NOT USE:**
- ❌ Given, Formula, Calculation (these are for Mathematics only)

---

### **3. SCIENCE (Theory - Physics, Chemistry, Biology)**

**Headings to USE:**
- ✅ Definition
- ✅ Explanation
- ✅ Example (if needed)
- ✅ Conclusion

**Format:**
- Focus on scientific concepts and principles
- Include relevant examples or applications
- Clear scientific explanations

**Example:**
```
Definition: Photosynthesis is the process by which plants convert light energy into chemical energy.

Explanation: This process occurs in chloroplasts and involves two main stages: light-dependent reactions and light-independent reactions (Calvin cycle).

Example: For instance, green plants use sunlight, water, and carbon dioxide to produce glucose and oxygen, which is essential for life on Earth.

Conclusion: Photosynthesis is crucial for maintaining the oxygen-carbon dioxide balance in the atmosphere.
```

**DO NOT USE:**
- ❌ Given, Formula, Calculation (unless it's a calculation-based science question)

---

### **4. SOCIAL SCIENCE (History, Geography, Civics, Economics)**

**Headings to USE:**
- ✅ Background / Context
- ✅ Key Points
- ✅ Explanation
- ✅ Conclusion

**Format:**
- Provide historical/geographical context
- List key points clearly
- Explain relationships and causes
- Structured presentation

**Example:**
```
Background / Context: The Industrial Revolution began in Britain in the late 18th century, marking a significant shift from agrarian to industrial society.

Key Points:
- Introduction of machinery and factories
- Urbanization and migration to cities
- Changes in social and economic structures

Explanation: The revolution transformed production methods, leading to increased efficiency and economic growth, but also brought challenges such as poor working conditions and social inequality.

Conclusion: The Industrial Revolution had lasting impacts on society, economy, and technology, shaping the modern world.
```

**DO NOT USE:**
- ❌ Given, Formula, Calculation (these are for Mathematics only)

---

## 📏 **Mark-Based Length Control**

**Marks control LENGTH only (regardless of subject):**
- **1 mark** → one sentence (1-2 lines)
- **2 marks** → short paragraph (2-3 lines)
- **5 marks** → explained answer (7-9 lines)
- **10 marks** → detailed, structured answer (9-10 lines minimum)

**Subject controls FORMAT (headings and structure):**
- Mathematics: Given, Formula, Calculation/Steps, Final Answer
- English: Introduction, Explanation, Analysis, Conclusion
- Science: Definition, Explanation, Example, Conclusion
- Social Science: Background/Context, Key Points, Explanation, Conclusion

---

## 🔧 **Implementation Details**

### **Files Modified:**

1. **`backend/app/ai_service.py`**:
   - Added `detect_subject()` function (lines ~18-100)
   - Updated `SYSTEM_PROMPT` with subject-wise rules (lines ~19-945)
   - Updated `user_prompt` to include detected subject and subject-specific instructions
   - Made math formatting rules conditional on subject

### **Key Changes:**

1. **Subject Detection**:
   ```python
   detected_subject = detect_subject(text_content)
   ```

2. **Subject-Specific Instructions**:
   - Added subject instruction blocks for each subject type
   - Instructions are dynamically inserted into the AI prompt

3. **Conditional Formatting**:
   - Math formatting rules only appear for mathematics
   - Subject-appropriate examples shown based on detected subject

---

## ✅ **How It Works**

1. **User uploads content** (PDF/Image)
2. **System extracts text** from the content
3. **Subject is detected** automatically using keyword analysis
4. **AI prompt includes** subject-specific answer structure rules
5. **AI generates questions** following subject-appropriate format
6. **Answers use** subject-specific headings and structure

---

## 🎯 **Examples**

### **Mathematics Example:**
```
Question: Solve the quadratic equation x² + 5x + 6 = 0

Answer:
Given: x² + 5x + 6 = 0
Formula: x = (-b ± √(b² - 4ac)) / (2a)
Calculation / Steps:
  Step 1: D = b² - 4ac = 25 - 24 = 1
  Step 2: x = (-5 ± 1) / 2
Final Answer: x = -2 or x = -3
```

### **English Example:**
```
Question: Analyze the theme of the poem and discuss its literary devices.

Answer:
Introduction: The poem explores themes of nature and human connection.

Explanation: The poet uses vivid imagery to depict natural scenes, creating a sense of harmony.

Analysis: Literary devices such as metaphor and personification enhance the emotional impact.

Conclusion: The poem effectively conveys the relationship between humans and nature.
```

### **Science Example:**
```
Question: Explain the process of photosynthesis.

Answer:
Definition: Photosynthesis is the process by which plants convert light energy into chemical energy.

Explanation: This process occurs in chloroplasts and involves two main stages: light-dependent and light-independent reactions.

Example: Green plants use sunlight, water, and carbon dioxide to produce glucose and oxygen.

Conclusion: Photosynthesis is crucial for maintaining the oxygen-carbon dioxide balance.
```

### **Social Science Example:**
```
Question: Discuss the causes and effects of the Industrial Revolution.

Answer:
Background / Context: The Industrial Revolution began in Britain in the late 18th century.

Key Points:
- Introduction of machinery and factories
- Urbanization and migration
- Changes in social structures

Explanation: The revolution transformed production methods, leading to economic growth but also social challenges.

Conclusion: The Industrial Revolution had lasting impacts on society and technology.
```

---

## 🚨 **Strict Rules**

1. **If subject is NOT Mathematics:**
   - ❌ DO NOT use math-style headings (Given, Formula, Calculation)
   - ✅ Use subject-appropriate headings

2. **If subject IS Mathematics:**
   - ✅ Use math-style headings (Given, Formula, Calculation/Steps, Final Answer)
   - ❌ DO NOT use literature-style headings (Introduction, Explanation, Analysis, Conclusion)

3. **Marks control LENGTH, Subject controls FORMAT**

---

## 📊 **Detection Accuracy**

The subject detection uses keyword counting:
- Counts matches for each subject category
- Returns subject with highest count
- Falls back to "general" if no clear match
- Checks for mathematical symbols as secondary indicator

**Improvement Suggestions:**
- Can be enhanced with ML-based classification
- Can allow manual subject selection in UI
- Can use more sophisticated keyword matching

---

## ✅ **Status**

**Implementation**: ✅ Complete
**Testing**: ⚠️ Needs testing with different subjects
**Documentation**: ✅ Complete

---

*Last Updated: December 2024*
*File: `backend/app/ai_service.py`*


