
-- ============================================================
-- RECALL AI | Initial Database Schema
-- PostgreSQL / Supabase
-- ============================================================

-- 1. WORKSPACES
CREATE TABLE public.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    public_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    website_url TEXT,
    support_email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. WORKSPACE MEMBERS
CREATE TABLE public.workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'agent'
        CHECK (role IN ('owner', 'admin', 'agent', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, user_id),
    UNIQUE (workspace_id, id)
);

-- 3. CUSTOMERS
CREATE TABLE public.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    external_id TEXT,
    name TEXT,
    email TEXT,
    identity_verified BOOLEAN NOT NULL DEFAULT FALSE,
    total_conversations INTEGER NOT NULL DEFAULT 0,
    last_interaction TIMESTAMPTZ,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (workspace_id, id),
    UNIQUE (workspace_id, external_id),
    UNIQUE (workspace_id, email)
);

-- 4. CONVERSATIONS
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    customer_id UUID,
    session_id TEXT NOT NULL,
    visitor_id TEXT,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'pending', 'resolved', 'closed')),
    sentiment TEXT NOT NULL DEFAULT 'unknown'
        CHECK (sentiment IN ('positive', 'neutral', 'negative', 'frustrated', 'unknown')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    UNIQUE (workspace_id, id),
    UNIQUE (workspace_id, session_id),

    FOREIGN KEY (workspace_id, customer_id)
        REFERENCES public.customers(workspace_id, id)
);

-- 5. MESSAGES
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    role TEXT NOT NULL
        CHECK (role IN ('customer', 'assistant', 'agent', 'system')),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (workspace_id, conversation_id)
        REFERENCES public.conversations(workspace_id, id)
        ON DELETE CASCADE
);

-- 6. SUPPORT TICKETS
CREATE TABLE public.support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    customer_id UUID,
    conversation_id UUID,
    subject TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'waiting', 'resolved', 'closed')),
    priority TEXT NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to UUID REFERENCES auth.users(id),
    resolution_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    FOREIGN KEY (workspace_id, customer_id)
        REFERENCES public.customers(workspace_id, id),

    FOREIGN KEY (workspace_id, conversation_id)
        REFERENCES public.conversations(workspace_id, id)
);

-- 7. AGENT ACTIVITY
CREATE TABLE public.agent_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    customer_id UUID,
    conversation_id UUID,
    event_type TEXT NOT NULL,
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (workspace_id, customer_id)
        REFERENCES public.customers(workspace_id, id),

    FOREIGN KEY (workspace_id, conversation_id)
        REFERENCES public.conversations(workspace_id, id)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_members_user
    ON public.workspace_members(user_id);

CREATE INDEX idx_customers_workspace
    ON public.customers(workspace_id);

CREATE INDEX idx_conversations_customer
    ON public.conversations(workspace_id, customer_id);

CREATE INDEX idx_conversations_status
    ON public.conversations(workspace_id, status);

CREATE INDEX idx_messages_conversation
    ON public.messages(workspace_id, conversation_id, created_at);

CREATE INDEX idx_tickets_workspace_status
    ON public.support_tickets(workspace_id, status);

CREATE INDEX idx_agent_activity_workspace
    ON public.agent_activity(workspace_id, created_at DESC);

-- ============================================================
-- WORKSPACE MEMBERSHIP HELPER
-- SECURITY DEFINER avoids recursive RLS evaluation.
-- ============================================================

CREATE OR REPLACE FUNCTION public.is_workspace_member(
    target_workspace_id UUID
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = target_workspace_id
          AND wm.user_id = (SELECT auth.uid())
    );
$$;

REVOKE ALL ON FUNCTION public.is_workspace_member(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_workspace_member(UUID) TO authenticated;

-- ============================================================
-- ROW LEVEL SECURITY
-- Dashboard users can read only their own workspace data.
-- Backend service-role operations must enforce tenant scope
-- explicitly because service-role access bypasses RLS.
-- ============================================================

ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_activity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Members can read their workspaces"
ON public.workspaces FOR SELECT TO authenticated
USING (public.is_workspace_member(id));

CREATE POLICY "Members can read workspace memberships"
ON public.workspace_members FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Members can read workspace customers"
ON public.customers FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Members can read workspace conversations"
ON public.conversations FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Members can read workspace messages"
ON public.messages FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Members can read workspace tickets"
ON public.support_tickets FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

CREATE POLICY "Members can read workspace activity"
ON public.agent_activity FOR SELECT TO authenticated
USING (public.is_workspace_member(workspace_id));

-- ============================================================
-- END INITIAL MIGRATION
-- ============================================================
