-- ================================
-- Bot Catatan Keuangan AI
-- Supabase Database Schema
-- ================================

-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== USERS TABLE ====================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    pin_hash VARCHAR(255) NOT NULL,
    safe_mode BOOLEAN DEFAULT FALSE,
    auto_delete_hours INTEGER DEFAULT 0,
    sheets_connected BOOLEAN DEFAULT FALSE,
    sheets_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Index for faster lookup by telegram_id
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- ==================== TRANSACTIONS TABLE ====================
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_encrypted TEXT NOT NULL,  -- Encrypted amount
    description VARCHAR(500),
    category VARCHAR(100) NOT NULL,
    source_type VARCHAR(20) DEFAULT 'text',  -- text, voice, receipt
    store_name VARCHAR(255),
    items JSONB,  -- Array of items for receipts
    receipt_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);

-- ==================== CATEGORIES TABLE ====================
CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📦',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index and unique constraint
CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_user_name ON categories(user_id, name);

-- ==================== SAVINGS TARGETS TABLE ====================
CREATE TABLE IF NOT EXISTS savings_targets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount BIGINT NOT NULL,
    current_amount BIGINT DEFAULT 0,
    deadline_months INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_savings_targets_user_id ON savings_targets(user_id);

-- ==================== USER SESSIONS TABLE ====================
-- For PIN verification state
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state VARCHAR(100),  -- Current conversation state
    state_data JSONB,    -- Additional state data
    pin_verified BOOLEAN DEFAULT FALSE,
    pin_verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- ==================== ROW LEVEL SECURITY ====================
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE savings_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Policies for service role (backend) - full access
CREATE POLICY "Service role full access on users" ON users
    FOR ALL USING (true);

CREATE POLICY "Service role full access on transactions" ON transactions
    FOR ALL USING (true);

CREATE POLICY "Service role full access on categories" ON categories
    FOR ALL USING (true);

CREATE POLICY "Service role full access on savings_targets" ON savings_targets
    FOR ALL USING (true);

CREATE POLICY "Service role full access on user_sessions" ON user_sessions
    FOR ALL USING (true);

-- ==================== HELPER FUNCTIONS ====================

-- Function to get user's total spending for a period
CREATE OR REPLACE FUNCTION get_user_spending_summary(
    p_user_id BIGINT,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    category VARCHAR(100),
    transaction_count BIGINT,
    total_transactions BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.category,
        COUNT(*)::BIGINT as transaction_count,
        (SELECT COUNT(*) FROM transactions WHERE user_id = p_user_id 
         AND created_at::DATE BETWEEN p_start_date AND p_end_date)::BIGINT as total_transactions
    FROM transactions t
    WHERE t.user_id = p_user_id
    AND t.created_at::DATE BETWEEN p_start_date AND p_end_date
    GROUP BY t.category
    ORDER BY transaction_count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==================== SAMPLE DATA (Optional) ====================
-- Uncomment to insert default categories

/*
INSERT INTO categories (user_id, name, icon, is_default) VALUES
(0, 'Makan', '🍔', true),
(0, 'Transport', '🚗', true),
(0, 'Belanja', '🛒', true),
(0, 'Hiburan', '🎮', true),
(0, 'Tagihan', '📄', true),
(0, 'Kesehatan', '💊', true),
(0, 'Pendidikan', '📚', true),
(0, 'Lainnya', '📦', true);
*/
