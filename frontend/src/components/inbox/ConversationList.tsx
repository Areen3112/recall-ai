import type React from 'react';
import type { Conversation, SentimentType } from '../../types';
import { SearchInput } from '../ui/SearchInput';
import { Badge } from '../ui/Badge';
import { Sparkles, AlertCircle } from 'lucide-react';

export interface ConversationListProps {
  conversations: Conversation[];
  selectedId: string;
  onSelect: (id: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  statusFilter: 'all' | 'open' | 'pending' | 'resolved';
  onStatusFilterChange: (status: 'all' | 'open' | 'pending' | 'resolved') => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  selectedId,
  onSelect,
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
}) => {
  const sentimentBadges: Record<SentimentType, { variant: 'emerald' | 'violet' | 'rose' | 'amber' | 'neutral'; label: string }> = {
    positive: { variant: 'emerald', label: 'Positive' },
    neutral: { variant: 'violet', label: 'Neutral' },
    negative: { variant: 'rose', label: 'Negative' },
    frustrated: { variant: 'rose', label: 'Frustrated' },
    unknown: { variant: 'neutral', label: 'Unknown' },
  };

  const filtered = conversations.filter((c) => {
    const matchesSearch =
      c.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.preview.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="h-full flex flex-col bg-[#0D0D13] border-r border-white/[0.07] overflow-hidden">
      {/* Header & Filter Controls */}
      <div className="p-3.5 border-b border-white/[0.07] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[#F4F4F7] tracking-tight">Inbox</h2>
            <span className="text-[11px] font-mono text-[#626270] px-1.5 py-0.2 rounded bg-white/[0.05]">
              {filtered.length}
            </span>
          </div>
          <span className="text-[10px] text-[#9B8CFF] font-medium flex items-center gap-1 font-mono">
            <Sparkles className="w-3 h-3" />
            Demo Sessions
          </span>
        </div>

        {/* Search */}
        <SearchInput
          value={searchQuery}
          onChange={onSearchChange}
          placeholder="Filter messages, customer..."
        />

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#12121A] border border-white/[0.05] text-xs">
          {(['all', 'open', 'pending', 'resolved'] as const).map((status) => (
            <button
              key={status}
              onClick={() => onStatusFilterChange(status)}
              className={`flex-1 py-1 text-center font-medium capitalize rounded-md transition-colors cursor-pointer text-xs ${
                statusFilter === status
                  ? 'bg-[#191923] text-[#F4F4F7] shadow-sm'
                  : 'text-[#92929F] hover:text-[#F4F4F7]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Cards List */}
      <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-[#626270] text-xs">
            No conversations match your filter.
          </div>
        ) : (
          filtered.map((conv) => {
            const isSelected = conv.id === selectedId;
            const hasFailedAttempt = conv.relevantMemories.some((m) => m.isFailedAttempt);
            const sentiment = sentimentBadges[conv.sentiment];

            return (
              <div
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`p-3.5 text-left cursor-pointer transition-all relative ${
                  isSelected
                    ? 'bg-[#161622] border-l-2 border-l-[#9B8CFF]'
                    : 'hover:bg-white/[0.02]'
                }`}
              >
                {/* Top Row: Avatar, Name, Timestamp, Unread dot */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2 truncate">
                    <img
                      src={conv.customerAvatar}
                      alt={conv.customerName}
                      className="w-6 h-6 rounded-full object-cover shrink-0"
                    />
                    <span className="text-xs font-semibold text-[#F4F4F7] truncate">
                      {conv.customerName}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-[10px] text-[#626270] font-mono">{conv.lastActivity}</span>
                    {conv.unread && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#9B8CFF] shadow-[0_0_6px_#9B8CFF]" />
                    )}
                  </div>
                </div>

                {/* Title */}
                <h4 className="text-xs font-medium text-[#F4F4F7] truncate mb-1">
                  {conv.title}
                </h4>

                {/* Preview text */}
                <p className="text-[11px] text-[#92929F] line-clamp-2 leading-relaxed mb-2">
                  {conv.preview}
                </p>

                {/* Badges / Intelligence indicators */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <Badge variant={sentiment.variant} size="sm">
                    {sentiment.label}
                  </Badge>

                  {hasFailedAttempt && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#F43F5E]/15 text-[#FF6B8B] border border-[#F43F5E]/30 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      Failed Step Stored
                    </span>
                  )}

                  {conv.priority === 'urgent' && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#F59E0B]/15 text-[#FBBF24]">
                      Urgent
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
