"""
Post-processing module for 10-mark math questions.
Converts LaTeX to board-style exam format for teacher trust.
"""
import re
from typing import Any, Dict, List


def remove_latex(text: str) -> str:
    """Remove LaTeX delimiters and convert to exam-friendly notation"""
    if not text or not isinstance(text, str):
        return text
    
    # Remove LaTeX inline math delimiters \( and \)
    text = re.sub(r'\\\(', '', text)
    text = re.sub(r'\\\)', '', text)
    
    # Remove LaTeX display math delimiters \[ and \]
    text = re.sub(r'\\\[', '', text)
    text = re.sub(r'\\\]', '', text)
    
    # Convert LaTeX fractions \frac{a}{b} to a/b or (a)/(b)
    def replace_frac(match):
        num = match.group(1)
        den = match.group(2)
        # Use parentheses if numerator or denominator has operations
        if any(op in num for op in ['+', '-', '*', '/']) or any(op in den for op in ['+', '-', '*', '/']):
            return f"({num})/({den})"
        return f"{num}/{den}"
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', replace_frac, text)
    
    # Convert LaTeX sqrt \sqrt{x} to √x or sqrt(x)
    def replace_sqrt(match):
        content = match.group(1)
        if len(content) > 3 or any(op in content for op in ['+', '-', '*', '/']):
            return f"√({content})"
        return f"√{content}"
    text = re.sub(r'\\sqrt\{([^}]+)\}', replace_sqrt, text)
    
    # Convert LaTeX powers x^{n} to x^n
    text = re.sub(r'\^\{([^}]+)\}', r'^\1', text)
    
    # Remove \times and replace with ×
    text = text.replace('\\times', '×')
    
    # Remove \div and replace with ÷
    text = text.replace('\\div', '÷')
    
    # Remove \boxed{...} and extract content
    text = re.sub(r'\\boxed\{([^}]+)\}', r'\1', text)
    
    # Remove \text{...} and extract content
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    
    # Remove \pm and replace with ±
    text = text.replace('\\pm', '±')
    
    # Remove \mp and replace with ∓
    text = text.replace('\\mp', '∓')
    
    # Clean up any remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def convert_to_board_style(answer: Any, marks: int) -> Dict[str, Any]:
    """Convert structured answer to board-style format for 10-mark questions"""
    if marks != 10:
        return answer
    
    if isinstance(answer, dict):
        # Extract components
        given = answer.get("given", "")
        formula = answer.get("formula", "")
        definition = answer.get("definition", "")
        coefficients = answer.get("coefficients", "")
        steps = answer.get("steps", [])
        function_values = answer.get("function_values", [])
        final = answer.get("final", "")
        
        # Remove LaTeX from all components
        given = remove_latex(given) if given else ""
        formula = remove_latex(formula) if formula else ""
        definition = remove_latex(definition) if definition else ""
        coefficients = remove_latex(coefficients) if coefficients else ""
        steps = [remove_latex(str(step)) for step in steps] if steps else []
        function_values = [remove_latex(str(val)) for val in function_values] if function_values else []
        final = remove_latex(final) if final else ""
        
        # Remove "Final Answer:" prefix if present (we'll add it in the structure)
        final = re.sub(r'^Final Answer:\s*', '', final, flags=re.IGNORECASE).strip()
        
        # Build substitution from coefficients or extract from steps
        substitution = ""
        if coefficients:
            substitution = f"Substituting: {coefficients}"
        elif steps:
            # Try to extract substitution from first step
            first_step = steps[0] if steps else ""
            if "=" in first_step and any(char in first_step for char in ['a', 'b', 'c', 'x', 'y']):
                substitution = first_step
        
        # Build calculation from steps
        calculation = ""
        if steps:
            calculation = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
            if function_values:
                calculation += "\n\nFunction Values:\n" + "\n".join([f"  • {val}" for val in function_values])
        
        # Restructure as board-style format
        board_format = {}
        
        if given:
            board_format["given"] = given
        
        if formula:
            board_format["formula"] = formula
        elif definition:
            # Use definition as formula if formula is missing
            board_format["formula"] = definition
        
        if substitution:
            board_format["substitution"] = substitution
        
        if calculation:
            board_format["calculation"] = calculation
        
        if final:
            board_format["final_answer"] = f"Final Answer: {final}"
        else:
            # Extract final answer from last step if available
            if steps:
                last_step = steps[-1]
                # Try to extract answer from last step
                if "=" in last_step:
                    parts = last_step.split("=")
                    if len(parts) > 1:
                        board_format["final_answer"] = f"Final Answer: {parts[-1].strip()}"
        
        return board_format
    
    elif isinstance(answer, str):
        # Convert string answer to board format
        cleaned = remove_latex(answer)
        return {
            "given": "",
            "formula": "",
            "substitution": "",
            "calculation": cleaned,
            "final_answer": f"Final Answer: {cleaned}"
        }
    
    return answer


def post_process_10mark_math(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Post-process 10-mark math questions to convert LaTeX to board-style exam format.
    
    For 10-mark math questions:
    - Removes LaTeX symbols
    - Converts formulas into board-style writing
    - Structures answers as: Given, Formula, Substitution, Calculation, Final Answer
    
    This increases trust among teachers by making answers look like student-written exam scripts.
    """
    processed_questions = []
    
    for q in questions:
        marks = q.get("marks", 0)
        q_type = q.get("type", "")
        
        # Only process 10-mark descriptive questions (likely math)
        if marks == 10 and q_type == "descriptive":
            correct_answer = q.get("correct_answer")
            if correct_answer:
                # Check if it's a math question (has formulas, equations, etc.)
                answer_str = str(correct_answer).lower()
                math_indicators = ["f(x)", "f'(x)", "derivative", "integral", "=", "x²", "x^2", "sqrt", "formula", "equation"]
                
                if any(indicator in answer_str for indicator in math_indicators):
                    print(f"🔄 Post-processing 10-mark math question: Converting LaTeX to board-style format")
                    q["correct_answer"] = convert_to_board_style(correct_answer, marks)
        
        processed_questions.append(q)
    
    return processed_questions


