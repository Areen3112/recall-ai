import type React from 'react';
import {
  Cpu,
  Database,
  Brain,
  Zap,
  MessageSquare,
  Layers,
  Lock,
  Workflow,
  FlaskConical,
  Info
} from 'lucide-react';
import { MOCK_INTEGRATIONS } from '../data/mock/integrations';
import { Badge } from '../components/ui/Badge';
import type { IntegrationItem } from '../types';

export const IntegrationsPage: React.FC = () => {
  const statusBadges: Record<IntegrationItem['status'], { label: string; variant: 'emerald' | 'violet' | 'amber' | 'neutral' }> = {
    configured: { label: 'Configured in Demo', variant: 'emerald' },
    available: { label: 'Available', variant: 'violet' },
    not_connected: { label: 'Not Connected', variant: 'neutral' },
    demo_environment: { label: 'Demo Environment', variant: 'amber' },
  };

  const getIntegrationIcon = (category: IntegrationItem['category']) => {
    switch (category) {
      case 'Channels':
        return MessageSquare;
      case 'Storage':
        return Database;
      case 'Memory Core':
        return Brain;
      case 'Inference Engine':
        return Zap;
      case 'CRM':
        return Layers;
      default:
        return Cpu;
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <h1 className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight">
            Integrations & Architecture
          </h1>
          <Badge variant="violet" size="sm">
            <FlaskConical className="w-3 h-3 mr-1" />
            Target Architecture (Demo Mode)
          </Badge>
        </div>
        <p className="text-xs sm:text-sm text-[#92929F] mt-1">
          Architectural specification for multi-tenant workspace isolation, persistent Hindsight memory storage, and Groq inference pipelines.
        </p>
      </div>

      {/* Honest Scope Banner */}
      <div className="p-3.5 rounded-xl bg-[#12121A] border border-white/[0.06] flex items-center justify-between text-xs text-[#92929F]">
        <div className="flex items-center gap-2.5">
          <Info className="w-4 h-4 text-[#9B8CFF] shrink-0" />
          <span>
            Integration status cards describe backend component contracts and simulated endpoints. Private keys and tokens are not held by the client application.
          </span>
        </div>
        <span className="font-mono text-[10px] text-[#626270]">Contract Verified</span>
      </div>

      {/* Architectural Flow Diagram Card */}
      <div className="p-6 rounded-2xl bg-[#12121A] border border-white/[0.08] shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Workflow className="w-4 h-4 text-[#9B8CFF]" />
            <h3 className="text-sm font-semibold text-[#F4F4F7] tracking-tight">
              RECALL AI End-to-End Request Pipeline
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[#B6A9FF] bg-[#9B8CFF]/10 px-2 py-0.5 rounded">
            Target Latency Budget: 1.2s
          </span>
        </div>

        {/* Visual Pipeline Flow */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
          {/* Step 1 */}
          <div className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.06] text-left space-y-1">
            <span className="text-[10px] font-mono text-[#9B8CFF] uppercase">01. Ingestion</span>
            <div className="text-xs font-semibold text-[#F4F4F7]">Support Client</div>
            <p className="text-[11px] text-[#92929F] leading-tight">
              POST /api/v1/chat with signed JWT and workspace UUID headers.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.06] text-left space-y-1">
            <span className="text-[10px] font-mono text-[#10B981] uppercase">02. Identity</span>
            <div className="text-xs font-semibold text-[#F4F4F7]">Supabase RLS</div>
            <p className="text-[11px] text-[#92929F] leading-tight">
              Verifies HS256 identity claims and scopes data strictly to workspace.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-3.5 rounded-xl bg-[#191923] border border-[#9B8CFF]/40 text-left space-y-1 glow-accent-sm">
            <span className="text-[10px] font-mono text-[#B6A9FF] uppercase">03. Recall</span>
            <div className="text-xs font-semibold text-[#B6A9FF]">Hindsight Cloud</div>
            <p className="text-[11px] text-[#92929F] leading-tight">
              Retrieves past memories, customer preferences & failed attempts.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.06] text-left space-y-1">
            <span className="text-[10px] font-mono text-[#F59E0B] uppercase">04. Reasoning</span>
            <div className="text-xs font-semibold text-[#F4F4F7]">Groq Llama 3.3</div>
            <p className="text-[11px] text-[#92929F] leading-tight">
              Generates structured JSON reply conditioned to avoid past failures.
            </p>
          </div>

          {/* Step 5 */}
          <div className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.06] text-left space-y-1">
            <span className="text-[10px] font-mono text-[#10B981] uppercase">05. Retention</span>
            <div className="text-xs font-semibold text-[#F4F4F7]">Memory Retain</div>
            <p className="text-[11px] text-[#92929F] leading-tight">
              Stores outcome, evolving preferences, and reported failures for future sessions.
            </p>
          </div>
        </div>
      </div>

      {/* Integration Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {MOCK_INTEGRATIONS.map((int) => {
          const Icon = getIntegrationIcon(int.category);
          const badge = statusBadges[int.status];

          return (
            <div
              key={int.id}
              className="p-5 rounded-2xl bg-[#12121A] border border-white/[0.07] hover:border-white/[0.14] transition-all flex flex-col justify-between shadow-sm text-left"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="p-2 rounded-xl bg-[#191923] border border-white/[0.06] text-[#9B8CFF]">
                    <Icon className="w-5 h-5" />
                  </div>
                  <Badge variant={badge.variant} size="sm" dot={int.status === 'configured'}>
                    {badge.label}
                  </Badge>
                </div>

                <div className="text-[10px] font-mono text-[#626270] uppercase mb-0.5">
                  {int.category} • {int.provider}
                </div>

                <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7] mb-1.5">
                  {int.name}
                </h3>

                <p className="text-xs text-[#92929F] leading-relaxed mb-4">
                  {int.description}
                </p>
              </div>

              <div className="pt-3 border-t border-white/[0.05] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px] text-[#626270]">
                  <span>Version / Engine:</span>
                  <span className="text-[#F4F4F7] font-mono">{int.version}</span>
                </div>

                {int.latencyAvg && (
                  <div className="flex items-center justify-between text-[11px] text-[#626270]">
                    <span>Target Budget:</span>
                    <span className="text-[#9B8CFF] font-mono font-medium">{int.latencyAvg}</span>
                  </div>
                )}

                <div className="p-2 rounded-lg bg-[#0D0D13] border border-white/[0.04] text-[11px] text-[#92929F]">
                  {int.details}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Security & Credentials Disclosure */}
      <div className="p-4 rounded-xl bg-[#0D0D13] border border-white/[0.07] flex items-start gap-3 text-xs text-[#92929F]">
        <Lock className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
        <div>
          <strong className="text-[#F4F4F7]">Zero Secret Disclosure Policy: </strong>
          In accordance with enterprise security standards, private encryption keys, Groq API secrets, Supabase service keys, and raw Hindsight Bank authentication credentials remain sealed within the private backend environment.
        </div>
      </div>
    </div>
  );
};
