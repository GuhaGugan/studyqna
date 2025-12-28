"""
AI Pipeline for Q/A Generation
Two-step process: Concept Extraction -> Q/A Generation
This improves accuracy and reduces costs compared to single-step generation.
"""

from typing import Dict, List, Any, Optional
from app.ai_service import get_openai_client, _validate_exam_quality, detect_subject
import json


def extract_concepts(
    text_content: str,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Step 1: Extract and validate concepts from text content (cheap AI call)
    
    Uses a cheaper model (gpt-3.5-turbo) to extract key concepts that will be used
    for question generation. This ensures concepts are accurate and validated before
    generating questions.
    
    Args:
        text_content: Text to extract concepts from
        subject: Optional subject hint (mathematics, english, science, etc.)
    
    Returns:
        Dict with validated concepts list and metadata
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI API key not configured")
    
    # Detect or use provided subject
    if subject and subject != "general":
        detected_subject = subject.lower()
    else:
        detected_subject = detect_subject(text_content)
    
    # Use cheaper model for concept extraction
    model = "gpt-3.5-turbo"
    
    # Adaptive content limit for concept extraction
    # gpt-3.5-turbo has 16,385 token limit
    # From error: 30K chars = 38K tokens, so ratio is ~1.27 tokens/char
    # 16,385 tokens / 1.27 ≈ 12,900 chars, but we need room for prompt (~3-4K tokens)
    # Safe limit: ~10,000 chars (≈12.7K tokens for content + ~3.7K for prompt/response)
    concept_extraction_limit = min(len(text_content), 10000)
    text_for_concepts = text_content[:concept_extraction_limit]
    
    if len(text_content) > concept_extraction_limit:
        print(f"📚 Concept extraction: Using {concept_extraction_limit:,} of {len(text_content):,} chars for concept extraction")
    else:
        print(f"📚 Concept extraction: Using all {len(text_content):,} chars for concept extraction")
    
    # Shorter prompt to save tokens - reduced from ~500 tokens to ~100 tokens
    prompt = f"""Extract key concepts from this {detected_subject} text. Return JSON array only.

Text:
{text_for_concepts}

Format: [{{"concept": "Name", "description": "Brief", "key_points": ["Point"]}}]"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert educational content analyzer. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up JSON (remove markdown code blocks if present)
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        concepts = json.loads(content)
        
        if not isinstance(concepts, list):
            raise ValueError("Concepts must be a list")
        
        # Validate concepts structure
        validated_concepts = []
        for idx, concept in enumerate(concepts):
            if not isinstance(concept, dict):
                print(f"⚠️  Skipping invalid concept {idx}: not a dict")
                continue
            
            if "concept" not in concept:
                print(f"⚠️  Skipping invalid concept {idx}: missing 'concept' field")
                continue
            
            validated_concepts.append({
                "concept": str(concept.get("concept", "")),
                "description": str(concept.get("description", "")),
                "key_points": concept.get("key_points", []) if isinstance(concept.get("key_points"), list) else []
            })
        
        print(f"✅ Extracted {len(validated_concepts)} validated concepts")
        
        return {
            "concepts": validated_concepts,
            "subject": detected_subject,
            "total_concepts": len(validated_concepts)
        }
    
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse concepts JSON: {e}")
        print(f"   Raw response: {content[:500]}")
        # Fallback: return empty concepts (will use full text in Step 2)
        return {
            "concepts": [],
            "subject": detected_subject,
            "total_concepts": 0,
            "error": "Failed to extract concepts, will use full text"
        }
    except Exception as e:
        print(f"❌ Error in concept extraction: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return empty concepts
        return {
            "concepts": [],
            "subject": detected_subject,
            "total_concepts": 0,
            "error": str(e)
        }


def generate_qa_from_concepts(
    text_content: str,
    concepts_data: Dict[str, Any],
    difficulty: str,
    qna_type: str,
    num_questions: int,
    marks_pattern: str = "mixed",
    target_language: str = "english",
    distribution_list: Optional[List[Dict[str, Any]]] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Step 2: Generate Q/A using validated concepts (controlled AI call)
    
    Uses the validated concepts from Step 1 to generate accurate questions and answers.
    This ensures questions are based on actual concepts rather than AI guesses.
    
    Args:
        text_content: Original text content
        concepts_data: Output from extract_concepts() containing validated concepts
        difficulty: Difficulty level (easy, medium, hard)
        qna_type: Question type (mcq, descriptive, mixed)
        num_questions: Number of questions to generate
        marks_pattern: Marks pattern
        target_language: Target language
        distribution_list: Question distribution list
        subject: Subject hint
    
    Returns:
        Dict with generated questions and metadata
    """
    from app.ai_service import generate_qna
    
    # If concepts extraction failed or returned empty, fall back to original method
    concepts = concepts_data.get("concepts", [])
    if not concepts or len(concepts) == 0:
        print("⚠️  No concepts extracted, falling back to standard generation")
        # Use original generate_qna function (import here to avoid circular import)
        from app.ai_service import generate_qna as generate_qna_original
        return generate_qna_original(
            text_content=text_content,
            difficulty=difficulty,
            qna_type=qna_type,
            num_questions=num_questions,
            marks_pattern=marks_pattern,
            target_language=target_language,
            distribution_list=distribution_list,
            subject=subject
        )
    
    # Build concept summary for prompt
    concept_summary = "\n".join([
        f"{idx + 1}. {c['concept']}: {c['description']}"
        for idx, c in enumerate(concepts[:20])  # Limit to first 20 concepts
    ])
    
    # Use the original generate_qna but with concept-enhanced prompt
    # We'll modify the text_content to include concepts at the start
    enhanced_text = f"""CONCEPTS TO FOCUS ON:
{concept_summary}

ORIGINAL TEXT:
{text_content}"""
    
    # Call original generate_qna with enhanced text (import here to avoid circular import)
    # This maintains all existing validation and formatting
    from app.ai_service import generate_qna as generate_qna_original
    result = generate_qna_original(
        text_content=enhanced_text,
        difficulty=difficulty,
        qna_type=qna_type,
        num_questions=num_questions,
        marks_pattern=marks_pattern,
        target_language=target_language,
        distribution_list=distribution_list,
        subject=concepts_data.get("subject") or subject
    )
    
    # Add concept metadata to result
    result["_concepts_used"] = len(concepts)
    result["_pipeline_step"] = "two_step"
    
    return result


def generate_qna_pipeline(
    text_content: str,
    difficulty: str,
    qna_type: str,
    num_questions: int,
    marks_pattern: str = "mixed",
    target_language: str = "english",
    remaining_questions: Optional[int] = None,
    distribution_list: Optional[List[Dict[str, Any]]] = None,
    subject: Optional[str] = None,
    num_parts: Optional[int] = None,
    use_pipeline: bool = True
) -> Dict[str, Any]:
    """
    Main pipeline function: Two-step Q/A generation
    
    Step 1: Extract concepts (cheap model)
    Step 2: Generate Q/A using concepts (controlled, with validation)
    
    Args:
        text_content: Text to generate questions from
        difficulty: Difficulty level
        qna_type: Question type
        num_questions: Number of questions
        marks_pattern: Marks pattern
        target_language: Target language
        remaining_questions: Remaining questions quota
        distribution_list: Question distribution
        subject: Subject hint
        num_parts: Number of parts (for split PDFs)
        use_pipeline: Whether to use two-step pipeline (default: True)
    
    Returns:
        Dict with generated questions and metadata
    """
    if not use_pipeline:
        # Fallback to original single-step generation
        from app.ai_service import generate_qna
        return generate_qna(
            text_content=text_content,
            difficulty=difficulty,
            qna_type=qna_type,
            num_questions=num_questions,
            marks_pattern=marks_pattern,
            target_language=target_language,
            remaining_questions=remaining_questions,
            distribution_list=distribution_list,
            subject=subject,
            num_parts=num_parts
        )
    
    print("🔄 Starting two-step AI pipeline...")
    
    # Step 1: Extract concepts
    print("📚 Step 1: Extracting concepts...")
    concepts_data = extract_concepts(text_content, subject)
    
    # Step 2: Generate Q/A from concepts
    print("❓ Step 2: Generating questions from concepts...")
    result = generate_qa_from_concepts(
        text_content=text_content,
        concepts_data=concepts_data,
        difficulty=difficulty,
        qna_type=qna_type,
        num_questions=num_questions,
        marks_pattern=marks_pattern,
        target_language=target_language,
        distribution_list=distribution_list,
        subject=subject
    )
    
    print("✅ Pipeline completed successfully")
    
    return result

