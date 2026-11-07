import type React from 'react';
import { ShieldAlert, Ban, Info } from 'lucide-react';
import type { Memory } from '../../types';

export interface FailedAttemptBannerProps {
  memory: Memory;
  compact?: boolean;
}

export const FailedAttemptBanner: React.FC<FailedAttemptBannerProps> = ({
  memory,
  compact = false,
}) => {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-[#F43F5E]/15 via-[#19121E] to-[#12121A] border border-[#F43F5E]/40 p-3.5 sm:p-4 glow-rose-sm text-left">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-[#F43F5E]/20 border border-[#F43F5E]/30 text-[#FB7185] shrink-0 mt-0.5">
          <Ban className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase bg-[#F43F5E]/20 text-[#FF6B8B] border border-[#F43F5E]/40">
              FAILED TROUBLESHOOTING STEP
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-white/[0.05] text-[#92929F] border border-white/[0.08]">
              Source: {memory.source}
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#F59E0B]/10 text-[#FBBF24] border border-[#F59E0B]/20">
              {memory.verification}
            </span>
          </div>

          <h4 className="text-xs sm:text-sm font-semibold text-[#F4F4F7] tracking-tight">
            {memory.title}
          </h4>

          <p className="text-xs text-[#92929F] mt-1 leading-relaxed">
            {memory.content}
          </p>

          {!compact && memory.avoidAction && (
            <div className="mt-2.5 p-2.5 rounded-lg bg-[#09090D]/80 border border-[#F43F5E]/25 flex items-start gap-2 text-xs">
              <ShieldAlert className="w-3.5 h-3.5 text-[#FB7185] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#FF6B8B]">Recall Agent Rule: </span>
                <span className="text-[#F4F4F7]">{memory.avoidAction}</span>
              </div>
            </div>
          )}

          <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[#626270]">
            <span>Related: <strong className="text-[#92929F]">{memory.relatedIssue}</strong></span>
            <span>Session: <code className="font-mono text-[#9B8CFF]">{memory.sessionId.slice(0, 18)}...</code></span>
            <span>Recorded: {memory.timestamp}</span>
          </div>

          <div className="mt-2 pt-2 border-t border-white/[0.05] flex items-center gap-1.5 text-[10px] text-[#FBBF24]">
            <Info className="w-3 h-3 shrink-0" />
            <span>Customer-reported outcome: Logged to avoid customer repetition. Not verified by diagnostic telemetry.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
