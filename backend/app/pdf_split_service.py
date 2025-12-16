"""
PDF Book Splitter Service
Splits large PDF files into smaller parts (~6MB each) for better processing
"""
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PyPDF2 import PdfReader, PdfWriter
from app.storage_service import save_file, read_file, ensure_storage_path
from app.config import settings


def split_pdf_into_parts(
    pdf_file_path: str,
    user_id: int,
    original_filename: str,
    target_size_mb: float = 6.0
) -> List[Dict[str, Any]]:
    """
    Split a large PDF into smaller parts of approximately target_size_mb each.
    
    Args:
        pdf_file_path: Path to the original PDF file
        user_id: User ID for storage path
        original_filename: Original filename (for naming parts)
        target_size_mb: Target size per part in MB (default: 6MB)
    
    Returns:
        List of dictionaries containing part information:
        [
            {
                "part_number": 1,
                "file_name": "book_part_1.pdf",
                "file_path": "/path/to/part1.pdf",
                "file_size": 6291456,
                "start_page": 1,
                "end_page": 20,
                "total_pages": 20
            },
            ...
        ]
    """
    target_size_bytes = int(target_size_mb * 1024 * 1024)
    
    # Read the PDF file
    pdf_content = read_file(pdf_file_path)
    pdf_reader = PdfReader(io.BytesIO(pdf_content))
    total_pages = len(pdf_reader.pages)
    
    print(f"📚 Splitting PDF: {original_filename}")
    print(f"   Total pages: {total_pages}")
    print(f"   Target size per part: {target_size_mb}MB ({target_size_bytes} bytes)")
    
    parts = []
    current_part = 1
    current_start_page = 0  # 0-indexed
    
    # Get base filename without extension
    base_name = Path(original_filename).stem
    
    # Calculate average page size to better estimate
    sample_pages = min(10, total_pages)
    total_sample_size = 0
    for i in range(sample_pages):
        temp_writer = PdfWriter()
        temp_writer.add_page(pdf_reader.pages[i])
        temp_buffer = io.BytesIO()
        temp_writer.write(temp_buffer)
        total_sample_size += len(temp_buffer.getvalue())
    avg_page_size = total_sample_size / sample_pages if sample_pages > 0 else target_size_bytes / 50
    
    # Override strategy: split by page count (~40 pages per part) to reduce part count
    pages_per_part = 40
    print(f"   Average page size: {avg_page_size / 1024:.2f} KB")
    print(f"   Using fixed page chunk: {pages_per_part} pages per part (page-based splitting)")
    
    while current_start_page < total_pages:
        writer = PdfWriter()
        start = current_start_page
        end = min(total_pages, start + pages_per_part)
        
        # Add pages for this chunk (page-based)
        for idx in range(start, end):
            writer.add_page(pdf_reader.pages[idx])
        
        # Write part to bytes
        part_buffer = io.BytesIO()
        writer.write(part_buffer)
        part_content = part_buffer.getvalue()
        actual_size = len(part_content)
        pages_in_part = end - start
        
        part_filename = f"{base_name}_part_{current_part}.pdf"
        part_file_path = save_file(part_content, user_id, "pdf", part_filename)
        
        part_info = {
            "part_number": current_part,
            "file_name": part_filename,
            "file_path": part_file_path,
            "file_size": actual_size,
            "start_page": start + 1,  # 1-indexed
            "end_page": end,          # 1-indexed
            "total_pages": pages_in_part
        }
        
        parts.append(part_info)
        
        print(f"   ✅ Part {current_part}: Pages {part_info['start_page']}-{part_info['end_page']} "
              f"({pages_in_part} pages, {actual_size / 1024 / 1024:.2f}MB)")
        
        current_part += 1
        current_start_page = end
    
    print(f"📦 PDF split into {len(parts)} parts")
    return parts


def get_part_preview(part_file_path: str, max_pages: int = 5) -> bytes:
    """
    Generate a preview PDF containing first few pages of a split part.
    
    Args:
        part_file_path: Path to the split part PDF
        max_pages: Maximum number of pages to include in preview
    
    Returns:
        Bytes of preview PDF
    """
    pdf_content = read_file(part_file_path)
    pdf_reader = PdfReader(io.BytesIO(pdf_content))
    
    writer = PdfWriter()
    preview_pages = min(max_pages, len(pdf_reader.pages))
    
    for i in range(preview_pages):
        writer.add_page(pdf_reader.pages[i])
    
    preview_buffer = io.BytesIO()
    writer.write(preview_buffer)
    return preview_buffer.getvalue()

