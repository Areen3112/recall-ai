import type React from 'react';
import {
  Brain,
  AlertTriangle,
  ArrowRight,
  FlaskConical,
  Zap
} from 'lucide-react';
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import {
  OVERVIEW_METRICS,
  CONVERSATION_TIMELINE_DATA,
  SENTIMENT_DISTRIBUTION_DATA
} from '../data/mock/analytics';
import { MOCK_ACTIVITIES } from '../data/mock/activities';
import { MOCK_CONVERSATIONS } from '../data/mock/conversations';
import { Badge } from '../components/ui/Badge';
import type { NavigationPage } from '../types';
import { MemoryGraphVisualizer } from '../components/memory/MemoryGraphVisualizer';

export interface OverviewPageProps {
  onNavigate: (page: NavigationPage) => void;
  onSelectConversation?: (id: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigate,
  onSelectConversation,
}) => {
  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-[#12121A] border border-white/[0.08] p-6 sm:p-8 shadow-xl">
        {/* Ambient subtle intelligence background glow */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-[#9B8CFF]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-[#10B981]/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl space-y-3">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium tracking-tight bg-[#9B8CFF]/10 text-[#B6A9FF] border border-[#9B8CFF]/25">
                <FlaskConical className="w-3.5 h-3.5 text-[#9B8CFF]" />
                DEMO ENVIRONMENT
              </span>
              <span className="text-[11px] font-mono text-[#626270]">Synthetic Demonstration Dataset</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F4F4F7] tracking-tight">
              Customer intelligence, with memory.
            </h1>

            <p className="text-sm sm:text-base text-[#92929F] leading-relaxed">
              Every conversation makes your support agent smarter. Every customer interaction becomes context for the next. Your customers never have to explain themselves twice.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => onNavigate('inbox')}
                className="px-4 py-2 rounded-lg bg-[#9B8CFF] hover:bg-[#B6A9FF] text-[#09090D] font-semibold text-xs sm:text-sm flex items-center gap-2 transition-all shadow-sm hover:shadow-[0_0_16px_rgba(155,140,255,0.35)] cursor-pointer"
              >
                <span>Open Support Inbox</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onNavigate('memory-explorer')}
                className="px-4 py-2 rounded-lg bg-[#191923] hover:bg-[#21212E] text-[#F4F4F7] border border-white/[0.08] text-xs sm:text-sm font-medium flex items-center gap-2 transition-all cursor-pointer"
              >
                <Brain className="w-4 h-4 text-[#9B8CFF]" />
                <span>Explore Memory Console</span>
              </button>
            </div>
          </div>

          {/* Quick Memory Pulse Graphic */}
          <div className="w-full lg:w-80 shrink-0 bg-[#0D0D13]/80 rounded-xl border border-white/[0.07] p-4 text-xs space-y-2.5">
            <div className="flex items-center justify-between text-[#626270] font-mono text-[11px]">
              <span>DEMO SCENARIO STATE</span>
              <span className="text-[#B6A9FF]">SIMULATED</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#9B8CFF]/15 border border-[#9B8CFF]/30 flex items-center justify-center shrink-0">
                <Brain className="w-5 h-5 text-[#B6A9FF]" />
              </div>
              <div className="min-w-0">
                <div className="text-[#F4F4F7] font-semibold truncate">Sarah Mitchell Profile</div>
                <div className="text-[11px] text-[#FB7185] flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>1 Failed attempt avoidance active</span>
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-[#626270]">
              <span>Prior failed step avoidance</span>
              <span className="text-[#9B8CFF] font-mono">Enforced</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Section Header with Truthful Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
        <div>
          <h2 className="text-sm font-bold text-[#F4F4F7] uppercase tracking-wider">
            Illustrative Performance Metrics
          </h2>
          <p className="text-xs text-[#92929F]">
            Demonstration baseline data illustrating persistent memory retrieval and response velocity.
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#626270] bg-[#12121A] px-2 py-0.5 rounded border border-white/[0.06] shrink-0">
          Synthetic Demo Metrics
        </span>
      </div>

      {/* 6 High-Quality Metric Components */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {OVERVIEW_METRICS.map((metric, idx) => (
          <div
            key={idx}
            className="rounded-xl bg-[#12121A] border border-white/[0.07] p-3.5 sm:p-4 hover:border-white/[0.12] transition-colors"
          >
            <div className="text-[11px] text-[#92929F] truncate font-medium">{metric.label}</div>
            <div className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight mt-1 font-mono">
              {metric.value}
            </div>
            <div className="flex items-center gap-1.5 mt-2 text-[11px]">
              <span
                className={`font-semibold font-mono ${
                  metric.isPositive ? 'text-[#34D399]' : 'text-[#FB7185]'
                }`}
              >
                {metric.change}
              </span>
              <span className="text-[#626270] truncate text-[10px]">{metric.trend}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Visual Graph of Persistent Memory */}
      <MemoryGraphVisualizer />

      {/* Main Analytics Area: Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversation Activity & Memory Retrievals Over Time (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 sm:p-6 space-y-4 shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7] tracking-tight">
                Simulated Conversation & Memory Trends
              </h3>
              <p className="text-xs text-[#92929F]">
                Demonstration activity modeling how long-term memory lookup scales with conversation volume
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono text-[#92929F]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#9B8CFF]" />
                Memories Recalled
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                Resolved
              </span>
            </div>
          </div>

          <div className="h-64 sm:h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CONVERSATION_TIMELINE_DATA}>
                <defs>
                  <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#9B8CFF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#9B8CFF" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="resolvedGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="#626270" fontSize={11} tickLine={false} />
                <YAxis stroke="#626270" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12121A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#F4F4F7',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="memoriesRetrieved"
                  stroke="#9B8CFF"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#memGradient)"
                  name="Memories Recalled"
                />
                <Area
                  type="monotone"
                  dataKey="resolved"
                  stroke="#10B981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#resolvedGradient)"
                  name="Resolved"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Distribution (1 col) */}
        <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 sm:p-6 space-y-4 shadow-md flex flex-col justify-between">
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7] tracking-tight">
              Customer Sentiment Sample
            </h3>
            <p className="text-xs text-[#92929F]">
              Demonstration classification distribution
            </p>
          </div>

          <div className="h-48 w-full relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={SENTIMENT_DISTRIBUTION_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {SENTIMENT_DISTRIBUTION_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12121A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#F4F4F7',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute text-center">
              <span className="text-2xl font-bold font-mono text-[#F4F4F7]">64%</span>
              <span className="block text-[10px] text-[#34D399] uppercase font-semibold">Positive</span>
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-white/[0.05]">
            {SENTIMENT_DISTRIBUTION_DATA.map((s) => (
              <div key={s.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-[#92929F]">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                  {s.name}
                </span>
                <span className="font-mono text-[#F4F4F7] font-medium">{s.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2-Column Section: Recent Conversations & Agent Telemetry Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Conversations */}
        <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 sm:p-6 space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7] tracking-tight">
                Demonstration Conversations
              </h3>
              <p className="text-xs text-[#92929F]">
                Sample support threads conditioned on persistent memory
              </p>
            </div>
            <button
              onClick={() => onNavigate('inbox')}
              className="text-xs text-[#B6A9FF] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Inbox</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5">
            {MOCK_CONVERSATIONS.slice(0, 4).map((conv) => (
              <div
                key={conv.id}
                onClick={() => {
                  if (onSelectConversation) onSelectConversation(conv.id);
                  onNavigate('inbox');
                }}
                className="p-3.5 rounded-xl bg-[#191923] border border-white/[0.05] hover:border-[#9B8CFF]/40 transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2 truncate">
                    <img
                      src={conv.customerAvatar}
                      alt={conv.customerName}
                      className="w-5 h-5 rounded-full object-cover shrink-0"
                    />
                    <span className="text-xs font-semibold text-[#F4F4F7] group-hover:text-[#B6A9FF] transition-colors truncate">
                      {conv.customerName}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#626270] font-mono shrink-0">
                    {conv.lastActivity}
                  </span>
                </div>

                <p className="text-xs text-[#92929F] line-clamp-1 leading-snug">
                  {conv.title}
                </p>

                <div className="mt-2 flex items-center gap-2">
                  <Badge
                    variant={
                      conv.sentiment === 'positive'
                        ? 'emerald'
                        : conv.sentiment === 'frustrated'
                        ? 'rose'
                        : 'violet'
                    }
                    size="sm"
                  >
                    {conv.sentiment}
                  </Badge>
                  {conv.relevantMemories.some((m) => m.isFailedAttempt) && (
                    <span className="text-[10px] text-[#FB7185] bg-[#F43F5E]/10 border border-[#F43F5E]/20 px-1.5 py-0.2 rounded font-medium flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Failed Step Stored
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Agent Activity */}
        <div className="rounded-2xl bg-[#12121A] border border-white/[0.08] p-5 sm:p-6 space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7] tracking-tight">
                Simulated Agent Events
              </h3>
              <p className="text-xs text-[#92929F]">
                Demonstration stream of memory lookups and orchestration steps
              </p>
            </div>
            <button
              onClick={() => onNavigate('activity')}
              className="text-xs text-[#B6A9FF] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>Activity Stream</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {MOCK_ACTIVITIES.slice(0, 5).map((act) => (
              <div
                key={act.id}
                className="flex items-start gap-3 p-2.5 rounded-lg bg-[#191923] border border-white/[0.04]"
              >
                <div
                  className={`p-1.5 rounded-md shrink-0 mt-0.5 ${
                    act.type === 'failed_attempt_recognition'
                      ? 'bg-[#F43F5E]/15 text-[#FB7185]'
                      : act.type === 'escalation'
                      ? 'bg-[#F59E0B]/15 text-[#FBBF24]'
                      : act.type === 'memory_retrieval'
                      ? 'bg-[#9B8CFF]/15 text-[#B6A9FF]'
                      : 'bg-white/[0.06] text-[#92929F]'
                  }`}
                >
                  {act.type === 'failed_attempt_recognition' ? (
                    <AlertTriangle className="w-3.5 h-3.5" />
                  ) : (
                    <Zap className="w-3.5 h-3.5" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-medium text-[#F4F4F7] truncate">
                      {act.customer}
                    </span>
                    <span className="text-[10px] text-[#626270] font-mono shrink-0">
                      {act.timestamp}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#92929F] mt-0.5 line-clamp-1">
                    {act.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
