-- schema.sql  (PostgreSQL 15+)
-- Run with: psql -d your_db -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
--  USERS
-- ─────────────────────────────────────────
CREATE TABLE users (
    id               BIGINT      PRIMARY KEY,          -- Telegram user_id
    username         TEXT,
    full_name        TEXT        NOT NULL,
    language_code    CHAR(2)     NOT NULL DEFAULT 'en',
    referred_by      BIGINT      REFERENCES users(id) ON DELETE SET NULL,
    referral_code    TEXT        UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(6), 'hex'),
    referral_balance NUMERIC(12,4) NOT NULL DEFAULT 0,
    is_banned        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_referred_by   ON users(referred_by);

-- ─────────────────────────────────────────
--  SUBSCRIPTIONS
-- ─────────────────────────────────────────
CREATE TYPE subscription_status AS ENUM ('active', 'expired', 'cancelled');

CREATE TABLE subscriptions (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status           subscription_status NOT NULL DEFAULT 'active',
    price_usd        NUMERIC(8,2) NOT NULL DEFAULT 30.00,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at       TIMESTAMPTZ NOT NULL,
    payment_provider TEXT        NOT NULL,   -- 'cryptobot' | 'stars' | 'wallet'
    payment_ref      TEXT,                   -- external invoice / payment id
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subs_user_id    ON subscriptions(user_id);
CREATE INDEX idx_subs_expires_at ON subscriptions(expires_at);
CREATE INDEX idx_subs_status     ON subscriptions(status);

-- ─────────────────────────────────────────
--  ENCRYPTED API KEYS
-- ─────────────────────────────────────────
CREATE TABLE api_keys (
    id               UUID   PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exchange         TEXT   NOT NULL,          -- 'binance' | 'okx' | 'bybit' | 'kucoin' | 'gate'
    encrypted_key    BYTEA  NOT NULL,
    encrypted_secret BYTEA  NOT NULL,
    iv_key           BYTEA  NOT NULL,          -- 12-byte GCM nonce
    iv_secret        BYTEA  NOT NULL,
    tag_key          BYTEA  NOT NULL,          -- 16-byte GCM auth tag
    tag_secret       BYTEA  NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_apikeys_user_exchange ON api_keys(user_id, exchange) WHERE is_active;

-- ─────────────────────────────────────────
--  REFERRAL PAYOUTS
-- ─────────────────────────────────────────
CREATE TABLE referral_payouts (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id     BIGINT      NOT NULL REFERENCES users(id),
    referee_id      BIGINT      NOT NULL REFERENCES users(id),
    subscription_id UUID        NOT NULL REFERENCES subscriptions(id),
    amount_usd      NUMERIC(8,4) NOT NULL,    -- 10% of subscription price
    paid_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
--  TRADES
-- ─────────────────────────────────────────
CREATE TYPE trade_side   AS ENUM ('long', 'short');
CREATE TYPE trade_status AS ENUM ('open', 'closed_tp', 'closed_sl', 'closed_manual');

CREATE TABLE trades (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     BIGINT      NOT NULL REFERENCES users(id),
    exchange    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    side        trade_side  NOT NULL,
    risk_level  SMALLINT    NOT NULL CHECK (risk_level BETWEEN 1 AND 5),
    entry_price NUMERIC(20,8),
    close_price NUMERIC(20,8),
    pnl_pct     NUMERIC(8,4),
    status      trade_status NOT NULL DEFAULT 'open',
    opened_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at   TIMESTAMPTZ
);

CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_status  ON trades(status);

-- ─────────────────────────────────────────
--  AUTO-UPDATE updated_at
-- ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
