# Difficulty Level Rules - Easy, Medium, Hard

## 📋 Current Implementation

The application follows specific rules for defining **Easy**, **Medium**, and **Hard** difficulty levels. These rules are embedded in the AI system prompt and control how questions are generated.

---

## 🎯 **Current Difficulty Definitions**

### **1. General Difficulty Rules** (Lines 969-973 in `ai_service.py`)

```
=== DIFFICULTY MODE (STRICT - MUST FOLLOW) ===
Difficulty Level: {difficulty}
- Easy: Basic understanding, direct answers
- Medium: Application of concepts, step-wise solutions
- Hard: Deep understanding, full derivations
```

**Explanation:**
- **Easy**: Tests basic recall and understanding. Direct, straightforward questions.
- **Medium**: Requires applying concepts. Step-by-step solutions needed.
- **Hard**: Tests deep understanding. Full derivations and comprehensive explanations required.

---

### **2. Answer Structure Rules** (Lines 1036-1038)

**For Mathematics Questions:**
- **Easy**: Direct answer with formula (1-2 lines)
- **Medium**: Show steps with formulas (3-6 lines)
- **Hard**: Complete derivation with step numbering and clear final answer (8-15 lines)

**For General Questions:**
- **Easy**: 1-2 lines (basic factual answer)
- **Medium**: 3-6 lines (application with steps)
- **Hard**: 8-15 lines (comprehensive explanation)

---

### **3. Marks-Based Difficulty Scaling** (Line 1118)

The difficulty level **scales with marks**:

| Marks | Easy | Medium | Hard |
|-------|------|--------|------|
| **1 mark** | 1-2 lines | 1-2 lines | 1-2 lines |
| **2 marks** | 2-3 lines | 2-3 lines | 2-3 lines |
| **3 marks** | 4-5 lines | 4-5 lines | 4-5 lines |
| **5 marks** | 6-8 lines | 6-8 lines | 6-8 lines |
| **10 marks** | 10-15 lines | 12-15 lines | 12-15+ lines |

**Key Point**: Higher marks = longer answers, but difficulty affects the **complexity** and **depth** of the answer, not just length.

---

## 📊 **Detailed Difficulty Rules by Question Type**

### **EASY Difficulty**

**Question Characteristics:**
- ✅ Direct, factual questions
- ✅ Simple recall of definitions
- ✅ Basic calculations
- ✅ One-step solutions
- ✅ No complex reasoning required

**Answer Format:**
- ✅ Direct answer (1-2 lines for 1-2 marks)
- ✅ Simple formula application (no derivation)
- ✅ No step-by-step working required
- ✅ Straightforward explanation

**Examples:**
- "What is 2 + 3?" → "5" (1 mark, Easy)
- "Define X." → "X is Y." (1-2 marks, Easy)
- "Solve x + 5 = 10" → "x = 5" (2 marks, Easy)

---

### **MEDIUM Difficulty**

**Question Characteristics:**
- ✅ Application of concepts
- ✅ Multi-step problems
- ✅ Requires understanding relationships
- ✅ Moderate complexity
- ✅ Some reasoning needed

**Answer Format:**
- ✅ Step-by-step solution (3-6 lines)
- ✅ Show formulas and substitutions
- ✅ Brief explanations
- ✅ Working shown clearly

**Examples:**
- "Given f(x) = 2x² + 3x + 1, find the roots." → Shows quadratic formula, substitution, calculation (5 marks, Medium)
- "Explain the concept of X and its importance." → 4-5 lines with examples (3 marks, Medium)
- "Calculate the area of a circle with radius 5." → Shows formula, substitution, answer (2 marks, Medium)

---

### **HARD Difficulty**

**Question Characteristics:**
- ✅ Deep conceptual understanding
- ✅ Complex multi-step problems
- ✅ Requires full derivation/proof
- ✅ Analysis and reasoning
- ✅ Exam-tricky questions

**Answer Format:**
- ✅ Complete derivation (8-15 lines)
- ✅ Step numbering mandatory (Step 1, Step 2, ...)
- ✅ Full logical reasoning
- ✅ Comprehensive explanation
- ✅ Clear final answer with conclusion

**Examples:**
- "Analyze the function f(x) = 3x³ - 6x² + 2. Find critical points and determine their nature." → Full derivation with steps, analysis, conclusion (10 marks, Hard)
- "Prove that X = Y using mathematical induction." → Complete proof with all steps (10 marks, Hard)
- "Comprehensively explain the relationship between X and Y with examples." → 12-15 lines with detailed analysis (10 marks, Hard)

---

## 🔄 **Difficulty Scaling with Marks**

The difficulty level **interacts with marks** to determine answer complexity:

### **1 Mark Questions:**
- **Easy**: Direct answer, no explanation
- **Medium**: Brief explanation (1-2 lines)
- **Hard**: Slightly more detailed (1-2 lines, but more precise)

### **2 Mark Questions:**
- **Easy**: Simple formula application
- **Medium**: Formula + brief working
- **Hard**: Formula + detailed working

### **3 Mark Questions:**
- **Easy**: Basic explanation (4-5 lines)
- **Medium**: Explanation with examples (4-5 lines)
- **Hard**: Detailed explanation with analysis (4-5 lines)

### **5 Mark Questions:**
- **Easy**: Step-wise solution (6-8 lines)
- **Medium**: Step-wise with reasoning (6-8 lines)
- **Hard**: Step-wise with full derivation (6-8 lines)

### **10 Mark Questions:**
- **Easy**: Comprehensive answer (10-15 lines)
- **Medium**: Comprehensive with analysis (12-15 lines)
- **Hard**: Full derivation with proof/analysis (12-15+ lines)

---

## 📝 **Current Rules Summary**

### **What We're Following:**

1. ✅ **Basic Definitions**: Easy = basic, Medium = application, Hard = deep understanding
2. ✅ **Answer Length**: Scales with marks (1 mark = 1-2 lines, 10 marks = 12-15+ lines)
3. ✅ **Complexity**: Difficulty affects complexity, not just length
4. ✅ **Step Requirements**: Hard questions require numbered steps
5. ✅ **Derivation**: Hard questions require full derivations

### **What Could Be Enhanced:**

1. ⚠️ **Question Complexity**: No explicit rules for question complexity based on difficulty
2. ⚠️ **Concept Depth**: No clear definition of "deep understanding" vs "basic understanding"
3. ⚠️ **Problem Types**: No specific problem types assigned to each difficulty
4. ⚠️ **Reasoning Level**: No explicit reasoning complexity rules

---

## 💡 **Recommendations for Enhancement**

If you want to make the difficulty levels more explicit and consistent, consider adding:

### **Enhanced Easy Rules:**
- Direct recall questions only
- Single concept testing
- No multi-step reasoning
- Straightforward calculations
- Definition-based questions

### **Enhanced Medium Rules:**
- Application of 1-2 concepts
- 2-3 step problems
- Requires understanding relationships
- Moderate complexity calculations
- Comparison/contrast questions

### **Enhanced Hard Rules:**
- Multiple concepts integration
- 4+ step problems
- Requires analysis and synthesis
- Complex calculations with reasoning
- Proof/derivation questions
- Exam-tricky scenarios

---

## 🔍 **Where Rules Are Defined**

**File**: `backend/app/ai_service.py`

**Key Sections:**
1. **Lines 969-973**: Basic difficulty definitions
2. **Lines 1036-1038**: Answer structure for math questions
3. **Line 1118**: Difficulty-based answer structure
4. **Lines 1040-1043**: Hard question requirements

---

## ✅ **Current Status**

**Working**: ✅ Yes, the rules are implemented and working
**Clear**: ⚠️ Basic rules are clear, but could be more detailed
**Consistent**: ✅ Rules are consistent across the codebase
**Enforced**: ✅ Rules are enforced in the AI prompt

---

## 🚀 **Next Steps (Optional)**

If you want to enhance the difficulty rules, I can:

1. **Add more detailed difficulty definitions** to the AI prompt
2. **Create explicit question complexity rules** for each difficulty
3. **Add difficulty-based problem type guidelines**
4. **Enhance validation** to check difficulty compliance
5. **Add difficulty indicators** in the UI

Would you like me to enhance these rules?

---

*Last Updated: December 2024*
*File: `backend/app/ai_service.py`*


