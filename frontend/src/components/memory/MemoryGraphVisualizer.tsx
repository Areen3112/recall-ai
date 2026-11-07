import { useState } from 'react';
import type React from 'react';
import { Brain, Ban, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

export interface MemoryGraphVisualizerProps {
  className?: string;
}

export const MemoryGraphVisualizer: React.FC<MemoryGraphVisualizerProps> = ({ className = '' }) => {
  const [activeNode, setActiveNode] = useState<'customer' | 'failed' | 'rule' | 'resolution'>('failed');

  return (
    <div className={`rounded-xl bg-[#12121A] border border-white/[0.08] p-4 sm:p-5 relative overflow-hidden ${className}`}>
      {/* Background radial gradient */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#9B8CFF]/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-[#9B8CFF]/15 border border-[#9B8CFF]/30 text-[#B6A9FF]">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-semibold text-[#F4F4F7]">
              Persistent Memory Reasoning Graph
            </h4>
            <p className="text-[11px] text-[#92929F]">
              Demonstration flow: Cross-session learning from Sarah Mitchell's reported troubleshooting failure
            </p>
          </div>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#9B8CFF]/15 text-[#B6A9FF] border border-[#9B8CFF]/30">
          Memory Flow (Demo)
        </span>
      </div>

      {/* Interactive Visual Graph Nodes */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 my-4 relative">
        {/* Node 1: Customer & Hardware */}
        <div
          onClick={() => setActiveNode('customer')}
          className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
            activeNode === 'customer'
              ? 'bg-[#191928] border-[#9B8CFF] shadow-[0_0_14px_rgba(155,140,255,0.2)]'
              : 'bg-[#151520] border-white/[0.08] hover:border-white/[0.16]'
          }`}
        >
          <div className="text-[10px] font-mono text-[#9B8CFF] uppercase mb-1">01 / Subject Fact</div>
          <div className="text-xs font-semibold text-[#F4F4F7]">Sarah Mitchell</div>
          <p className="text-[11px] text-[#92929F] mt-1 leading-tight">
            Apex Pro ANC on macOS Sequoia 15.1
          </p>
        </div>

        {/* Node 2: Customer-Reported Failed Attempt */}
        <div
          onClick={() => setActiveNode('failed')}
          className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
            activeNode === 'failed'
              ? 'bg-[#1A1017] border-[#F43F5E] glow-rose-sm'
              : 'bg-[#151520] border-[#F43F5E]/30 hover:border-[#F43F5E]/60'
          }`}
        >
          <div className="text-[10px] font-mono text-[#FB7185] uppercase mb-1 flex items-center gap-1">
            <Ban className="w-3 h-3" />
            <span>02 / Failed Attempt</span>
          </div>
          <div className="text-xs font-semibold text-[#FB7185]">Forget & Re-pair</div>
          <p className="text-[11px] text-[#92929F] mt-1 leading-tight">
            Did not fix disconnects. Customer report (unverified).
          </p>
        </div>

        {/* Node 3: Avoidance Filter */}
        <div
          onClick={() => setActiveNode('rule')}
          className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
            activeNode === 'rule'
              ? 'bg-[#191928] border-[#9B8CFF] shadow-[0_0_14px_rgba(155,140,255,0.2)]'
              : 'bg-[#151520] border-white/[0.08] hover:border-white/[0.16]'
          }`}
        >
          <div className="text-[10px] font-mono text-[#B6A9FF] uppercase mb-1 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" />
            <span>03 / Retention Rule</span>
          </div>
          <div className="text-xs font-semibold text-[#F4F4F7]">Avoidance Filter</div>
          <p className="text-[11px] text-[#92929F] mt-1 leading-tight">
            Suppresses forget_and_pair in future sessions for Sarah.
          </p>
        </div>

        {/* Node 4: Active Next Suggestion */}
        <div
          onClick={() => setActiveNode('resolution')}
          className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
            activeNode === 'resolution'
              ? 'bg-[#0E1B17] border-[#10B981] shadow-[0_0_14px_rgba(16,185,129,0.2)]'
              : 'bg-[#151520] border-[#10B981]/30 hover:border-[#10B981]/60'
          }`}
        >
          <div className="text-[10px] font-mono text-[#34D399] uppercase mb-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>04 / Next Step</span>
          </div>
          <div className="text-xs font-semibold text-[#34D399]">Targeted Reset</div>
          <p className="text-[11px] text-[#92929F] mt-1 leading-tight">
            Apex Pro controller reset + macOS daemon restart.
          </p>
        </div>
      </div>

      {/* Explanatory Callout */}
      <div className="p-3 rounded-lg bg-[#0D0D13] border border-white/[0.06] text-xs flex items-start gap-2.5">
        <Sparkles className="w-4 h-4 text-[#9B8CFF] shrink-0 mt-0.5" />
        <div className="text-[#92929F]">
          <strong className="text-[#F4F4F7]">Persistent Memory Principle: </strong>
          Stateless chatbots reset context every session and repetitively recommend basic steps like forgetting devices.
          RECALL AI queries long-term customer memory first, discovers prior customer-reported failures, and advances directly to higher-tier procedures without customer repetition.
        </div>
      </div>
    </div>
  );
};
