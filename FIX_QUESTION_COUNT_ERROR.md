# Fix: "AI generated only 10 questions but 15 were requested" Error

## Problem
In production, when using custom distribution (e.g., 5 questions of 2 marks + 10 questions of 1 mark = 15 total), the AI is generating only 10 questions instead of 15, causing a 500 error.

## Root Cause
The AI is not strictly following the custom distribution requirements, even though the prompt has strong language about exact counts.

## Solution Applied

### 1. Enhanced Distribution Breakdown in Prompt
Added explicit step-by-step breakdown showing exactly what needs to be generated:

```
🚨 EXACT DISTRIBUTION BREAKDOWN - YOU MUST GENERATE EXACTLY:
  • 5 questions of 2 marks (type: short)
  • 10 questions of 1 mark (type: mcq)
🚨 TOTAL REQUIRED: 15 questions (sum of all above)
🚨 STEP-BY-STEP GENERATION PROCESS:
  1. Generate 5 questions of 2 marks (type: short)
  2. Generate 10 questions of 1 mark (type: mcq)
  3. Count ALL questions - total MUST be 15
  4. Verify each category matches the count above
  5. ONLY output JSON when you have verified the count is exactly 15
```

### 2. Enhanced Distribution Requirements Section
Added detailed verification checklist:

```
DISTRIBUTION REQUIREMENTS (ABSOLUTELY MANDATORY):
- Follow the distribution EXACTLY: [distribution]
- 🚨 DISTRIBUTION BREAKDOWN - YOU MUST GENERATE:
  • EXACTLY 5 questions of 2 marks (type: short)
  • EXACTLY 10 questions of 1 mark (type: mcq)
- 🚨 TOTAL REQUIRED: 15 questions (sum of all counts above)
- 🚨 VERIFY: After generating, count each category:
  * Count questions with 2 marks and type "short" - should be EXACTLY 5
  * Count questions with 1 mark and type "mcq" - should be EXACTLY 10
- 🚨 FINAL CHECK: Total count = 15 (sum all categories above)
```

### 3. Retry Logic Already in Place
The backend already has retry logic (3 retries) that:
- Detects when fewer questions are generated
- Retries with STRICTER instructions
- Provides detailed error messages

## Files Modified
- `backend/app/ai_service.py`:
  - Enhanced `user_prompt` with explicit distribution breakdown
  - Added step-by-step generation process
  - Strengthened distribution requirements section

## Testing
After deploying, test with:
1. Custom distribution: 5 questions (2 marks, short) + 10 questions (1 mark, mcq)
2. Verify exactly 15 questions are generated
3. Check that distribution matches exactly

## If Still Failing

### Option 1: Check Backend Logs
```bash
# SSH into server
ssh ubuntu@YOUR_SERVER_IP

# Check backend logs
sudo journalctl -u studyqna-backend -n 100 --no-pager | grep -i "question\|count\|distribution"
```

Look for:
- "Expected=15, Got=10" - AI still not generating enough
- Distribution breakdown showing what was generated vs requested

### Option 2: Increase Retries
If retries are exhausting, you can increase retry count:

**Edit:** `backend/app/routers/qna.py`

**Find (around line 222):**
```python
max_retries = 3  # Increased retries for format repetition and insufficient questions
```

**Change to:**
```python
max_retries = 5  # Increased retries for format repetition and insufficient questions
```

### Option 3: Add More Explicit Instructions in Retry
The retry already includes explicit instructions, but you can make them even stronger by modifying the error message in `ai_service.py` around line 2257.

### Option 4: Use Different Model
If GPT-4o-mini is consistently failing, consider:
- Using `gpt-4o` (more expensive but more reliable)
- Using `gpt-4-turbo` (better at following instructions)

**Edit:** `backend/app/ai_service.py` around line 2078:
```python
model="gpt-4o-mini",  # Change to "gpt-4o" or "gpt-4-turbo"
```

## Deployment Steps

1. **Update backend code:**
   ```bash
   # On your local machine, the changes are already made
   # Commit and push to Git
   git add backend/app/ai_service.py
   git commit -m "Fix: Enhanced distribution breakdown for exact question count"
   git push
   ```

2. **Deploy to server:**
   ```bash
   # SSH into server
   ssh ubuntu@YOUR_SERVER_IP

   # Pull latest changes
   cd ~/studyqna-assistant
   git pull origin main

   # Restart backend
   sudo systemctl restart studyqna-backend

   # Check logs
   sudo journalctl -u studyqna-backend -f
   ```

3. **Test:**
   - Try generating with custom distribution
   - Verify exactly 15 questions are generated
   - Check distribution matches

## Expected Behavior After Fix

✅ AI generates exactly 15 questions:
- 5 questions of 2 marks (short type)
- 10 questions of 1 mark (mcq type)

✅ No more "AI generated only 10 questions" errors

✅ Custom distribution works correctly

## Summary

**Problem:** AI generating 10 questions instead of 15 for custom distribution

**Solution:** Enhanced prompt with explicit step-by-step breakdown and verification checklist

**Files Changed:** `backend/app/ai_service.py`

**Deployment:** Update backend code and restart service

**Testing:** Verify custom distribution generates exact count

