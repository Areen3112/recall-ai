import type React from 'react';
import {
  Mail,
  Calendar,
  MessageSquare,
  Brain,
  Sliders,
  Ban,
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import type { Customer, Memory, Conversation } from '../../types';
import { Badge } from '../ui/Badge';
import { FailedAttemptBanner } from '../memory/FailedAttemptBanner';

export interface CustomerDetailViewProps {
  customer: Customer;
  memories: Memory[];
  conversations: Conversation[];
  onOpenConversation?: (convId: string) => void;
  onNavigateToMemoryExplorer?: (customerId: string) => void;
}

export const CustomerDetailView: React.FC<CustomerDetailViewProps> = ({
  customer,
  memories,
  conversations,
  onOpenConversation,
  onNavigateToMemoryExplorer,
}) => {
  const failedMemories = memories.filter((m) => m.isFailedAttempt);
  const regularMemories = memories.filter((m) => !m.isFailedAttempt);

  return (
    <div className="h-full overflow-y-auto bg-[#09090D] p-4 sm:p-6 space-y-6">
      {/* Customer Hero Profile Header */}
      <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 sm:p-6 shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <img
              src={customer.avatar}
              alt={customer.name}
              className="w-16 h-16 rounded-2xl object-cover border-2 border-white/[0.1] shadow-lg"
            />
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-xl font-bold text-[#F4F4F7] tracking-tight">
                  {customer.name}
                </h2>
                <Badge
                  variant={
                    customer.status === 'vip'
                      ? 'emerald'
                      : customer.status === 'churn_risk'
                      ? 'rose'
                      : 'violet'
                  }
                  size="md"
                  dot
                >
                  {customer.status.toUpperCase()}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#92929F] mt-1.5">
                <span className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-[#626270]" />
                  {customer.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-[#626270]" />
                  Customer since {customer.customerSince}
                </span>
              </div>
            </div>
          </div>

          {/* Quick stats ribbon */}
          <div className="flex items-center gap-3 bg-[#0D0D13] p-3 rounded-xl border border-white/[0.06]">
            <div className="text-center px-3 border-r border-white/[0.06]">
              <div className="text-base font-bold text-[#F4F4F7] font-mono">
                {customer.conversationCount}
              </div>
              <div className="text-[10px] text-[#626270] uppercase">Convs</div>
            </div>
            <div className="text-center px-3 border-r border-white/[0.06]">
              <div className="text-base font-bold text-[#9B8CFF] font-mono">
                {memories.length}
              </div>
              <div className="text-[10px] text-[#626270] uppercase">Memories</div>
            </div>
            <div className="text-center px-3">
              <div className="text-base font-bold text-[#FB7185] font-mono">
                {failedMemories.length}
              </div>
              <div className="text-[10px] text-[#626270] uppercase">Failed Steps</div>
            </div>
          </div>
        </div>

        {/* Hardware specifications if present */}
        {customer.deviceInfo && (
          <div className="mt-4 pt-4 border-t border-white/[0.06] grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-[#191923] p-2.5 rounded-lg border border-white/[0.04]">
              <span className="text-[#626270] block text-[10px] uppercase font-mono">Hardware Model</span>
              <span className="text-[#F4F4F7] font-medium">{customer.deviceInfo.model}</span>
            </div>
            <div className="bg-[#191923] p-2.5 rounded-lg border border-white/[0.04]">
              <span className="text-[#626270] block text-[10px] uppercase font-mono">Operating System</span>
              <span className="text-[#F4F4F7] font-medium">{customer.deviceInfo.os}</span>
            </div>
            <div className="bg-[#191923] p-2.5 rounded-lg border border-white/[0.04]">
              <span className="text-[#626270] block text-[10px] uppercase font-mono">Firmware / Serial</span>
              <span className="text-[#9B8CFF] font-mono">{customer.deviceInfo.firmware || customer.deviceInfo.serial}</span>
            </div>
          </div>
        )}
      </div>

      {/* 2-Column Intelligence Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Customer Memory & Knowledge */}
        <div className="space-y-5">
          {/* Failed Attempts Section */}
          {failedMemories.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[#FB7185] text-xs font-bold uppercase tracking-wider">
                  <Ban className="w-4 h-4 text-[#F43F5E]" />
                  <span>Reported Failed Attempts ({failedMemories.length})</span>
                </div>
                <span className="text-[10px] font-mono text-[#F43F5E]">Active Avoidance</span>
              </div>
              {failedMemories.map((mem) => (
                <FailedAttemptBanner key={mem.id} memory={mem} />
              ))}
            </div>
          )}

          {/* Long-Term Memory Bank */}
          <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[#9B8CFF]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#F4F4F7]">
                  Persistent Memory Profile
                </h3>
              </div>
              {onNavigateToMemoryExplorer && (
                <button
                  onClick={() => onNavigateToMemoryExplorer(customer.id)}
                  className="text-xs text-[#B6A9FF] hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <span>Memory Explorer</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>

            <div className="space-y-2.5">
              {regularMemories.map((mem) => (
                <div
                  key={mem.id}
                  className="p-3 rounded-xl bg-[#191923] border border-white/[0.05] hover:border-white/[0.1] transition-colors"
                >
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="font-mono text-[#B6A9FF] capitalize">
                      {mem.category.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-[#626270]">
                      {(mem.confidenceScore * 100).toFixed(0)}% conf
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-[#F4F4F7]">{mem.title}</h4>
                  <p className="text-xs text-[#92929F] mt-1 leading-relaxed">{mem.content}</p>
                  <div className="mt-2 pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px] text-[#626270]">
                    <span>Source: {mem.source}</span>
                    <span className="text-[#34D399]">{mem.verification}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Interaction History & Relationship Intelligence */}
        <div className="space-y-5">
          {/* Interaction History Chronological Timeline */}
          <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-[#9B8CFF]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#F4F4F7]">
                  Conversation History
                </h3>
              </div>
              <span className="text-[11px] text-[#626270] font-mono">
                {conversations.length} sessions
              </span>
            </div>

            <div className="space-y-3">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => onOpenConversation && onOpenConversation(conv.id)}
                  className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.05] hover:border-[#9B8CFF]/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-[#F4F4F7] group-hover:text-[#B6A9FF] transition-colors">
                      {conv.title}
                    </span>
                    <span className="text-[10px] text-[#626270] font-mono">{conv.lastActivity}</span>
                  </div>
                  <p className="text-xs text-[#92929F] line-clamp-2 leading-relaxed">
                    {conv.preview}
                  </p>
                  <div className="mt-2 pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px]">
                    <span className="text-[#626270] font-mono">
                      Session: {conv.sessionId.slice(0, 18)}...
                    </span>
                    <span className="text-[#9B8CFF] flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                      Open thread <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Preferences & Relationship Intelligence */}
          <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#9B8CFF]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#F4F4F7]">
                Customer Preferences
              </h3>
            </div>
            <div className="space-y-2">
              {customer.preferences.map((pref, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-[#191923] border border-white/[0.04] text-xs text-[#92929F] flex items-start gap-2.5"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#9B8CFF] mt-1.5 shrink-0" />
                  <span>{pref}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
