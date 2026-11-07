import type { ChatRequestPayload, ChatHeaders, ChatResponsePayload } from './types';

export class ChatApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Sends a message to the backend chat API conforming to contracts/api-spec.yaml.
   * Requires valid signed token & workspace headers when interacting with a live backend.
   */
  async sendMessage(
    payload: ChatRequestPayload,
    headers: ChatHeaders
  ): Promise<{ data: ChatResponsePayload | null; error: string | null; status: number }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': headers['X-Workspace-ID'],
          'Idempotency-Key': headers['Idempotency-Key'],
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({ detail: response.statusText }));
        return {
          data: null,
          error: errorJson.detail || `Server error (${response.status})`,
          status: response.status,
        };
      }

      const data: ChatResponsePayload = await response.json();
      return { data, error: null, status: response.status };
    } catch (err) {
      return {
        data: null,
        error: err instanceof Error ? err.message : 'Network request failed',
        status: 0,
      };
    }
  }

  /**
   * Healthcheck endpoint
   */
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, { method: 'GET' });
      return res.ok;
    } catch {
      return false;
    }
  }
}

export const chatApiClient = new ChatApiClient();
