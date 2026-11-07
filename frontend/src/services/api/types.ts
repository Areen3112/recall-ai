export interface ChatRequestPayload {
  session_id: string;
  message: string;
  customer_id?: string | null;
  visitor_id?: string | null;
  identity_token?: string | null;
}

export interface ChatHeaders {
  'X-Workspace-ID': string;
  'Idempotency-Key': string;
}

export interface ChatResponsePayload {
  response: string;
  session_id: string;
  sentiment: 'positive' | 'neutral' | 'negative' | 'frustrated' | 'unknown';
  memories_used: string[];
  memory_retrieved: boolean;
  escalation_required: boolean;
  escalation_reason: string | null;
}

export interface ApiErrorResponse {
  detail: string;
}
