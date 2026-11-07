export type NavigationPage =
  | 'overview'
  | 'inbox'
  | 'customers'
  | 'memory-explorer'
  | 'activity'
  | 'analytics'
  | 'knowledge-base'
  | 'integrations'
  | 'settings';

export type SentimentType = 'positive' | 'neutral' | 'negative' | 'frustrated' | 'unknown';

export type MemoryCategory =
  | 'customer_facts'
  | 'preferences'
  | 'customer_reported_issues'
  | 'failed_attempts'
  | 'successful_resolutions'
  | 'agent_observations'
  | 'historical_context';

export interface DeviceInfo {
  model: string;
  os: string;
  serial?: string;
  firmware?: string;
}

export interface CustomerIssue {
  id: string;
  title: string;
  date: string;
  status: 'resolved' | 'active' | 'investigating';
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  avatar: string;
  customerSince: string;
  status: 'active' | 'pending' | 'churn_risk' | 'vip';
  sentiment: SentimentType;
  conversationCount: number;
  memoryCount: number;
  failedAttemptsCount: number;
  lastInteraction: string;
  deviceInfo?: DeviceInfo;
  preferences: string[];
  reportedIssues: CustomerIssue[];
  notes?: string;
}

export interface Memory {
  id: string;
  customerId: string;
  customerName: string;
  category: MemoryCategory;
  title: string;
  content: string;
  source: 'Customer Report' | 'Agent Synthesis' | 'Support Transcript' | 'CRM Sync' | 'Diagnostic Log';
  verification: 'Not independently verified' | 'Verified by Telemetry' | 'Agent Confirmed' | 'Unverified';
  relatedIssue: string;
  sessionId: string;
  timestamp: string;
  confidenceScore: number;
  recalledCount: number;
  isFailedAttempt: boolean;
  failedActionId?: string;
  avoidAction?: string;
  context?: string;
}

export interface Message {
  id: string;
  sender: 'customer' | 'agent' | 'system';
  text: string;
  timestamp: string;
  sentiment?: SentimentType;
  memoriesUsed?: string[];
  memoryRetrieved?: boolean;
  escalationRequired?: boolean;
  escalationReason?: string | null;
  failedAttemptRecognized?: string;
  isSimulated?: boolean;
}

export interface Conversation {
  id: string;
  customerId: string;
  customerName: string;
  customerEmail: string;
  customerAvatar: string;
  title: string;
  preview: string;
  status: 'open' | 'pending' | 'resolved';
  priority: 'urgent' | 'high' | 'normal' | 'low';
  sentiment: SentimentType;
  lastActivity: string;
  unread: boolean;
  sessionId: string;
  messages: Message[];
  relevantMemories: Memory[];
}

export type ActivityType =
  | 'memory_retrieval'
  | 'customer_identification'
  | 'sentiment_analysis'
  | 'response_generation'
  | 'troubleshooting_recommendation'
  | 'failed_attempt_recognition'
  | 'escalation'
  | 'memory_retention';

export interface AgentActivity {
  id: string;
  type: ActivityType;
  customer: string;
  customerId: string;
  description: string;
  details: string;
  timestamp: string;
  status: 'completed' | 'flagged' | 'pending' | 'skipped';
  latencyMs: number;
  conversationId: string;
  sessionId?: string;
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  slug: string;
  category: 'Hardware' | 'Audio & Connectivity' | 'Account & Billing' | 'Troubleshooting' | 'Policies';
  excerpt: string;
  content: string;
  lastUpdated: string;
  readTime: string;
  indexedInHindsight: boolean;
  tags: string[];
}

export interface IntegrationItem {
  id: string;
  name: string;
  category: 'Channels' | 'Storage' | 'Memory Core' | 'Inference Engine' | 'CRM';
  description: string;
  status: 'configured' | 'available' | 'not_connected' | 'demo_environment';
  provider: string;
  version: string;
  details: string;
  latencyAvg?: string;
  healthStatus?: 'healthy' | 'degraded' | 'idle';
}
