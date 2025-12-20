# Credit Request Feature - Implementation Summary

## Overview
Users can now request additional question credits when they exceed their 700 question limit. Admins can approve/reject these requests.

## How It Works

### For Users:
1. When a user exceeds 700 questions, they see a message suggesting they can request additional credits
2. User can go to Profile tab and click "Request Credits"
3. User enters:
   - Number of credits requested (1-1000)
   - Optional reason/notes
4. Request is submitted and status shows as "Pending"
5. When approved by admin, credits are automatically added to their account
6. Effective limit becomes: 700 (base) + bonus_questions (granted)

### For Admins:
1. Admin sees all credit requests in Admin Dashboard
2. Can approve or reject requests
3. When approved, credits are added to user's `bonus_questions` field
4. All actions are logged in audit log

## Database Changes Required

### 1. Add `bonus_questions` column to `users` table:
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_questions INTEGER DEFAULT 0;
```

### 2. Create `credit_requests` table:
```sql
CREATE TABLE IF NOT EXISTS credit_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    requested_credits INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    notes TEXT,
    user_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_credit_requests_user_id ON credit_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_requests_status ON credit_requests(status);
```

## API Endpoints

### User Endpoints:
- `POST /api/user/request-credits` - Request additional credits
- Request body: `{ "requested_credits": 100, "user_notes": "Optional reason" }`

### Admin Endpoints:
- `GET /api/admin/credit-requests` - List all credit requests
- `POST /api/admin/credit-requests/{request_id}/approve` - Approve request
- `POST /api/admin/credit-requests/{request_id}/reject` - Reject request

## Frontend Implementation Needed

1. **Profile Tab**: Add "Request Credits" button when limit is exceeded
2. **Request Modal**: Form to enter credits and reason
3. **Request Status**: Show pending/approved/rejected status
4. **Admin Dashboard**: Add "Credit Requests" tab with approve/reject actions

## Example Flow

1. User has 712/700 questions (exceeded limit)
2. User clicks "Request Credits" in Profile tab
3. User requests 200 credits with note: "Need more for final exams"
4. Admin sees request in Admin Dashboard
5. Admin approves and grants 200 credits
6. User's effective limit becomes: 700 + 200 = 900 questions
7. User can now generate up to 900 questions total

## Benefits

- Users can continue using the system after reaching limit
- Admins have control over credit allocation
- All requests are tracked and audited
- Flexible system that can grant any amount of credits

