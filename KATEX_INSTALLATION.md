# KaTeX Installation Guide

## Frontend Installation

To use KaTeX for proper LaTeX rendering, install the required packages:

```bash
cd frontend
npm install katex react-katex
```

## What Changed

1. **AI Prompt Updated**: Now returns structured JSON with `steps` array instead of text with `\n`
2. **Frontend Rendering**: Uses KaTeX (react-katex) instead of MathJax
3. **Marks-Based Rendering**:
   - 1 mark: Plain text
   - 2 marks: InlineMath
   - 5+ marks: BlockMath + steps array
   - 10 marks: BlockMath + steps + derivation

## Benefits

- ✅ No more "Math input error" in PDFs
- ✅ Consistent rendering across web and PDF
- ✅ Better performance (KaTeX is faster than MathJax)
- ✅ Structured data (no parsing needed)
- ✅ No newline handling issues

## Next Steps

1. Run `npm install katex react-katex` in the frontend directory
2. Restart the frontend dev server
3. Test question generation - LaTeX should render correctly


