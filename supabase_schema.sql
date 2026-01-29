-- Agentry Cloud Mode Database Schema
-- Run this in your Supabase SQL editor to set up the required tables

-- =============================================================================
-- Chat Sessions
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT DEFAULT 'New Chat',
    provider TEXT,
    model TEXT,
    model_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast user session lookup
CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at DESC);

-- =============================================================================
-- Chat Messages
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast message retrieval
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON chat_messages(created_at);

-- =============================================================================
-- User Media (for Vercel Blob references)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    filename TEXT,
    blob_url TEXT,
    blob_pathname TEXT,
    content_type TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_user ON user_media(user_id);

-- =============================================================================
-- Request Metrics (Performance tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS request_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    session_id UUID,
    endpoint TEXT,
    method TEXT,
    latency_ms FLOAT,
    tokens_input INTEGER,
    tokens_output INTEGER,
    memory_retrieval_ms FLOAT,
    llm_latency_ms FLOAT,
    status_code INTEGER DEFAULT 200,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_user ON request_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_metrics_created ON request_metrics(created_at);

-- =============================================================================
-- RPC Function: Get User Stats
-- =============================================================================
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_requests', COUNT(*),
        'avg_latency_ms', ROUND(AVG(latency_ms)::numeric, 2),
        'total_tokens', SUM(COALESCE(tokens_input, 0) + COALESCE(tokens_output, 0)),
        'sessions_count', (SELECT COUNT(*) FROM chat_sessions WHERE user_id = p_user_id),
        'messages_count', (
            SELECT COUNT(*) 
            FROM chat_messages m 
            JOIN chat_sessions s ON m.session_id = s.id 
            WHERE s.user_id = p_user_id
        )
    ) INTO result
    FROM request_metrics
    WHERE user_id = p_user_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Row Level Security (RLS) - Optional but recommended
-- Enable RLS on tables for multi-tenant security
-- =============================================================================
-- ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_media ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE request_metrics ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (adjust based on your auth setup):
-- CREATE POLICY "Users can only see their own sessions"
--     ON chat_sessions FOR ALL
--     USING (auth.uid()::text = user_id);
