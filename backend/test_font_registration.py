"""
Test font registration to debug black blocks issue
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

# Register Tamil font
font_dir = os.path.join(os.path.dirname(__file__), "app", "fonts")
tamil_font_path = os.path.join(font_dir, "NotoSansTamil-Regular.ttf")

print(f"Font directory: {font_dir}")
print(f"Tamil font path: {tamil_font_path}")
print(f"Font exists: {os.path.exists(tamil_font_path)}")

if os.path.exists(tamil_font_path):
    try:
        pdfmetrics.registerFont(TTFont("NotoTamil", tamil_font_path))
        print("✅ Font registered successfully!")
    except Exception as e:
        print(f"❌ Failed to register font: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("❌ Font file not found!")
    sys.exit(1)

# Check registered fonts
registered = pdfmetrics.getRegisteredFontNames()
print(f"\nRegistered fonts: {registered}")
print(f"NotoTamil in registered fonts: {'NotoTamil' in registered}")

# Create a simple PDF with Tamil text
buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=A4)
story = []

styles = getSampleStyleSheet()
tamil_style = ParagraphStyle(
    'TamilStyle',
    parent=styles['Normal'],
    fontName='NotoTamil',
    fontSize=16
)

# Test Tamil text
test_text = "வணக்கம் உலகம்"  # "Hello World" in Tamil
print(f"\nTest text: {test_text}")
print(f"Using font: NotoTamil")

story.append(Paragraph(f"<font name='NotoTamil'>{test_text}</font>", tamil_style))

try:
    doc.build(story)
    buffer.seek(0)
    pdf_bytes = buffer.read()
    
    output_path = "test_font_output.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"\n✅ PDF created: {output_path}")
    print(f"📊 Size: {len(pdf_bytes)} bytes")
    print(f"\n💡 Open {output_path} to check if Tamil text renders correctly")
    print(f"   If you see black blocks, the font embedding failed.")
    print(f"   If you see Tamil text, the font is working correctly.")
    
except Exception as e:
    print(f"❌ Error creating PDF: {e}")
    import traceback
    traceback.print_exc()


