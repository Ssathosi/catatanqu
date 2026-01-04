-- ================================
-- Bot Catatan Keuangan AI
-- Wallet Feature Schema
-- ================================

-- Run this in Supabase SQL Editor AFTER the main schema

-- ==================== WALLETS TABLE ====================
CREATE TABLE IF NOT EXISTS wallets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,           -- "Dana", "BCA", "Cash"
    type VARCHAR(20) NOT NULL,            -- "ewallet", "bank", "cash"
    icon VARCHAR(10) DEFAULT '💰',
    balance_encrypted TEXT NOT NULL,      -- Saldo terenkripsi
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_type ON wallets(type);

-- Unique constraint: one wallet name per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_wallets_user_name ON wallets(user_id, name) WHERE is_active = TRUE;

-- ==================== WALLET LOGS TABLE ====================
CREATE TABLE IF NOT EXISTS wallet_logs (
    id BIGSERIAL PRIMARY KEY,
    wallet_id BIGINT NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    transaction_id BIGINT REFERENCES transactions(id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL,            -- "expense", "income", "topup", "transfer_in", "transfer_out", "initial"
    amount_encrypted TEXT NOT NULL,
    balance_before_encrypted TEXT NOT NULL,
    balance_after_encrypted TEXT NOT NULL,
    note VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_wallet_logs_wallet_id ON wallet_logs(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallet_logs_created_at ON wallet_logs(created_at);

-- ==================== MODIFY TRANSACTIONS TABLE ====================
-- Add wallet_id column to transactions
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS wallet_id BIGINT REFERENCES wallets(id) ON DELETE SET NULL;

-- Index for wallet lookups
CREATE INDEX IF NOT EXISTS idx_transactions_wallet_id ON transactions(wallet_id);

-- ==================== RLS POLICIES ====================
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallet_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on wallets" ON wallets
    FOR ALL USING (true);

CREATE POLICY "Service role full access on wallet_logs" ON wallet_logs
    FOR ALL USING (true);
