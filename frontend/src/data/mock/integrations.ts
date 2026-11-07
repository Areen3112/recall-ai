import type { IntegrationItem } from '../../types';

export const MOCK_INTEGRATIONS: IntegrationItem[] = [
  {
    id: 'int-widget',
    name: 'Website Support Widget',
    category: 'Channels',
    description: 'Embeddable customer support chat widget with signed session authentication and reactive memory recall.',
    status: 'configured',
    provider: 'Recall Native SDK',
    version: 'v2.4.0',
    details: 'Active on customer portal. Supports JWT-based identity token verification and session persistence.',
    latencyAvg: '45ms',
    healthStatus: 'healthy'
  },
  {
    id: 'int-supabase',
    name: 'Supabase PostgreSQL',
    category: 'Storage',
    description: 'Workspace-isolated relational database storing customer profiles, identity claims, conversation threads, and idempotency audit logs.',
    status: 'configured',
    provider: 'Supabase Managed Cloud',
    version: 'PostgreSQL 16.2',
    details: 'Row-Level Security (RLS) and workspace UUID isolation active. Credentials managed via secure server environment.',
    latencyAvg: '18ms',
    healthStatus: 'healthy'
  },
  {
    id: 'int-hindsight',
    name: 'Hindsight Cloud Memory Core',
    category: 'Memory Core',
    description: 'Persistent-memory intelligence layer implementing Retain, Recall, and Reflect workflows for long-term customer context.',
    status: 'configured',
    provider: 'Hindsight API',
    version: 'v1.4.1 Client',
    details: 'Cross-session memory bank scoped to authenticated workspace. Recognizes previous failed troubleshooting attempts and tracks evolving context.',
    latencyAvg: '135ms',
    healthStatus: 'healthy'
  },
  {
    id: 'int-groq',
    name: 'Groq Inference Engine',
    category: 'Inference Engine',
    description: 'Ultra-low-latency LPU inference delivering fast, structured support reasoning conditioned on retrieved memory.',
    status: 'configured',
    provider: 'Groq Cloud',
    version: 'Llama 3.3 70B Versatile',
    details: 'Strict JSON schema formatting and temperature-controlled generation. Bounded retry and fallbacks configured.',
    latencyAvg: '780ms',
    healthStatus: 'healthy'
  },
  {
    id: 'int-crm-salesforce',
    name: 'Salesforce & Zendesk Sync',
    category: 'CRM',
    description: 'Bi-directional synchronization of customer support tickets, enterprise SLA status, and CRM contact attributes.',
    status: 'available',
    provider: 'Enterprise Connector',
    version: 'v1.0 (Preview)',
    details: 'Roadmap integration. Ready for OAuth2 workspace binding once CRM credentials are configured in workspace settings.',
    healthStatus: 'idle'
  },
  {
    id: 'int-slack',
    name: 'Slack Support Escalations',
    category: 'Channels',
    description: 'Real-time alert webhooks to internal support triage channels when high customer frustration or repeated failed attempts occur.',
    status: 'available',
    provider: 'Slack Incoming Webhooks',
    version: 'v2.0 Webhook API',
    details: 'Pushes rich cards with customer memory provenance when escalation triggers fire.',
    healthStatus: 'idle'
  }
];
