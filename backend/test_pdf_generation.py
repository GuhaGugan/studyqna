"""
Test script for PDF generation with multilingual support
Run this from the backend directory: python test_pdf_generation.py
"""
import os
import sys

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.download_service import generate_pdf

# Sample Q&A data in Tamil (you can modify this)
sample_qna_data = {
    "questions": [
        {
            "question": "கார்கள் எந்த வசதியமீைன்னிரத்திக் கரெண்ட உங்கள் தவேகைள ைமீன்னறிந்த சயெல்பட்ம்?",
            "type": "mcq",
            "options": [
                "கயைாளா திறன்",
                "ஹாேலாேகிராஃபிக் காட்சிகள்",
                "சீய-கணமடயைம் தன்ம",
                "மீன்னிஸுத்திக் காெண்ட சயெல்படம் திறன்"
            ],
            "correct_answer": "சீய-கணமடயைம் தன்ம",
            "marks": 1
        },
        {
            "question": "நாளயை சாலகைளில் எந்த வகயைான கார்கள் பயணத்தை சாத்தியமாக்கீம்?",
            "type": "mcq",
            "options": [
                "ய-ஓட்டநர் கார்கள்",
                "பரம்பரயைான எரிபாெள் கார்கள்",
                "மின்சார கார்கள்",
                "பாரம்பரிய கார்கள்"
            ],
            "correct_answer": "ய-ஓட்டநர் கார்கள்",
            "marks": 2
        }
    ]
}

def test_pdf_generation():
    """Test PDF generation with sample data"""
    print("🧪 Testing PDF generation...")
    print("📝 Sample data: Tamil questions")
    
    try:
        # Generate PDF
        pdf_bytes = generate_pdf(
            qna_data=sample_qna_data,
            output_format="questions_answers",
            title="Test Questions - Tamil",
            target_language="tamil"
        )
        
        # Save to file
        output_path = "test_output.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
        file_size = len(pdf_bytes)
        print(f"✅ PDF generated successfully!")
        print(f"📄 Saved to: {output_path}")
        print(f"📊 File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        print(f"\n💡 Open {output_path} to view the generated PDF")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()


