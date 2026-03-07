-- ============================================================
--  OMNIGENIUS — Supabase Schema
--  Run in Supabase SQL Editor (Dashboard > SQL Editor > New query)
--  Or via CLI: supabase db push
--
--  Tables:
--    users               Core user accounts
--    user_preferences    Appearance + notification settings
--    subscriptions       Stripe subscription state
--    conversations       Chat/Search/Reason sessions
--    messages            Individual messages within conversations
--    shared_conversations Public share links
--    api_keys            og- prefixed API keys (Advanced plan)
--    uploaded_files      Files attached to conversations
--    usage_events        Per-query usage log (billing + analytics)
--    export_requests     Data export job queue
--    waitlist            Pre-launch waitlist
--    careers_interest    Careers notification list
--    admin_notes         Internal notes on users (admin only)
-- ============================================================

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enums ────────────────────────────────────────────────────
CREATE TYPE plan_type AS ENUM ('free', 'pro', 'advanced');
CREATE TYPE chat_mode AS ENUM ('chat', 'search', 'reason', 'auto');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE sub_status AS ENUM ('active', 'past_due', 'canceled', 'trialing', 'incomplete');
CREATE TYPE export_status AS ENUM ('pending', 'processing', 'complete', 'failed');

-- ============================================================
--  USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_id            TEXT UNIQUE NOT NULL,           -- Clerk user ID (user_xxxx)
    email               TEXT UNIQUE NOT NULL,
    first_name          TEXT NOT NULL DEFAULT '',
    last_name           TEXT NOT NULL DEFAULT '',
    display_name        TEXT,                           -- Falls back to first_name if null
    bio                 TEXT,
    avatar_url          TEXT,                           -- CloudFront URL
    plan                plan_type NOT NULL DEFAULT 'free',
    stripe_customer_id  TEXT UNIQUE,                   -- Stripe cus_xxx
    queries_today       INTEGER NOT NULL DEFAULT 0,
    queries_total       INTEGER NOT NULL DEFAULT 0,
    suspended_at        TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ,                   -- Soft delete (GDPR)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Reset queries_today at midnight UTC via pg_cron (set up separately)
-- SELECT cron.schedule('reset-daily-usage', '0 0 * * *',
--   $$UPDATE public.users SET queries_today = 0$$);

CREATE INDEX idx_users_clerk_id       ON public.users(clerk_id);
CREATE INDEX idx_users_email          ON public.users(email);
CREATE INDEX idx_users_plan           ON public.users(plan);
CREATE INDEX idx_users_stripe_cust    ON public.users(stripe_customer_id);
CREATE INDEX idx_users_deleted        ON public.users(deleted_at) WHERE deleted_at IS NULL;

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
--  USER PREFERENCES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.user_preferences (
    user_id                         UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    -- Appearance
    theme                           TEXT NOT NULL DEFAULT 'dark',   -- dark | light | system
    font_size                       INTEGER NOT NULL DEFAULT 15 CHECK (font_size BETWEEN 12 AND 18),
    show_reasoning                  BOOLEAN NOT NULL DEFAULT TRUE,
    compact_view                    BOOLEAN NOT NULL DEFAULT FALSE,
    animate_responses               BOOLEAN NOT NULL DEFAULT TRUE,
    show_source_citations           BOOLEAN NOT NULL DEFAULT TRUE,
    -- Notifications
    notif_security_alerts           BOOLEAN NOT NULL DEFAULT TRUE,  -- always on, non-editable
    notif_billing_receipts          BOOLEAN NOT NULL DEFAULT TRUE,  -- always on, non-editable
    notif_product_updates           BOOLEAN NOT NULL DEFAULT TRUE,
    notif_tips                      BOOLEAN NOT NULL DEFAULT TRUE,
    notif_usage_alerts              BOOLEAN NOT NULL DEFAULT TRUE,
    notif_marketing                 BOOLEAN NOT NULL DEFAULT FALSE,
    -- Privacy
    conversation_history_enabled    BOOLEAN NOT NULL DEFAULT TRUE,
    usage_analytics_enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    allow_model_improvement         BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_prefs_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
--  SUBSCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stripe_subscription_id  TEXT UNIQUE,
    stripe_price_id         TEXT,
    plan                    plan_type NOT NULL DEFAULT 'free',
    status                  sub_status NOT NULL DEFAULT 'active',
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    cancel_at_period_end    BOOLEAN NOT NULL DEFAULT FALSE,
    canceled_at             TIMESTAMPTZ,
    trial_end               TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id    ON public.subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_id  ON public.subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status     ON public.subscriptions(status);

CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON public.subscriptions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
--  CONVERSATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title       TEXT,                                   -- Auto-generated from first message
    mode        chat_mode NOT NULL DEFAULT 'chat',
    is_shared   BOOLEAN NOT NULL DEFAULT FALSE,
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id    ON public.conversations(user_id);
CREATE INDEX idx_conversations_updated    ON public.conversations(user_id, updated_at DESC);
CREATE INDEX idx_conversations_mode       ON public.conversations(user_id, mode);

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Full text search on conversation title
CREATE INDEX idx_conversations_title_fts
    ON public.conversations
    USING gin(to_tsvector('english', COALESCE(title, '')));

-- ============================================================
--  MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role                message_role NOT NULL,
    content             TEXT NOT NULL,
    reasoning_content   TEXT,                   -- Chain-of-thought (Reason mode only)
    mode                chat_mode NOT NULL DEFAULT 'chat',
    model               TEXT NOT NULL DEFAULT 'chimera-v1',
    tokens_input        INTEGER,
    tokens_output       INTEGER,
    reasoning_loops     INTEGER,                -- Number of reason loops used
    sources             JSONB,                  -- Search mode: [{title, url, snippet}]
    file_ids            UUID[],                 -- Attached file references
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation    ON public.messages(conversation_id, created_at ASC);
CREATE INDEX idx_messages_user_id         ON public.messages(user_id);
CREATE INDEX idx_messages_created_at      ON public.messages(user_id, created_at DESC);
CREATE INDEX idx_messages_mode            ON public.messages(user_id, mode);

-- Increment conversation.message_count on insert
CREATE OR REPLACE FUNCTION increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.conversations
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_increment_message_count
    AFTER INSERT ON public.messages
    FOR EACH ROW EXECUTE FUNCTION increment_message_count();

-- ============================================================
--  SHARED CONVERSATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.shared_conversations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    slug                TEXT UNIQUE NOT NULL,       -- URL-safe random string (e.g. aB3xK9mP)
    view_count          INTEGER NOT NULL DEFAULT 0,
    expires_at          TIMESTAMPTZ,               -- NULL = never expires
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_shared_slug        ON public.shared_conversations(slug) WHERE revoked_at IS NULL;
CREATE INDEX idx_shared_user_id     ON public.shared_conversations(user_id);
CREATE INDEX idx_shared_conv_id     ON public.shared_conversations(conversation_id);

-- Increment view count (called by public GET /share/:slug)
CREATE OR REPLACE FUNCTION increment_share_views(p_slug TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE public.shared_conversations
    SET view_count = view_count + 1
    WHERE slug = p_slug
      AND revoked_at IS NULL
      AND (expires_at IS NULL OR expires_at > NOW());
END;
$$ LANGUAGE plpgsql;

-- ============================================================
--  API KEYS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    key_hash        TEXT UNIQUE NOT NULL,       -- SHA-256 of the full key (og-xxxx...)
    key_prefix      TEXT NOT NULL,             -- First 10 chars for display (og-a1b2c3d4)
    rate_limit_rpm  INTEGER NOT NULL DEFAULT 60,    -- Requests per minute
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id   ON public.api_keys(user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_api_keys_hash      ON public.api_keys(key_hash) WHERE revoked_at IS NULL;

-- ============================================================
--  UPLOADED FILES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.uploaded_files (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    mime_type       TEXT NOT NULL,
    size_bytes      INTEGER NOT NULL,
    s3_key          TEXT NOT NULL,                  -- S3 object key
    cloudfront_url  TEXT,
    extracted_text  TEXT,                           -- PDF text extraction result
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uploaded_files_user ON public.uploaded_files(user_id);

-- ============================================================
--  USAGE EVENTS
--  Append-only log. One row per assistant response.
--  Used for billing, analytics, and per-user rate limiting.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.usage_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    conversation_id     UUID REFERENCES public.conversations(id) ON DELETE SET NULL,
    message_id          UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    mode                chat_mode NOT NULL,
    model               TEXT NOT NULL DEFAULT 'chimera-v1',
    tokens_input        INTEGER NOT NULL DEFAULT 0,
    tokens_output       INTEGER NOT NULL DEFAULT 0,
    reasoning_loops     INTEGER,
    latency_ms          INTEGER,                    -- End-to-end response time
    via_api_key         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partition by month in production for scale:
-- CREATE TABLE usage_events_2026_03 PARTITION OF usage_events
--     FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE INDEX idx_usage_user_date    ON public.usage_events(user_id, created_at DESC);
CREATE INDEX idx_usage_mode         ON public.usage_events(user_id, mode, created_at DESC);
CREATE INDEX idx_usage_date         ON public.usage_events(created_at DESC);

-- Increment queries_today + queries_total on each usage event
CREATE OR REPLACE FUNCTION increment_user_query_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.users
    SET queries_today = queries_today + 1,
        queries_total = queries_total + 1
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_increment_query_counts
    AFTER INSERT ON public.usage_events
    FOR EACH ROW EXECUTE FUNCTION increment_user_query_counts();

-- ============================================================
--  EXPORT REQUESTS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.export_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status          export_status NOT NULL DEFAULT 'pending',
    s3_key          TEXT,                           -- Set when export is ready
    download_url    TEXT,                           -- Presigned S3 URL
    expires_at      TIMESTAMPTZ,                    -- Download link expiry
    error_message   TEXT,
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_export_requests_user ON public.export_requests(user_id, requested_at DESC);

-- ============================================================
--  WAITLIST
-- ============================================================
CREATE TABLE IF NOT EXISTS public.waitlist (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    name            TEXT,
    source          TEXT,                           -- twitter | producthunt | direct | referral
    position        SERIAL,                         -- Waitlist position (auto-incremented)
    invited_at      TIMESTAMPTZ,
    converted_at    TIMESTAMPTZ,                    -- Set when they sign up
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_waitlist_email      ON public.waitlist(email);
CREATE INDEX idx_waitlist_invited    ON public.waitlist(invited_at) WHERE invited_at IS NULL;

-- ============================================================
--  CAREERS INTEREST
-- ============================================================
CREATE TABLE IF NOT EXISTS public.careers_interest (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
--  ADMIN NOTES
--  Internal annotations on users (visible only to admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.admin_notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    author      TEXT NOT NULL,                      -- Admin email or name
    note        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_admin_notes_user ON public.admin_notes(user_id, created_at DESC);

-- ============================================================
--  ROW LEVEL SECURITY (RLS)
--  Users can only read/write their own rows.
--  Service role key bypasses RLS (used by backend only).
-- ============================================================

ALTER TABLE public.users               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shared_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploaded_files      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_events        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.export_requests     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_notes         ENABLE ROW LEVEL SECURITY;

-- Helper: get the Clerk user_id from the JWT sub claim
-- Supabase passes the JWT; we match on clerk_id stored in users table.
CREATE OR REPLACE FUNCTION auth_user_id() RETURNS UUID AS $$
    SELECT id FROM public.users
    WHERE clerk_id = auth.jwt() ->> 'sub'
    LIMIT 1;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- users: own row only
CREATE POLICY users_select_own ON public.users
    FOR SELECT USING (id = auth_user_id());
CREATE POLICY users_update_own ON public.users
    FOR UPDATE USING (id = auth_user_id());

-- user_preferences: own row only
CREATE POLICY prefs_all_own ON public.user_preferences
    FOR ALL USING (user_id = auth_user_id());

-- subscriptions: own row only
CREATE POLICY subs_select_own ON public.subscriptions
    FOR SELECT USING (user_id = auth_user_id());

-- conversations: own rows only
CREATE POLICY conversations_all_own ON public.conversations
    FOR ALL USING (user_id = auth_user_id());

-- messages: own rows only
CREATE POLICY messages_all_own ON public.messages
    FOR ALL USING (user_id = auth_user_id());

-- shared_conversations: public read for valid slugs; write own rows only
CREATE POLICY shared_public_read ON public.shared_conversations
    FOR SELECT USING (
        revoked_at IS NULL
        AND (expires_at IS NULL OR expires_at > NOW())
    );
CREATE POLICY shared_write_own ON public.shared_conversations
    FOR ALL USING (user_id = auth_user_id());

-- api_keys: own rows only
CREATE POLICY apikeys_all_own ON public.api_keys
    FOR ALL USING (user_id = auth_user_id());

-- uploaded_files: own rows only
CREATE POLICY files_all_own ON public.uploaded_files
    FOR ALL USING (user_id = auth_user_id());

-- usage_events: own rows, read only (backend writes via service role)
CREATE POLICY usage_select_own ON public.usage_events
    FOR SELECT USING (user_id = auth_user_id());

-- export_requests: own rows only
CREATE POLICY exports_all_own ON public.export_requests
    FOR ALL USING (user_id = auth_user_id());

-- waitlist + careers: public insert only (no read from client)
CREATE POLICY waitlist_insert ON public.waitlist
    FOR INSERT WITH CHECK (true);
CREATE POLICY careers_insert ON public.careers_interest
    FOR INSERT WITH CHECK (true);

-- admin_notes: no client access (service role only)
-- (no permissive policies = all access denied to anon/authenticated roles)

-- ============================================================
--  USEFUL VIEWS
-- ============================================================

-- Admin: user overview with plan + usage
CREATE OR REPLACE VIEW public.v_user_overview AS
SELECT
    u.id,
    u.email,
    u.display_name,
    u.first_name || ' ' || u.last_name AS full_name,
    u.plan,
    u.queries_today,
    u.queries_total,
    u.created_at,
    u.suspended_at,
    u.deleted_at,
    s.status        AS sub_status,
    s.current_period_end AS renewal_date,
    COUNT(DISTINCT c.id)  AS conversation_count
FROM public.users u
LEFT JOIN public.subscriptions s ON s.user_id = u.id AND s.status = 'active'
LEFT JOIN public.conversations c ON c.user_id = u.id
WHERE u.deleted_at IS NULL
GROUP BY u.id, s.status, s.current_period_end;

-- Usage by mode for a user (last 30 days)
CREATE OR REPLACE VIEW public.v_usage_by_mode AS
SELECT
    user_id,
    mode,
    COUNT(*)                    AS query_count,
    SUM(tokens_input)           AS total_tokens_in,
    SUM(tokens_output)          AS total_tokens_out,
    AVG(latency_ms)             AS avg_latency_ms,
    DATE_TRUNC('day', created_at) AS day
FROM public.usage_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id, mode, DATE_TRUNC('day', created_at);

-- Platform stats (admin dashboard)
CREATE OR REPLACE VIEW public.v_platform_stats AS
SELECT
    (SELECT COUNT(*) FROM public.users WHERE deleted_at IS NULL)                AS total_users,
    (SELECT COUNT(*) FROM public.users WHERE plan = 'pro' AND deleted_at IS NULL)      AS pro_users,
    (SELECT COUNT(*) FROM public.users WHERE plan = 'advanced' AND deleted_at IS NULL) AS advanced_users,
    (SELECT COUNT(*) FROM public.waitlist WHERE invited_at IS NULL)             AS waitlist_pending,
    (SELECT COUNT(*) FROM public.usage_events WHERE created_at >= NOW() - INTERVAL '24 hours') AS queries_today,
    (SELECT COUNT(*) FROM public.usage_events WHERE created_at >= NOW() - INTERVAL '7 days')   AS queries_week,
    (SELECT COALESCE(AVG(latency_ms), 0) FROM public.usage_events WHERE created_at >= NOW() - INTERVAL '24 hours') AS avg_latency_today_ms;

-- ============================================================
--  SEED DATA (development only)
--  Comment out before running in production
-- ============================================================

-- INSERT INTO public.users (clerk_id, email, first_name, last_name, plan)
-- VALUES ('user_dev_seed_001', 'eric@omnigenius.co', 'Eric', 'Martin', 'advanced')
-- ON CONFLICT (clerk_id) DO NOTHING;
