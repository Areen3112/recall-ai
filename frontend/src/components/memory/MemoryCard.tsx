import type React from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Tag,
  Sliders,
  FileText,
  Eye,
  Clock,
  Sparkles
} from 'lucide-react';
import type { Memory, MemoryCategory } from '../../types';
import { Badge } from '../ui/Badge';

export interface MemoryCardProps {
  memory: Memory;
  isSelected?: boolean;
  onClick?: () => void;
  showCustomerName?: boolean;
}

export const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  isSelected = false,
  onClick,
  showCustomerName = true,
}) => {
  const categoryConfig: Record<MemoryCategory, { label: string; icon: React.ComponentType<{ className?: string }>; color: 'violet' | 'emerald' | 'amber' | 'rose' | 'neutral' }> = {
    customer_facts: { label: 'Customer Fact', icon: Tag, color: 'violet' },
    preferences: { label: 'Preference', icon: Sliders, color: 'violet' },
    customer_reported_issues: { label: 'Reported Issue', icon: FileText, color: 'amber' },
    failed_attempts: { label: 'Failed Attempt', icon: AlertTriangle, color: 'rose' },
    successful_resolutions: { label: 'Resolution', icon: CheckCircle, color: 'emerald' },
    agent_observations: { label: 'Agent Observation', icon: Eye, color: 'violet' },
    historical_context: { label: 'History', icon: Clock, color: 'neutral' },
  };

  const config = categoryConfig[memory.category];
  const Icon = config.icon;

  return (
    <div
      onClick={onClick}
      className={`relative rounded-xl p-3.5 sm:p-4 text-left transition-all duration-200 cursor-pointer ${
        memory.isFailedAttempt
          ? isSelected
            ? 'bg-[#18111D] border-2 border-[#F43F5E] glow-rose-sm'
            : 'bg-[#140F18] border border-[#F43F5E]/30 hover:border-[#F43F5E]/60'
          : isSelected
          ? 'bg-[#151522] border-2 border-[#9B8CFF] shadow-[0_0_20px_rgba(155,140,255,0.18)]'
          : 'bg-[#12121A] border border-white/[0.07] hover:border-white/[0.14] hover:bg-[#161622]'
      }`}
    >
      {/* Top category & indicators */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <Badge
            variant={memory.isFailedAttempt ? 'failed' : config.color}
            size="sm"
            dot={memory.isFailedAttempt}
          >
            <Icon className="w-3 h-3" />
            <span>{config.label}</span>
          </Badge>

          {showCustomerName && (
            <span className="text-[11px] text-[#92929F] font-medium truncate max-w-[140px]">
              {memory.customerName}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[10px] font-mono text-[#626270]">
            {(memory.confidenceScore * 100).toFixed(0)}% conf
          </span>
          {isSelected && (
            <span className="w-1.5 h-1.5 rounded-full bg-[#9B8CFF] shadow-[0_0_6px_#9B8CFF]" />
          )}
        </div>
      </div>

      {/* Title */}
      <h4 className="text-xs sm:text-sm font-semibold text-[#F4F4F7] tracking-tight line-clamp-1 mb-1">
        {memory.title}
      </h4>

      {/* Snippet */}
      <p className="text-xs text-[#92929F] line-clamp-2 leading-relaxed">
        {memory.content}
      </p>

      {/* Avoidance notice if failed attempt */}
      {memory.isFailedAttempt && memory.avoidAction && (
        <div className="mt-2 text-[11px] text-[#FB7185] bg-[#F43F5E]/10 border border-[#F43F5E]/20 rounded-md px-2 py-1 flex items-center gap-1.5">
          <AlertTriangle className="w-3 h-3 shrink-0" />
          <span className="truncate">Rule: {memory.avoidAction}</span>
        </div>
      )}

      {/* Footer metadata */}
      <div className="mt-3 pt-2 border-t border-white/[0.05] flex items-center justify-between text-[10px] text-[#626270]">
        <div className="flex items-center gap-2">
          <span>Source: {memory.source}</span>
          <span>•</span>
          <span className="text-[#92929F]">{memory.verification}</span>
        </div>
        <div className="flex items-center gap-1 font-mono">
          <Sparkles className="w-3 h-3 text-[#9B8CFF]" />
          <span>Used {memory.recalledCount}x</span>
        </div>
      </div>
    </div>
  );
};
