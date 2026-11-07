import type { KnowledgeArticle } from '../../types';

export const MOCK_KNOWLEDGE_ARTICLES: KnowledgeArticle[] = [
  {
    id: 'kb-01',
    title: 'Troubleshooting Bluetooth Audio Drops & 2.4GHz RF Interference',
    slug: 'troubleshooting-bluetooth-drops-interference',
    category: 'Audio & Connectivity',
    excerpt: 'Detailed diagnosis guide for intermittent disconnections, microwave/Wi-Fi crosstalk, and macOS/Windows audio buffer allocation.',
    content: `### Overview
Bluetooth operates in the 2.4 GHz ISM band. Periodic disconnects (e.g., every 10–12 minutes) typically stem from one of three issues:
1. **Host-side power management**: macOS or Windows placing the USB Bluetooth controller into low-power mode during silent periods.
2. **Channel congestion**: Overlapping 2.4GHz Wi-Fi channels (especially Channel 6 or 11) saturating packet retransmissions.
3. **L2CAP signaling timeout**: Stale packet queues inside the headphone Bluetooth controller.

### Troubleshooting Hierarchy
- **Level 1 (Basic)**: Toggle Bluetooth interface, disconnect auxiliary peripherals.
- **Level 2 (Protocol Reset)**: Forget device from host settings, initiate pairing mode.
- **Level 3 (Hardware Firmware Reset)**: Power down device. Hold Power + ANC buttons for 12 seconds until LEDs flash amber twice.
- **Level 4 (Driver Stack Reinitialization)**: Restart background daemon (\`bluetoothd\` on macOS; restart Bluetooth Support Service on Windows).`,
    lastUpdated: 'Nov 04, 2026',
    readTime: '4 min read',
    indexedInHindsight: true,
    tags: ['Bluetooth', 'macOS', 'Windows', 'Audio Stutter', 'RF Interference']
  },
  {
    id: 'kb-02',
    title: 'Hardware Controller Hard Reset Procedure (Apex Pro & Ultra)',
    slug: 'apex-pro-hardware-controller-hard-reset',
    category: 'Hardware',
    excerpt: 'Step-by-step procedure to reset internal NVRAM, wipe corrupted paired states, and restore default DAC gain stage without voiding warranty.',
    content: `### When to perform a Hard Reset
Perform a hard reset when the device fails to negotiate audio codecs, shows stuck LED indicators, or drops connection continuously despite host reboots.

### Instructions
1. Ensure headphones have at least **20% battery charge**.
2. Disconnect any 3.5mm analog or USB-C charging cables.
3. With the headset powered on, press and hold:
   - **Power button** (Right earcup)
   - **ANC Mode Toggle button** (Left earcup)
4. Maintain hold for **12 continuous seconds**.
5. The LED ring will pulse rapidly in **Amber**, followed by two solid **White flashes**.
6. Release both buttons. The headset will reboot into factory standby mode.`,
    lastUpdated: 'Oct 29, 2026',
    readTime: '3 min read',
    indexedInHindsight: true,
    tags: ['Reset', 'Firmware', 'Apex Pro', 'Factory Default']
  },
  {
    id: 'kb-03',
    title: 'Linux PipeWire & WirePlumber Low-Latency Configuration',
    slug: 'linux-pipewire-wireplumber-low-latency',
    category: 'Troubleshooting',
    excerpt: 'Configuring PipeWire 1.0+ for high-bitrate LDAC, aptX Adaptive, and preventing A2DP buffer underruns.',
    content: `### PipeWire Configuration for Apex Pro
By default, some Linux distributions limit Bluetooth sample rates to 44.1kHz with conservative buffer sizes.

Create or edit \`~/.config/pipewire/pipewire.conf.d/apex-pro.conf\`:
\`\`\`conf
context.properties = {
    default.clock.rate = 48000
    default.clock.quantum = 256
    default.clock.min-quantum = 128
}

bluez5.codecs = [ "ldac", "aptx_hd", "aac", "sbc" ]
bluez5.ldac.quality = "auto" # or "hq" for 990 kbps locked
\`\`\`

Reload PipeWire:
\`\`\`bash
systemctl --user restart pipewire pipewire-pulse wireplumber
\`\`\``,
    lastUpdated: 'Nov 01, 2026',
    readTime: '5 min read',
    indexedInHindsight: true,
    tags: ['Linux', 'PipeWire', 'LDAC', 'WirePlumber', 'Advanced']
  },
  {
    id: 'kb-04',
    title: 'Multipoint Bluetooth Audio Routing & Priority Rules',
    slug: 'multipoint-bluetooth-audio-routing-priority',
    category: 'Audio & Connectivity',
    excerpt: 'How Apex Pro arbitrates incoming phone calls vs desktop media playback across two simultaneously connected hosts.',
    content: `### Multipoint Arbitration Matrix
The headset maintains active connections to two BLE/Classic Bluetooth hosts concurrently.

1. **Voice Call Priority**: Inbound phone calls (HFP/HSP) take absolute precedence over media playback (A2DP).
2. **Media Preemption**: Starting playback on Device B pauses Device A after 1.5s of continuous audio signal.
3. **Known Limitation on Windows 11**: Windows Teams virtual audio sinks may fail to release exclusive audio control. Disabling "Allow applications to take exclusive control" in Sound Control Panel mitigates this.`,
    lastUpdated: 'Oct 15, 2026',
    readTime: '3 min read',
    indexedInHindsight: true,
    tags: ['Multipoint', 'Teams', 'Windows 11', 'Priority']
  },
  {
    id: 'kb-05',
    title: 'Warranty Replacement & RMA Escalation Guidelines',
    slug: 'warranty-replacement-rma-guidelines',
    category: 'Policies',
    excerpt: 'Standard operational procedures for authorizing expedited replacement units when troubleshooting memory records verify hardware fault.',
    content: `### RMA Qualification Criteria
An automated or human agent may approve immediate warranty replacement if:
1. Customer has attempted Level 2 & Level 3 troubleshooting as recorded in **Recall Memory**.
2. Hardware serial is within the 24-month limited warranty window.
3. Diagnostic logs confirm persistent hardware failure (e.g., driver impedance fault, damaged microphone array).`,
    lastUpdated: 'Sep 20, 2026',
    readTime: '4 min read',
    indexedInHindsight: true,
    tags: ['RMA', 'Warranty', 'Policy', 'Support Escalation']
  }
];
