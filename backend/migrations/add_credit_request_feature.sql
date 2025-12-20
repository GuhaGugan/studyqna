-- Migration: Add Credit Request Feature
-- This migration adds support for users to request additional question credits

-- Step 1: Add bonus_questions column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_questions INTEGER DEFAULT 0;

-- Step 2: Create credit_requests table
CREATE TABLE IF NOT EXISTS credit_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    requested_credits INTEGER NOT NULL CHECK (requested_credits > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    user_notes TEXT
);

-- Step 3: Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_credit_requests_user_id ON credit_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_requests_status ON credit_requests(status);
CREATE INDEX IF NOT EXISTS idx_credit_requests_requested_at ON credit_requests(requested_at DESC);

-- Step 4: Add comment for documentation
COMMENT ON TABLE credit_requests IS 'Stores user requests for additional question credits';
COMMENT ON COLUMN users.bonus_questions IS 'Additional question credits granted by admin (added to base limit of 700)';

