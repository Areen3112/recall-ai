export type DemoSentiment = 'positive' | 'neutral' | 'negative' | 'frustrated' | 'unknown';

export interface DemoChatRequest {
  session_id: string;
  message: string;
}

export interface DemoChatResponse {
  response: string;
  session_id: string;
  sentiment: DemoSentiment;
  memories_used: string[];
  memory_retrieved: boolean;
  escalation_required: boolean;
  escalation_reason: string | null;
}

export type DemoChatErrorKind = 'network' | 'http' | 'invalid_json' | 'invalid_response';

export interface DemoChatError {
  kind: DemoChatErrorKind;
  message: string;
  status?: number;
}

export type DemoChatResult =
  | {
      ok: true;
      data: DemoChatResponse;
      status: number;
      workflowStatus: string | null;
      memoryStatus: string | null;
    }
  | { ok: false; error: DemoChatError };

const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, '');
const SENTIMENTS = new Set<DemoSentiment>(['positive', 'neutral', 'negative', 'frustrated', 'unknown']);

function createIdempotencyKey(): string {
  if (typeof crypto === 'undefined' || typeof crypto.randomUUID !== 'function') {
    throw new Error('Secure random identifier generation is unavailable.');
  }
  return `sarah-dashboard-${crypto.randomUUID()}`;
}

function isDemoChatResponse(value: unknown, expectedSessionId: string): value is DemoChatResponse {
  if (typeof value !== 'object' || value === null) return false;
  const data = value as Record<string, unknown>;
  return (
    typeof data.response === 'string' &&
    data.response.length > 0 &&
    data.session_id === expectedSessionId &&
    typeof data.sentiment === 'string' &&
    SENTIMENTS.has(data.sentiment as DemoSentiment) &&
    Array.isArray(data.memories_used) &&
    data.memories_used.every((item) => typeof item === 'string') &&
    typeof data.memory_retrieved === 'boolean' &&
    typeof data.escalation_required === 'boolean' &&
    (data.escalation_reason === null || typeof data.escalation_reason === 'string')
  );
}

export async function sendDemoChatMessage(payload: DemoChatRequest): Promise<DemoChatResult> {
  let idempotencyKey: string;
  try {
    idempotencyKey = createIdempotencyKey();
  } catch {
    return {
      ok: false,
      error: {
        kind: 'network',
        message: 'Secure request setup is unavailable in this browser.',
      },
    };
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/demo/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
      },
      body: JSON.stringify({ session_id: payload.session_id, message: payload.message }),
    });
  } catch {
    return {
      ok: false,
      error: {
        kind: 'network',
        message: 'Could not reach the demo backend. Check that it is running, then try again.',
      },
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      error: {
        kind: 'http',
        status: response.status,
        message: `The demo backend could not complete this request (HTTP ${response.status}).`,
      },
    };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      ok: false,
      error: { kind: 'invalid_json', status: response.status, message: 'The backend returned an unreadable response.' },
    };
  }

  if (!isDemoChatResponse(body, payload.session_id)) {
    return {
      ok: false,
      error: { kind: 'invalid_response', status: response.status, message: 'The backend response had an unexpected format.' },
    };
  }

  return {
    ok: true,
    data: body,
    status: response.status,
    workflowStatus: response.headers.get('X-Workflow-Status'),
    memoryStatus: response.headers.get('X-Memory-Status'),
  };
}
