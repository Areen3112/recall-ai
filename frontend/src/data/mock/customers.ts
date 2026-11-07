import type { Customer } from '../../types';

export const MOCK_CUSTOMERS: Customer[] = [
  {
    id: 'cust-sarah-mitchell-01',
    name: 'Sarah Mitchell',
    email: 'sarah.mitchell@craftdesign.io',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    customerSince: 'March 2024',
    status: 'active',
    sentiment: 'neutral',
    conversationCount: 3,
    memoryCount: 6,
    failedAttemptsCount: 1,
    lastInteraction: '12 mins ago',
    deviceInfo: {
      model: 'Apex Pro ANC Headphones (Matte Black)',
      os: 'macOS Sequoia 15.1 / iOS 18.2',
      serial: 'APX-7749-MB',
      firmware: 'v3.1.2-rc4'
    },
    preferences: [
      'Prefers bullet-point diagnostic steps',
      'Uses device primarily for Zoom and Figma calls',
      'Declined phone callback in previous ticket; prefers async text'
    ],
    reportedIssues: [
      {
        id: 'iss-sm-01',
        title: 'Bluetooth disconnection every 10 minutes',
        date: 'Nov 07, 2026',
        status: 'active'
      },
      {
        id: 'iss-sm-02',
        title: 'Left ear cup proximity sensor sensitivity',
        date: 'Oct 14, 2026',
        status: 'resolved'
      }
    ],
    notes: 'Key demo customer demonstrating cross-session learning and avoidance of failed repair steps.'
  },
  {
    id: 'cust-david-chen-02',
    name: 'David Chen',
    email: 'd.chen@synthetix.systems',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    customerSince: 'January 2024',
    status: 'vip',
    sentiment: 'positive',
    conversationCount: 7,
    memoryCount: 9,
    failedAttemptsCount: 0,
    lastInteraction: '2 hours ago',
    deviceInfo: {
      model: 'Apex Pro Studio ANC',
      os: 'Arch Linux (Kernel 6.11) / Android 15',
      serial: 'APX-9901-SL',
      firmware: 'v3.2.0'
    },
    preferences: [
      'Software engineer; appreciates technical terminal logs and hex codes',
      'Uses LDAC high-res audio codec',
      'Requested beta firmware track enrollment'
    ],
    reportedIssues: [
      {
        id: 'iss-dc-01',
        title: 'PipeWire audio sink buffer underrun over A2DP',
        date: 'Nov 06, 2026',
        status: 'resolved'
      }
    ],
    notes: 'Enrolled in Developer Preview Program. Consistently provides telemetry dumps.'
  },
  {
    id: 'cust-elena-rostova-03',
    name: 'Elena Rostova',
    email: 'elena.rostova@auroracap.com',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    customerSince: 'June 2024',
    status: 'active',
    sentiment: 'positive',
    conversationCount: 4,
    memoryCount: 5,
    failedAttemptsCount: 0,
    lastInteraction: 'Yesterday',
    deviceInfo: {
      model: 'Recall Wireless Buds Ultra',
      os: 'iOS 18.2',
      serial: 'BUD-4102-WH',
      firmware: 'v2.0.8'
    },
    preferences: [
      'Sensitive to high clamping force and firm silicone tips',
      'Prefers Memory Foam small size tips',
      'Travels frequently across European timezones'
    ],
    reportedIssues: [
      {
        id: 'iss-er-01',
        title: 'Replacement foam tip kit shipped to Zurich address',
        date: 'Nov 02, 2026',
        status: 'resolved'
      }
    ]
  },
  {
    id: 'cust-marcus-vance-04',
    name: 'Marcus Vance',
    email: 'marcus.v@hyperplane.co',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    customerSince: 'September 2024',
    status: 'churn_risk',
    sentiment: 'frustrated',
    conversationCount: 5,
    memoryCount: 8,
    failedAttemptsCount: 2,
    lastInteraction: '45 mins ago',
    deviceInfo: {
      model: 'Apex Pro ANC Headphones (Space Gray)',
      os: 'Windows 11 Enterprise (Build 24H2) / macOS 15',
      serial: 'APX-6512-SG',
      firmware: 'v3.1.1'
    },
    preferences: [
      'Needs dual multipoint switching between Work PC and Personal MacBook',
      'Expressed frustration with multiple generic reboot suggestions',
      'Prefers direct tier-2 engineering escalation'
    ],
    reportedIssues: [
      {
        id: 'iss-mv-01',
        title: 'Multipoint audio handoff fails when Teams call rings',
        date: 'Nov 07, 2026',
        status: 'investigating'
      }
    ],
    notes: 'Escalation trigger active: 2 repeated failure reports with Windows Bluetooth driver stack.'
  },
  {
    id: 'cust-priya-patel-05',
    name: 'Priya Patel',
    email: 'priya.patel@novabio.org',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    customerSince: 'February 2024',
    status: 'vip',
    sentiment: 'positive',
    conversationCount: 12,
    memoryCount: 14,
    failedAttemptsCount: 0,
    lastInteraction: '3 hours ago',
    deviceInfo: {
      model: 'Recall Enterprise Fleet (65 Seats)',
      os: 'Mixed Managed Fleet',
      serial: 'ENT-FLT-2024-NVA',
      firmware: 'v3.1.2-fleet'
    },
    preferences: [
      'IT Director managing departmental deployment',
      'Requires silent background MDM firmware updates',
      'Primary contact for quarterly hardware audits'
    ],
    reportedIssues: [
      {
        id: 'iss-pp-01',
        title: 'Bulk provision token generation for Boston lab',
        date: 'Nov 05, 2026',
        status: 'resolved'
      }
    ]
  }
];
