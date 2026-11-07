import { useState } from 'react';
import type React from 'react';
import {
  Brain,
  AlertTriangle,
  ShieldCheck,
  Zap,
  UserCheck,
  Smile,
  Database,
  Filter,
  CheckCircle2,
  FlaskConical
} from 'lucide-react';
import { MOCK_ACTIVITIES } from '../data/mock/activities';
import type { ActivityType } from '../types';
import { Badge } from '../components/ui/Badge';
import { SearchInput } from '../components/ui/SearchInput';

export interface ActivityPageProps {
  onOpenConversation?: (convId: string) => void;
}

export const ActivityPage: React.FC<ActivityPageProps> = ({ onOpenConversation }) => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const typeConfig: Record<ActivityType, { label: string; icon: React.ComponentType<{ className?: string }>; color: 'violet' | 'emerald' | 'amber' | 'rose' | 'neutral' }> = {
    memory_retrieval: { label: 'Memory Retrieval', icon: Brain, color: 'violet' },
    customer_identification: { label: 'Customer Identification', icon: UserCheck, color: 'emerald' },
    sentiment_analysis: { label: 'Sentiment Analysis', icon: Smile, color: 'violet' },
    response_generation: { label: 'Response Generation', icon: Zap, color: 'emerald' },
    troubleshooting_recommendation: { label: 'Recommendation', icon: CheckCircle2, color: 'emerald' },
    failed_attempt_recognition: { label: 'Failed-Attempt Recognition', icon: AlertTriangle, color: 'rose' },
    escalation: { label: 'Escalation Work', icon: ShieldCheck, color: 'amber' },
    memory_retention: { label: 'Memory Retention', icon: Database, color: 'violet' },
  };

  const filtered = MOCK_ACTIVITIES.filter((act) => {
    const matchesType = selectedType === 'all' || act.type === selectedType;
    const matchesSearch =
      act.customer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.details.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight">
              Agent Activity Stream
            </h1>
            <Badge variant="violet" size="sm">
              <FlaskConical className="w-3 h-3 mr-1" />
              Simulated Telemetry
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-[#92929F] mt-1">
            Demonstration event feed modeling memory recall lookups, LLM generation cycles, failed-step detections, and escalation triggers.
          </p>
        </div>

        {/* Status badge */}
        <div className="flex items-center gap-2 bg-[#12121A] px-3 py-1.5 rounded-xl border border-white/[0.06] text-xs">
          <span className="w-2 h-2 rounded-full bg-[#9B8CFF]" />
          <span className="text-[#92929F]">Telemetry Status:</span>
          <span className="font-mono text-[#F4F4F7] font-semibold">Simulated Stream</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#12121A] p-3 rounded-xl border border-white/[0.06]">
        <div className="flex items-center gap-2 flex-wrap flex-1">
          <Filter className="w-4 h-4 text-[#626270]" />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-[#191923] text-xs text-[#F4F4F7] border border-white/[0.08] rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-[#9B8CFF]/50 cursor-pointer"
          >
            <option value="all">All Activity Types</option>
            <option value="failed_attempt_recognition">Failed-Attempt Recognition</option>
            <option value="memory_retrieval">Memory Retrieval</option>
            <option value="response_generation">Response Generation</option>
            <option value="escalation">Escalation Triggered</option>
            <option value="memory_retention">Memory Retention</option>
          </select>
        </div>

        <div className="w-full sm:w-72">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search simulated activities..."
          />
        </div>
      </div>

      {/* Vertical Activity Timeline */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-3 before:bottom-3 before:w-[2px] before:bg-white/[0.07]">
        {filtered.map((act) => {
          const config = typeConfig[act.type];
          const Icon = config.icon;
          const isFailedAttempt = act.type === 'failed_attempt_recognition';

          return (
            <div key={act.id} className="relative group">
              {/* Timeline Node Dot */}
              <div
                className={`absolute -left-6 sm:-left-8 top-3 w-6 h-6 rounded-full flex items-center justify-center border-2 ${
                  isFailedAttempt
                    ? 'bg-[#18111D] border-[#F43F5E] text-[#FB7185] glow-rose-sm'
                    : act.type === 'escalation'
                    ? 'bg-[#1A1813] border-[#F59E0B] text-[#FBBF24]'
                    : 'bg-[#12121A] border-[#9B8CFF] text-[#B6A9FF]'
                }`}
              >
                <Icon className="w-3 h-3" />
              </div>

              {/* Event Card */}
              <div
                className={`rounded-xl p-4 sm:p-5 transition-all text-left ${
                  isFailedAttempt
                    ? 'bg-[#151017] border border-[#F43F5E]/30 glow-rose-sm'
                    : 'bg-[#12121A] border border-white/[0.07] hover:border-white/[0.12]'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={config.color} size="sm">
                      {config.label}
                    </Badge>
                    <span className="text-xs font-semibold text-[#F4F4F7]">
                      {act.customer}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-[#626270] font-mono">
                    <span>{act.timestamp}</span>
                    <span>•</span>
                    <span className="text-[#9B8CFF]">{act.latencyMs}ms budget</span>
                  </div>
                </div>

                <h4 className="text-sm font-semibold text-[#F4F4F7] mb-1">
                  {act.description}
                </h4>

                <p className="text-xs text-[#92929F] leading-relaxed">
                  {act.details}
                </p>

                {/* Footer linking to conversation */}
                <div className="mt-3 pt-2.5 border-t border-white/[0.05] flex items-center justify-between text-[11px]">
                  <span className="text-[#626270] font-mono">
                    Session: {act.sessionId || act.conversationId}
                  </span>

                  {onOpenConversation && (
                    <button
                      onClick={() => onOpenConversation(act.conversationId)}
                      className="text-[#9B8CFF] hover:underline cursor-pointer"
                    >
                      View in Inbox →
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
