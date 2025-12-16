# PDF Book Splitter Feature Documentation

## Overview

The PDF Book Splitter feature allows teachers to upload large PDF books (up to 100MB) and automatically split them into smaller parts of approximately 6MB each. This improves upload, OCR, and question generation performance.

## Features

1. **Automatic Detection**: Large PDFs (>6MB) are automatically detected after upload
2. **Smart Splitting**: PDFs are split into ~6MB chunks while maintaining page order
3. **Part Management**: Each part can be:
   - Previewed (first 5 pages)
   - Renamed with custom names
   - Selected for question generation
4. **Seamless Integration**: Selected parts work with existing QnA generation flow

## Backend Components

### Database Model
- **`PdfSplitPart`**: Stores metadata for each split part
  - `parent_upload_id`: Reference to original PDF
  - `part_number`: Sequential part number (1, 2, 3...)
  - `custom_name`: User-defined name (optional)
  - `file_path`: Storage path for the part
  - `start_page`, `end_page`: Page range
  - `total_pages`: Number of pages in part

### Service (`pdf_split_service.py`)
- `split_pdf_into_parts()`: Main splitting function
- `get_part_preview()`: Generates preview PDF (first 5 pages)

### API Endpoints

1. **`POST /api/upload/{upload_id}/split`**
   - Splits a PDF into parts
   - Returns list of created parts

2. **`GET /api/upload/{upload_id}/split-parts`**
   - Lists all split parts for a PDF

3. **`PUT /api/upload/split-parts/{part_id}/rename`**
   - Renames a split part with custom name

4. **`GET /api/upload/split-parts/{part_id}/preview`**
   - Returns preview PDF (first 5 pages)

5. **`GET /api/upload/split-parts/{part_id}/download`**
   - Creates a temporary Upload record for the part
   - Returns upload ID for QnA generation

## Frontend Components

### `PdfSplitParts.jsx`
- Displays split parts UI
- Handles splitting, renaming, preview, and selection
- Shows part information (pages, size, custom name)

### Integration in Dashboard
- Automatically shows split parts component for PDFs >6MB
- Integrates with existing upload display
- Selected parts work seamlessly with QnA generator

## Usage Flow

1. **Upload Large PDF** (>6MB)
   - Teacher uploads PDF as usual
   - System detects large size

2. **Split PDF**
   - Teacher clicks "Split PDF into Parts"
   - System splits PDF into ~6MB chunks
   - Parts are displayed with page ranges

3. **Manage Parts**
   - Teacher can rename parts (e.g., "Chapter 1", "Unit 2")
   - Teacher can preview parts (first 5 pages)
   - Teacher can select a part for question generation

4. **Generate Questions**
   - Selected part is treated as a regular upload
   - Works with existing QnA generation flow
   - No changes to OCR or AI prompts

## Configuration

### Settings (`config.py`)
- `MAX_PDF_SIZE_MB`: 6MB (regular upload limit)
- `MAX_BOOK_PDF_SIZE_MB`: 100MB (maximum for book splitting)
- `MAX_IMAGE_SIZE_MB`: 10MB (unchanged)

## Database Migration

Run the migration script to create the `pdf_split_parts` table:

```bash
cd backend
python migrations/add_pdf_split_parts.py
```

Or manually run:

```sql
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS is_split BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS pdf_split_parts (
    id SERIAL PRIMARY KEY,
    parent_upload_id INTEGER NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    part_number INTEGER NOT NULL,
    custom_name VARCHAR(200),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    start_page INTEGER NOT NULL,
    end_page INTEGER NOT NULL,
    total_pages INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_upload_id, part_number)
);

CREATE INDEX idx_pdf_split_parts_parent_upload ON pdf_split_parts(parent_upload_id);
CREATE INDEX idx_pdf_split_parts_user ON pdf_split_parts(user_id);
```

## Important Notes

1. **No Breaking Changes**: All existing functionality remains unchanged
2. **Quota System**: Each part is treated as a separate upload when selected
3. **Storage**: Split parts are stored in the same secure storage as regular uploads
4. **Encryption**: Split parts inherit encryption settings from storage service
5. **Page Limits**: Original PDF page limits still apply (40 pages premium, 10 free)

## Error Handling

- Splitting fails gracefully with user-friendly error messages
- Preview failures don't block part selection
- Rename validation ensures names are not empty and <200 characters

## Future Enhancements

- Chapter boundary detection for smarter splitting
- Batch selection of multiple parts
- Merge parts back into single PDF
- Part reordering


