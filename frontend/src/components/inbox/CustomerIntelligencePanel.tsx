import type React from 'react';
import {
  Brain,
  Sliders,
  ExternalLink,
  Laptop,
  Ban,
  Sparkles,
} from 'lucide-react';
import type { Customer, Memory } from '../../types';
import { Badge } from '../ui/Badge';
import { FailedAttemptBanner } from '../memory/FailedAttemptBanner';

export interface CustomerIntelligencePanelProps {
  customer: Customer;
  memories: Memory[];
  onNavigateToMemoryExplorer?: (customerId: string) => void;
  isLiveDemoCustomer?: boolean;
}

export const CustomerIntelligencePanel: React.FC<CustomerIntelligencePanelProps> = ({
  customer,
  memories,
  onNavigateToMemoryExplorer,
  isLiveDemoCustomer = false,
}) => {
  const failedAttemptMemories = memories.filter((m) => m.isFailedAttempt);
  const regularMemories = memories.filter((m) => !m.isFailedAttempt);

  if (isLiveDemoCustomer) {
    return (
      <div className="h-full flex flex-col bg-[#0D0D13] border-l border-white/[0.07] overflow-y-auto">
        <div className="p-4 border-b border-white/[0.07] space-y-3 bg-[#101017]">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#9B8CFF]">
            Synthetic Demo Profile
          </span>
          <div className="flex items-center gap-3">
            <img
              src={customer.avatar}
              alt={customer.name}
              className="w-11 h-11 rounded-full object-cover border border-white/[0.1] shadow-sm"
            />
            <div>
              <h3 className="text-sm font-semibold text-[#F4F4F7] tracking-tight">{customer.name}</h3>
              <p className="text-xs text-[#92929F]">Identity is resolved server-side</p>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="flex items-center gap-1.5 mb-2 text-[#B6A9FF]">
            <Sparkles className="w-4 h-4" />
            <h4 className="text-xs font-bold tracking-wider uppercase">Live Memory Results</h4>
          </div>
          <p className="text-[11px] text-[#92929F] leading-relaxed">
            Memory retrieval status and memory identifiers appear on each reply only when returned by the backend.
            This endpoint does not provide a memory inventory or telemetry snapshot.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#0D0D13] border-l border-white/[0.07] overflow-y-auto">
      {/* Customer Header */}
      <div className="p-4 border-b border-white/[0.07] space-y-3 bg-[#101017]">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#9B8CFF]">
            Customer Profile
          </span>
          <Badge
            variant={
              customer.status === 'vip'
                ? 'emerald'
                : customer.status === 'churn_risk'
                ? 'rose'
                : 'violet'
            }
            size="sm"
          >
            {customer.status.toUpperCase()}
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          <img
            src={customer.avatar}
            alt={customer.name}
            className="w-11 h-11 rounded-full object-cover border border-white/[0.1] shadow-sm"
          />
          <div>
            <h3 className="text-sm font-semibold text-[#F4F4F7] tracking-tight">
              {customer.name}
            </h3>
            <p className="text-xs text-[#92929F] truncate max-w-[180px]">{customer.email}</p>
            <div className="flex items-center gap-2 text-[10px] text-[#626270] mt-0.5">
              <span>Since {customer.customerSince}</span>
              <span>•</span>
              <span>{customer.conversationCount} conversations</span>
            </div>
          </div>
        </div>

        {/* Hardware telemetry snapshot if present */}
        {customer.deviceInfo && (
          <div className="p-2 rounded-lg bg-[#14141E] border border-white/[0.05] text-[11px] text-[#92929F] space-y-1">
            <div className="flex items-center gap-1.5 text-[#F4F4F7] font-medium">
              <Laptop className="w-3.5 h-3.5 text-[#9B8CFF]" />
              <span className="truncate">{customer.deviceInfo.model}</span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-[#626270]">
              <span>OS: {customer.deviceInfo.os}</span>
              {customer.deviceInfo.firmware && <span>FW: {customer.deviceInfo.firmware}</span>}
            </div>
          </div>
        )}
      </div>

      {/* Main Intelligence Section */}
      <div className="p-4 space-y-5">
        {/* "WHAT RECALL REMEMBERS" Section */}
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-[#9B8CFF]" />
              <h4 className="text-xs font-bold tracking-wider uppercase text-[#F4F4F7]">
                WHAT RECALL REMEMBERS
              </h4>
            </div>
            <span className="text-[10px] font-mono text-[#9B8CFF] bg-[#9B8CFF]/15 px-1.5 py-0.2 rounded">
              {memories.length} Memories
            </span>
          </div>

          <p className="text-[11px] text-[#92929F] leading-snug mb-3">
            Persistent long-term memories retrieved from Hindsight Cloud to formulate answers without asking the customer to repeat themselves.
          </p>

          {/* FAILED ATTEMPTS HIGHLIGHT - Top Priority */}
          {failedAttemptMemories.length > 0 && (
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-[11px] font-semibold text-[#FB7185]">
                <div className="flex items-center gap-1">
                  <Ban className="w-3.5 h-3.5 text-[#F43F5E]" />
                  <span>Failed Troubleshooting Attempts ({failedAttemptMemories.length})</span>
                </div>
                <span className="text-[10px] font-normal text-[#92929F]">Customer Report</span>
              </div>

              {failedAttemptMemories.map((mem) => (
                <FailedAttemptBanner key={mem.id} memory={mem} compact={false} />
              ))}
            </div>
          )}

          {/* Regular Structured Memories */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold text-[#92929F] uppercase tracking-wider block">
              Preferences & Verified Facts
            </span>

            {regularMemories.map((mem) => (
              <div
                key={mem.id}
                className="p-3 rounded-lg bg-[#14141E] border border-white/[0.05] hover:border-white/[0.1] transition-colors space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[#B6A9FF] capitalize">
                    {mem.category.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] text-[#626270]">
                    {(mem.confidenceScore * 100).toFixed(0)}% conf
                  </span>
                </div>

                <div className="text-xs font-medium text-[#F4F4F7]">{mem.title}</div>
                <p className="text-[11px] text-[#92929F] leading-relaxed">{mem.content}</p>

                <div className="pt-1 flex items-center justify-between text-[10px] text-[#626270]">
                  <span>Source: {mem.source}</span>
                  <span className="text-[#34D399]">{mem.verification}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Customer Preferences List */}
        {customer.preferences && customer.preferences.length > 0 && (
          <div className="pt-3 border-t border-white/[0.06]">
            <h5 className="text-[11px] font-semibold text-[#92929F] uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#9B8CFF]" />
              Interaction Preferences
            </h5>
            <ul className="space-y-1.5">
              {customer.preferences.map((pref, idx) => (
                <li
                  key={idx}
                  className="text-xs text-[#92929F] flex items-start gap-2 bg-[#12121A] p-2 rounded-lg border border-white/[0.04]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#9B8CFF] mt-1.5 shrink-0" />
                  <span>{pref}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Reported Issues History */}
        {customer.reportedIssues && customer.reportedIssues.length > 0 && (
          <div className="pt-3 border-t border-white/[0.06]">
            <h5 className="text-[11px] font-semibold text-[#92929F] uppercase tracking-wider mb-2">
              Reported Issues
            </h5>
            <div className="space-y-1.5">
              {customer.reportedIssues.map((iss) => (
                <div
                  key={iss.id}
                  className="flex items-center justify-between text-xs p-2 rounded-lg bg-[#12121A] border border-white/[0.04]"
                >
                  <div className="truncate mr-2">
                    <div className="text-[#F4F4F7] truncate">{iss.title}</div>
                    <div className="text-[10px] text-[#626270]">{iss.date}</div>
                  </div>
                  <Badge
                    variant={
                      iss.status === 'resolved'
                        ? 'emerald'
                        : iss.status === 'active'
                        ? 'rose'
                        : 'amber'
                    }
                    size="sm"
                  >
                    {iss.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Deep Link to Memory Explorer */}
        {onNavigateToMemoryExplorer && (
          <div className="pt-3 border-t border-white/[0.06]">
            <button
              onClick={() => onNavigateToMemoryExplorer(customer.id)}
              className="w-full py-2 px-3 rounded-lg bg-[#9B8CFF]/15 hover:bg-[#9B8CFF]/25 border border-[#9B8CFF]/30 text-xs font-medium text-[#B6A9FF] flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            >
              <span>Explore all {customer.name} memories</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
