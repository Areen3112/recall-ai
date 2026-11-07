-- PROPOSAL ONLY. Do not run until reviewed and approved.
-- This is a one-time transactional migration. Execute the complete file in one
-- PostgreSQL session; do not split it into autocommitted statements or rerun it
-- automatically. If a statement fails before COMMIT, PostgreSQL rolls back this
-- transaction, including its DDL and count backfill. Resolve the reported cause
-- and execute the complete file again. If the connection is lost around COMMIT,
-- inspect migration history, indexes, trigger, and counts before taking action;
-- do not blindly rerun this file.

BEGIN;

-- Hold these locks through COMMIT. Existing writers finish before the backfill;
-- concurrent conversation/message/ticket writes wait until the trigger and unique
-- indexes are installed, so there is no insert gap between backfill and trigger.
LOCK TABLE public.conversations, public.messages, public.support_tickets
    IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.support_tickets
        WHERE conversation_id IS NOT NULL
          AND status IN ('open', 'in_progress', 'waiting')
        GROUP BY workspace_id, conversation_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate active tickets exist; review and resolve them before migration';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.support_tickets AS ticket
        JOIN public.conversations AS conversation
          ON conversation.workspace_id = ticket.workspace_id
         AND conversation.id = ticket.conversation_id
        WHERE ticket.conversation_id IS NOT NULL
          AND ticket.status IN ('open', 'in_progress', 'waiting')
          AND ticket.customer_id IS DISTINCT FROM conversation.customer_id
    ) THEN
        RAISE EXCEPTION 'Active ticket/customer relationships need review before migration';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.messages
        WHERE role IN ('customer', 'assistant')
          AND jsonb_typeof(metadata -> 'idempotency_key') = 'string'
        GROUP BY workspace_id, conversation_id, role, metadata ->> 'idempotency_key'
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate message idempotency keys exist; review them before migration';
    END IF;
END;
$$;

-- Reconcile the existing counter while conversation inserts are blocked.
UPDATE public.customers AS customer
SET total_conversations = (
    SELECT COUNT(*)::integer
    FROM public.conversations AS conversation
    WHERE conversation.workspace_id = customer.workspace_id
      AND conversation.customer_id = customer.id
);

-- The backend stores the same string key in metadata for the customer and
-- assistant message; role distinguishes the two unique rows per request.
CREATE UNIQUE INDEX uq_messages_chat_idempotency
ON public.messages (
    workspace_id,
    conversation_id,
    role,
    (metadata ->> 'idempotency_key')
)
WHERE role IN ('customer', 'assistant')
  AND jsonb_typeof(metadata -> 'idempotency_key') = 'string';

-- This matches current repository behavior: one active ticket per conversation.
-- Resolved/closed tickets do not block a later escalation for that conversation.
CREATE UNIQUE INDEX uq_support_tickets_active_conversation
ON public.support_tickets (workspace_id, conversation_id)
WHERE conversation_id IS NOT NULL
  AND status IN ('open', 'in_progress', 'waiting');

CREATE FUNCTION public.recall_ai_count_customer_conversation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NEW.customer_id IS NOT NULL THEN
        UPDATE public.customers
        SET total_conversations = COALESCE(total_conversations, 0) + 1
        WHERE workspace_id = NEW.workspace_id
          AND id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$;

-- The trigger fires once for each committed new row. Existing rows were handled
-- by the backfill above; conflict/reuse paths do not insert another conversation.
CREATE TRIGGER trg_recall_ai_count_customer_conversation
AFTER INSERT ON public.conversations
FOR EACH ROW
EXECUTE FUNCTION public.recall_ai_count_customer_conversation();

COMMIT;
