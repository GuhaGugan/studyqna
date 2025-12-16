# Troubleshooting Guide

## Common Issues and Solutions

### 1. 403 Forbidden on Upload

**Error:** `POST /api/upload 403 (Forbidden)`

**Causes:**
- User not logged in
- JWT token expired or invalid
- Token not being sent with request

**Solutions:**

1. **Check if user is logged in:**
   - Open browser console
   - Check: `localStorage.getItem('token')`
   - Should return a JWT token string

2. **Verify token is being sent:**
   - Open Network tab in DevTools
   - Check the upload request headers
   - Should see: `Authorization: Bearer <token>`

3. **Re-login:**
   - Logout and login again
   - This will refresh the token

4. **Check backend logs:**
   - Look for authentication errors
   - Verify token is valid

### 2. 500 Internal Server Error on Premium Request

**Error:** `POST /api/user/request-premium 500 (Internal Server Error)`

**Fixed:** Response format issue - now returns correct schema with `user_email`

**If still occurs:**
- Check backend terminal for detailed error
- Verify database connection
- Check if user exists in database

### 3. Email/OTP Not Working

**Symptoms:**
- OTP request succeeds but no email received
- Error in backend console

**Solutions:**

1. **Check backend console:**
   - OTP is printed to console if email fails
   - Look for: `⚠️  DEVELOPMENT MODE: OTP for email@example.com is: 123456`

2. **Configure SMTP (optional):**
   - Update `.env` file with SMTP credentials
   - For Gmail, use App Password

3. **Use console OTP:**
   - For development, use OTP from backend console
   - This is normal if SMTP isn't configured

### 4. Database Connection Errors

**Error:** `password authentication failed`

**Solutions:**
- Verify `.env` file has correct `DATABASE_URL`
- Check PostgreSQL is running
- Verify user and password match database setup
- Test connection: `psql -U studyqna_user -d studyqna`

### 5. File Upload Issues

**403 Forbidden:**
- User not authenticated (see #1)

**400 Bad Request:**
- File too large
- Wrong file type
- Exceeds page limits

**Solutions:**
- Check file size (PDF: 5MB max, Image: 2MB max)
- Verify file type (PDF or image)
- For free users: max 10 pages

### 6. Frontend Not Connecting to Backend

**Error:** Network errors, CORS issues

**Solutions:**
1. **Verify backend is running:**
   - Check http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. **Check CORS settings:**
   - Backend should allow `http://localhost:3000`
   - Check `app/config.py` for `CORS_ORIGINS`

3. **Verify proxy:**
   - Frontend `vite.config.js` should proxy `/api` to `http://localhost:8000`

### 7. Authentication Token Issues

**Symptoms:**
- Logged out unexpectedly
- 401/403 errors

**Solutions:**
1. **Check token expiration:**
   - Default: 24 hours
   - Re-login if expired

2. **Verify token format:**
   - Should be: `Bearer <token>`
   - Check in Network tab

3. **Clear and re-login:**
   ```javascript
   localStorage.clear()
   // Then login again
   ```

### 8. Premium Request Already Pending

**Error:** "Premium request already pending"

**Solutions:**
- Wait for admin approval
- Or admin can reject and you can request again
- Check status in admin dashboard

### 9. Storage Directory Issues

**Error:** File upload fails, storage errors

**Solutions:**
1. **Create storage directory:**
   ```bash
   mkdir -p storage/uploads
   ```

2. **Set permissions (Linux/Mac):**
   ```bash
   chmod 700 storage
   ```

3. **Check STORAGE_PATH in .env:**
   - Should be: `./storage` (relative) or absolute path

### 10. Human Detection Not Working

**Symptoms:**
- Images with humans not being blocked
- Detection errors

**Solutions:**
1. **Install ultralytics:**
   ```bash
   pip install ultralytics
   ```

2. **Model downloads automatically:**
   - First use will download YOLO model
   - Requires internet connection

3. **If model fails:**
   - Detection is disabled gracefully
   - App continues to work

## Debugging Steps

### Check Backend Logs

Look for errors in the backend terminal:
- Authentication errors
- Database errors
- File processing errors

### Check Frontend Console

Open browser DevTools (F12):
- Console tab: JavaScript errors
- Network tab: API request/response details

### Verify Configuration

1. **Backend `.env`:**
   - DATABASE_URL correct
   - SECRET_KEY set
   - ADMIN_EMAIL matches your email

2. **Frontend:**
   - API proxy configured
   - Token stored in localStorage

### Test API Directly

Use http://localhost:8000/docs to test endpoints:
- Verify authentication works
- Test upload endpoint
- Check error responses

## Getting Help

If issues persist:
1. Check backend terminal for detailed errors
2. Check browser console for frontend errors
3. Verify all configuration files
4. Review this troubleshooting guide
5. Check the main documentation files


