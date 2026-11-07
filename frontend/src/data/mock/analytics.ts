export interface MetricSummary {
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
  trend: string;
  description: string;
}

export const OVERVIEW_METRICS: MetricSummary[] = [
  {
    label: 'Total Conversations',
    value: '1,482',
    change: '+14.2%',
    isPositive: true,
    trend: 'vs last month',
    description: 'Lifetime conversations across web widget and API'
  },
  {
    label: 'Active Conversations',
    value: '24',
    change: '-3',
    isPositive: true,
    trend: 'in live queue',
    description: 'Currently processing or awaiting customer reply'
  },
  {
    label: 'Remembered Customers',
    value: '842',
    change: '+28.4%',
    isPositive: true,
    trend: 'growing memory bank',
    description: 'Customers with persistent long-term memory profiles'
  },
  {
    label: 'Memories Retrieved',
    value: '3,890',
    change: '+42.1%',
    isPositive: true,
    trend: 'context queries',
    description: 'Historical memories pulled prior to agent response generation'
  },
  {
    label: 'Resolution Rate',
    value: '91.4%',
    change: '+6.8%',
    isPositive: true,
    trend: 'first-contact resolution',
    description: 'Issues resolved without repeating previously failed actions'
  },
  {
    label: 'Avg Response Time',
    value: '1.2s',
    change: '-0.4s',
    isPositive: true,
    trend: 'Groq Llama 3.3 pipeline',
    description: 'End-to-end latency including Hindsight memory recall'
  }
];

export const CONVERSATION_TIMELINE_DATA = [
  { day: 'Mon', conversations: 184, memoriesRetrieved: 460, resolved: 168 },
  { day: 'Tue', conversations: 210, memoriesRetrieved: 540, resolved: 194 },
  { day: 'Wed', conversations: 235, memoriesRetrieved: 610, resolved: 218 },
  { day: 'Thu', conversations: 198, memoriesRetrieved: 520, resolved: 182 },
  { day: 'Fri', conversations: 260, memoriesRetrieved: 690, resolved: 242 },
  { day: 'Sat', conversations: 145, memoriesRetrieved: 380, resolved: 135 },
  { day: 'Sun', conversations: 160, memoriesRetrieved: 410, resolved: 149 },
];

export const SENTIMENT_DISTRIBUTION_DATA = [
  { name: 'Positive', value: 64, color: '#10B981' },
  { name: 'Neutral', value: 25, color: '#9B8CFF' },
  { name: 'Frustrated', value: 11, color: '#F43F5E' },
];

export const MEMORY_RETRIEVAL_BY_CATEGORY = [
  { category: 'Customer Facts', count: 1120, fill: '#9B8CFF' },
  { category: 'Preferences', count: 890, fill: '#B6A9FF' },
  { category: 'Reported Issues', count: 740, fill: '#7B68EE' },
  { category: 'Failed Attempts', count: 430, fill: '#F43F5E' },
  { category: 'Resolutions', count: 520, fill: '#10B981' },
  { category: 'Agent Observations', count: 190, fill: '#F59E0B' },
];

export const REPEAT_ISSUE_COMPARISON = [
  { period: 'Week 1', withoutRecall: 38.5, withRecall: 14.2 },
  { period: 'Week 2', withoutRecall: 39.1, withRecall: 11.5 },
  { period: 'Week 3', withoutRecall: 41.0, withRecall: 8.8 },
  { period: 'Week 4', withoutRecall: 42.4, withRecall: 6.2 },
];

export const LATENCY_BREAKDOWN_DATA = [
  { stage: 'Token Verification', latencyMs: 24 },
  { stage: 'Workspace Scope', latencyMs: 18 },
  { stage: 'Hindsight Memory Recall', latencyMs: 135 },
  { stage: 'Groq Reasoning & Gen', latencyMs: 840 },
  { stage: 'Memory Retention Async', latencyMs: 190 },
];
