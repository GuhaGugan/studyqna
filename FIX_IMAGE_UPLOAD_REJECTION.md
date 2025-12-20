# Fix: Mobile Photos Being Rejected on Production Server

## Problem Analysis

Photos taken from mobile are being rejected on the production server. There are **two potential causes**:

### Issue 1: Free Users Blocked (Backend)
**Location:** `backend/app/routers/upload.py` line 226-230

Free users are currently **blocked from uploading images**. The code explicitly raises an error:
```python
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Image uploads require premium access"
)
```

### Issue 2: Content Validation Too Strict (Backend)
**Location:** `backend/app/content_validation.py`

The validation system is very strict and may reject legitimate study material photos if:
- Text extraction fails (OCR issues)
- Image quality is slightly blurry
- Edge/text patterns aren't detected properly
- False positives from face/body detection

---

## Solution Options

### Option 1: Allow Free Users to Upload Images (Recommended)

If you want to allow free users to upload images:

**Edit:** `backend/app/routers/upload.py`

**Find (around line 225-230):**
```python
else:
    # Free users: check monthly limit (simplified)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Image uploads require premium access"
    )
```

**Replace with:**
```python
else:
    # Free users: Allow image uploads (you can add daily/monthly limits if needed)
    # Check daily limit (optional - adjust as needed)
    today_image_uploads = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.file_type == FileType.IMAGE,
        Upload.created_at >= datetime.utcnow().date()
    ).count()
    
    # Allow 3 images per day for free users (adjust as needed)
    if today_image_uploads >= 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free users can upload 3 images per day. Upgrade to premium for unlimited uploads."
        )
```

### Option 2: Make Content Validation Less Strict

If validation is rejecting legitimate photos, you can make it more lenient:

**Edit:** `backend/app/content_validation.py`

**Option 2A: Reduce Text Requirement**

Find line 366:
```python
if extracted_text and len(extracted_text.strip()) >= 10:
```

Change to:
```python
if extracted_text and len(extracted_text.strip()) >= 5:  # Reduced from 10 to 5
```

And line 370:
```python
if alnum_count >= 5:  # Reduced from 5 to 3
```

**Option 2B: Make Quality Check Less Strict**

Find line 575 in `content_validation.py`:
```python
if laplacian_var < 100:
```

Change to:
```python
if laplacian_var < 50:  # Reduced from 100 to 50 (allows slightly blurry photos)
```

**Option 2C: Allow Images Even If OCR Fails (If Edge Patterns Detected)**

This is already partially implemented, but you can make it more lenient by adjusting thresholds in `check_is_study_material()` function.

---

## Quick Fix Steps (SSH into Server)

### Step 1: Check Current Error

First, check what error is being returned:

```bash
# SSH into server
ssh ubuntu@YOUR_SERVER_IP

# Check backend logs
sudo journalctl -u studyqna-backend -n 50 --no-pager | grep -i "image\|upload\|reject"
```

Or check the backend console output if running manually.

### Step 2: Update Backend Code

```bash
# Navigate to backend
cd ~/studyqna-assistant/backend
# or
cd ~/studyqna/backend

# Edit upload.py
nano app/routers/upload.py
```

**Find and update the free user image upload block (around line 226-230).**

### Step 3: Restart Backend

```bash
# If using systemd
sudo systemctl restart studyqna-backend

# Or if using PM2
pm2 restart studyqna-backend

# Or if running manually, restart the uvicorn process
```

### Step 4: Test

Try uploading a photo from mobile again.

---

## Diagnostic: Check What's Being Rejected

To see the exact error, check backend logs:

```bash
# Real-time logs
sudo journalctl -u studyqna-backend -f

# Or check PM2 logs
pm2 logs studyqna-backend

# Or if running manually, check the console output
```

Look for messages like:
- `"Image uploads require premium access"` → Issue 1 (free user blocked)
- `"Image does not contain readable text"` → Issue 2 (validation too strict)
- `"Image not readable"` → Quality check too strict
- `"Image contains human body content"` → False positive in detection

---

## Recommended Fix (Complete)

I recommend **allowing free users with a daily limit** and **making validation slightly more lenient**:

### 1. Update `backend/app/routers/upload.py`:

```python
# Around line 225, replace the free user block with:
else:
    # Free users: Allow image uploads with daily limit
    today_image_uploads = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.file_type == FileType.IMAGE,
        Upload.created_at >= datetime.utcnow().date()
    ).count()
    
    # Allow 5 images per day for free users
    if today_image_uploads >= 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free users can upload 5 images per day. Upgrade to premium for unlimited uploads."
        )
```

### 2. Make Validation More Lenient (Optional):

In `backend/app/content_validation.py`:

- Line 366: Change `>= 10` to `>= 5` (reduce text requirement)
- Line 370: Change `>= 5` to `>= 3` (reduce alphanumeric requirement)
- Line 575: Change `< 100` to `< 50` (allow slightly blurry photos)

---

## After Making Changes

1. **Restart backend:**
   ```bash
   sudo systemctl restart studyqna-backend
   # or
   pm2 restart studyqna-backend
   ```

2. **Test on mobile:**
   - Take a photo of study material
   - Try uploading
   - Check if it works

3. **If still failing:**
   - Check backend logs for exact error
   - Adjust validation thresholds further if needed

---

## Alternative: Temporarily Disable Strict Validation

If you need a quick fix and want to allow all images temporarily:

**Edit:** `backend/app/routers/upload.py`

**Around line 200, comment out the validation:**
```python
# Image validation
if is_image:
    # TEMPORARY: Skip strict validation for testing
    # try:
    #     is_valid, error_msg = validate_image(file_content, current_user)
    #     if not is_valid:
    #         raise HTTPException(...)
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     raise HTTPException(...)
    
    # Just check quota (remove validation temporarily)
    if is_premium:
        if current_user.image_quota_remaining <= 0:
            raise HTTPException(...)
    else:
        # Free user check (from Option 1 above)
        ...
```

**⚠️ WARNING:** This disables all content validation. Only use for testing!

---

## Summary

**Most likely cause:** Free users are blocked from image uploads.

**Quick fix:** Update `backend/app/routers/upload.py` to allow free users with a daily limit.

**If validation is too strict:** Adjust thresholds in `backend/app/content_validation.py`.

