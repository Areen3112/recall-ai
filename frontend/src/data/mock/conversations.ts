import type { Conversation } from '../../types';
import { MOCK_MEMORIES } from './memories';

export const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-sarah-session-02',
    customerId: 'cust-sarah-mitchell-01',
    customerName: 'Sarah Mitchell',
    customerEmail: 'sarah.mitchell@craftdesign.io',
    customerAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    title: 'Recurring Bluetooth Disconnections (Cross-Session Follow-up)',
    preview: 'My Bluetooth headphones disconnected again. Based on my previous support history, what different step should I try?',
    status: 'open',
    priority: 'urgent',
    sentiment: 'neutral',
    lastActivity: '12m ago',
    unread: true,
    sessionId: 'sarah-demo-v2-recall-session-9821',
    relevantMemories: [
      MOCK_MEMORIES[0], // Failed attempt: Bluetooth forget & repair failed
      MOCK_MEMORIES[1], // Preferred communication channel
      MOCK_MEMORIES[2], // Workstation info
      MOCK_MEMORIES[3], // Recurring disconnection
    ],
    messages: [
      {
        id: 'msg-sm-201',
        sender: 'customer',
        text: 'My Bluetooth headphones disconnected again. Based on my previous support history, what different troubleshooting step should I try?',
        timestamp: '16:40 UTC',
        sentiment: 'neutral',
      },
      {
        id: 'msg-sm-202',
        sender: 'agent',
        text: `Hello Sarah, welcome back.

I see from your previous session that **restarting Bluetooth and forgetting/re-pairing your Apex Pro headphones in macOS did not resolve the 10-minute disconnections**. I will not ask you to repeat that step.

Given your specific hardware setup (Apex Pro ANC on MacBook Pro M2 Max / macOS Sequoia 15.1), here are the next targeted procedures:

### Step 1: Device-Specific Controller Reset (Apex Pro only)
*Note: This procedure applies exclusively to Apex Pro hardware; do not apply to other models.*
1. Power down your Apex Pro headphones completely.
2. Press and hold both the **Power** button (Right cup) and **ANC Mode** button (Left cup) simultaneously for **12 continuous seconds**.
3. Release when the LED ring flashes alternating amber and white twice. This clears internal L2CAP state tables without unpairing devices.

### Step 2: Advanced Host Daemon Restart (macOS only)
> [!CAUTION] Host Command (macOS only): This command terminates and restarts the system CoreBluetooth daemon. It will temporarily drop all active Bluetooth peripherals (keyboards, trackpads, mice) for 2 to 3 seconds. Run this only if Step 1 does not hold the connection past 15 minutes.
\`\`\`bash
sudo pkill -9 bluetoothd
\`\`\`

If neither procedure resolves the 10-minute drop, we will skip further client-side troubleshooting and initiate an expedited warranty replacement exchange.`,
        timestamp: '16:41 UTC',
        sentiment: 'positive',
        memoriesUsed: [
          'mem-sm-failed-01: Bluetooth Forget & Re-pair Failed (Customer Report - Not independently verified)',
          'mem-sm-fact-01: MacBook Pro M2 Max / macOS Sequoia 15.1 (Diagnostic Log)',
          'mem-sm-pref-01: Prefers concise bulleted diagnostics (Agent Confirmed)'
        ],
        memoryRetrieved: true,
        failedAttemptRecognized: 'bluetooth_repair_forget_and_pair',
        escalationRequired: false,
        escalationReason: null
      }
    ]
  },
  {
    id: 'conv-sarah-session-01',
    customerId: 'cust-sarah-mitchell-01',
    customerName: 'Sarah Mitchell',
    customerEmail: 'sarah.mitchell@craftdesign.io',
    customerAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    title: 'Initial Disconnection Report & Failed Step Recording',
    preview: 'I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. It did not help...',
    status: 'resolved',
    priority: 'high',
    sentiment: 'neutral',
    lastActivity: '45m ago',
    unread: false,
    sessionId: 'sarah-demo-v2-learn-session-4b19',
    relevantMemories: [
      MOCK_MEMORIES[2], // Hardware OS
      MOCK_MEMORIES[3], // Recurring issue
    ],
    messages: [
      {
        id: 'msg-sm-101',
        sender: 'customer',
        text: 'My Bluetooth headphones disconnect about every 10 minutes. Restarting Bluetooth and the headphones did not help. Please suggest one different step: forgetting these headphones in Bluetooth settings and pairing them again.',
        timestamp: '16:25 UTC',
        sentiment: 'neutral'
      },
      {
        id: 'msg-sm-102',
        sender: 'agent',
        text: `I understand the frustration with your Apex Pro dropping connection every 10 minutes.

Let's test the standard re-pair sequence:
1. In macOS **System Settings > Bluetooth**, click the (i) icon next to Apex Pro and choose **"Forget This Device"**.
2. Put your Apex Pro into pairing mode by holding the power button for 5 seconds until the LED pulses blue.
3. Re-pair from your host device list.

Please test this during your next audio call and report back if disconnects persist.`,
        timestamp: '16:26 UTC',
        sentiment: 'neutral',
        memoryRetrieved: true,
        memoriesUsed: ['mem-sm-fact-01: Primary Workstation Hardware & OS (Diagnostic Log)']
      },
      {
        id: 'msg-sm-103',
        sender: 'customer',
        text: 'I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. It did not help; they still disconnect after about 10 minutes.',
        timestamp: '16:32 UTC',
        sentiment: 'frustrated'
      },
      {
        id: 'msg-sm-104',
        sender: 'agent',
        text: `Thank you for reporting back, Sarah.

I have recorded in your persistent profile that the **Bluetooth forget-and-pair procedure did not resolve recurring disconnections**.

*Status: Stored as customer-reported outcome (not independently verified by telemetry). Our automated reasoning will suppress this recommendation in future sessions.*

I am preparing secondary hardware diagnostic steps for your next session.`,
        timestamp: '16:33 UTC',
        sentiment: 'neutral',
        memoryRetrieved: true,
        memoriesUsed: ['mem-sm-failed-01: Logged new failed troubleshooting attempt (Customer Report)']
      }
    ]
  },
  {
    id: 'conv-marcus-01',
    customerId: 'cust-marcus-vance-04',
    customerName: 'Marcus Vance',
    customerEmail: 'marcus.v@hyperplane.co',
    customerAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    title: 'Multipoint Windows 11 Audio Handoff Stutter',
    preview: 'I already tried reinstalling the generic Bluetooth driver. Do not ask me to do that again.',
    status: 'open',
    priority: 'urgent',
    sentiment: 'frustrated',
    lastActivity: '45m ago',
    unread: true,
    sessionId: 'marcus-session-nov07-1120',
    relevantMemories: [
      MOCK_MEMORIES[6], // Failed attempt: Windows Generic Bluetooth driver reset failed
      MOCK_MEMORIES[7], // Strict multipoint priority policy
    ],
    messages: [
      {
        id: 'msg-mv-101',
        sender: 'customer',
        text: 'When Teams receives an incoming call on Windows 11, the audio completely cuts out on both my PC and iPhone. I already tried reinstalling the generic Bluetooth adapter driver as your docs said, and it made no difference. What next?',
        timestamp: '15:42 UTC',
        sentiment: 'frustrated'
      },
      {
        id: 'msg-mv-102',
        sender: 'agent',
        text: `Hello Marcus. I note from your memory record that reinstalling the generic Windows Bluetooth driver has already been attempted and failed. We will not repeat that suggestion.

Because this issue involves multipoint arbitration with Microsoft Teams on Windows 11 Build 24H2, I have flagged this ticket for Tier-2 Audio Systems Escalation (#ESC-4091).

> [!CAUTION] Advanced Workstation Adjustment: Disabling "Allow applications to take exclusive control" in Windows Sound Control Panel will affect spatial audio software. Please await Tier-2 engineering guidance before altering audio registry settings.`,
        timestamp: '15:43 UTC',
        sentiment: 'neutral',
        memoryRetrieved: true,
        memoriesUsed: ['mem-mv-failed-01: Windows Generic Bluetooth Stack Reset Failed (Customer Report)'],
        escalationRequired: true,
        escalationReason: 'Repeated driver failure report on Windows 11 enterprise build + high customer frustration'
      }
    ]
  },
  {
    id: 'conv-david-01',
    customerId: 'cust-david-chen-02',
    customerName: 'David Chen',
    customerEmail: 'd.chen@synthetix.systems',
    customerAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    title: 'PipeWire LDAC Configuration Verification',
    preview: 'The pipewire.conf snippet worked cleanly. Zero packet underruns during a 4-hour session.',
    status: 'resolved',
    priority: 'normal',
    sentiment: 'positive',
    lastActivity: '2h ago',
    unread: false,
    sessionId: 'david-session-nov06-4401',
    relevantMemories: [
      MOCK_MEMORIES[8], // Linux Audio Environment
      MOCK_MEMORIES[9], // WirePlumber LDAC Auto-Negotiation Config
    ],
    messages: [
      {
        id: 'msg-dc-101',
        sender: 'customer',
        text: 'Confirming that the PipeWire configuration fragment you provided yesterday completely resolved the LDAC packet drop. Tested with 96kHz/24bit audio stream without a glitch.',
        timestamp: '14:20 UTC',
        sentiment: 'positive'
      },
      {
        id: 'msg-dc-102',
        sender: 'agent',
        text: `Fantastic to hear, David.

I have retained this resolution configuration under your developer profile in Recall AI.

\`\`\`conf
bluez5.codecs = [ "ldac", "aptx_hd", "aac", "sbc" ]
bluez5.ldac.quality = "hq"
\`\`\`

Should you upgrade PipeWire or test with another kernel, our assistant will preserve this setting as your baseline preference.`,
        timestamp: '14:21 UTC',
        sentiment: 'positive',
        memoryRetrieved: true,
        memoriesUsed: [
          'mem-dc-fact-01: Linux Audio Environment (Customer Report)',
          'mem-dc-res-01: WirePlumber LDAC Auto-Negotiation (Agent Confirmed)'
        ]
      }
    ]
  },
  {
    id: 'conv-priya-01',
    customerId: 'cust-priya-patel-05',
    customerName: 'Priya Patel',
    customerEmail: 'priya.patel@novabio.org',
    customerAvatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    title: 'Enterprise MDM Provisioning Batch (65 Seats)',
    preview: 'Provisioning manifest has been deployed. Awaiting MDM certificate checksum verification.',
    status: 'pending',
    priority: 'normal',
    sentiment: 'positive',
    lastActivity: '3h ago',
    unread: false,
    sessionId: 'priya-session-nov05-3310',
    relevantMemories: [
      MOCK_MEMORIES[11] // Enterprise deployment scope
    ],
    messages: [
      {
        id: 'msg-pp-101',
        sender: 'customer',
        text: 'We are rolling out the v3.1.2 firmware to the first 25 units in the Cambridge lab today. Can you confirm the MDM token is still active?',
        timestamp: '13:00 UTC',
        sentiment: 'positive'
      },
      {
        id: 'msg-pp-102',
        sender: 'agent',
        text: 'Hello Priya. Checked your NovaBio enterprise deployment: your provision token is active through Dec 2026 with 65 licensed seats. Automated silent updates are enabled. Let me know if you need telemetry reports for the rollout.',
        timestamp: '13:02 UTC',
        sentiment: 'positive',
        memoryRetrieved: true,
        memoriesUsed: ['mem-pp-fact-01: Enterprise Deployment Scope & Contract (CRM Sync)']
      }
    ]
  }
];
