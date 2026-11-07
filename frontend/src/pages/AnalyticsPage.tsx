import { useState } from 'react';
import type React from 'react';
import {
  ArrowUpRight,
  ArrowDownRight,
  Info,
  FlaskConical
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  MEMORY_RETRIEVAL_BY_CATEGORY,
  REPEAT_ISSUE_COMPARISON,
  LATENCY_BREAKDOWN_DATA
} from '../data/mock/analytics';
import { Badge } from '../components/ui/Badge';

export const AnalyticsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight">
              Demonstration Benchmark Analytics
            </h1>
            <Badge variant="violet" size="sm">
              <FlaskConical className="w-3 h-3 mr-1" />
              Simulated Dataset
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-[#92929F] mt-1">
            Simulated comparative models evaluating persistent-memory impact: repeat issue reduction, resolution velocity, and latency budgets.
          </p>
        </div>

        {/* Date range controls */}
        <div className="flex items-center gap-1 bg-[#12121A] p-1 rounded-xl border border-white/[0.06] text-xs">
          {(['24h', '7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                dateRange === range
                  ? 'bg-[#191923] text-[#F4F4F7] shadow-sm'
                  : 'text-[#92929F] hover:text-[#F4F4F7]'
              }`}
            >
              {range === '24h' ? 'Last 24h' : range === '7d' ? 'Last 7 Days' : range === '30d' ? 'Last 30 Days' : 'Quarter'}
            </button>
          ))}
        </div>
      </div>

      {/* Honest Demo Banner */}
      <div className="p-3.5 rounded-xl bg-[#12121A] border border-white/[0.06] flex items-center justify-between text-xs text-[#92929F]">
        <div className="flex items-center gap-2.5">
          <Info className="w-4 h-4 text-[#9B8CFF] shrink-0" />
          <span>
            Demonstration analytics: Displays modeled benchmark metrics illustrating expected cross-session memory dynamics. Not connected to a live production database.
          </span>
        </div>
        <span className="font-mono text-[10px] text-[#626270] uppercase">Demo Model</span>
      </div>

      {/* 4 Primary KPI Highlight Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#12121A] border border-white/[0.07] space-y-1">
          <div className="text-xs text-[#92929F] font-medium">Model Repeat Issue Rate</div>
          <div className="text-2xl font-bold text-[#34D399] font-mono tracking-tight flex items-center gap-2">
            <span>6.2%</span>
            <span className="text-xs font-normal text-[#34D399] flex items-center">
              <ArrowDownRight className="w-3.5 h-3.5" /> -36.2%
            </span>
          </div>
          <p className="text-[11px] text-[#626270]">
            Illustrates expected suppression of repeated restart steps when failed actions are recalled.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#12121A] border border-white/[0.07] space-y-1">
          <div className="text-xs text-[#92929F] font-medium">Simulated First-Contact Resolution</div>
          <div className="text-2xl font-bold text-[#F4F4F7] font-mono tracking-tight flex items-center gap-2">
            <span>91.4%</span>
            <span className="text-xs font-normal text-[#34D399] flex items-center">
              <ArrowUpRight className="w-3.5 h-3.5" /> +6.8%
            </span>
          </div>
          <p className="text-[11px] text-[#626270]">
            Projected resolution benchmark when agent references persistent hardware context.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#12121A] border border-white/[0.07] space-y-1">
          <div className="text-xs text-[#92929F] font-medium">Model Escalation Rate</div>
          <div className="text-2xl font-bold text-[#FBBF24] font-mono tracking-tight flex items-center gap-2">
            <span>4.8%</span>
            <span className="text-xs font-normal text-[#34D399] flex items-center">
              <ArrowDownRight className="w-3.5 h-3.5" /> -2.1%
            </span>
          </div>
          <p className="text-[11px] text-[#626270]">
            Modeled handoff to human support after two consecutive failed diagnostic reports.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#12121A] border border-white/[0.07] space-y-1">
          <div className="text-xs text-[#92929F] font-medium">Target Response Latency Budget</div>
          <div className="text-2xl font-bold text-[#B6A9FF] font-mono tracking-tight flex items-center gap-2">
            <span>1.2s</span>
            <span className="text-xs font-normal text-[#34D399] flex items-center">
              <ArrowDownRight className="w-3.5 h-3.5" /> -0.4s
            </span>
          </div>
          <p className="text-[11px] text-[#626270]">
            Calculated target: Groq Llama 3.3 70B inference combined with Hindsight Cloud retrieval.
          </p>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Repeat Issue Frequency (Modeled Comparison) */}
        <div className="p-5 sm:p-6 rounded-2xl bg-[#12121A] border border-white/[0.08] space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7]">
                Repeat Issue Frequency: Modeled Comparison (%)
              </h3>
              <p className="text-xs text-[#92929F]">
                Illustrative comparison: Stateless LLM support vs RECALL AI Persistent Memory
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10B981]/15 text-[#34D399]">
              Modeled Benefit
            </span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={REPEAT_ISSUE_COMPARISON}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="period" stroke="#626270" fontSize={11} tickLine={false} />
                <YAxis stroke="#626270" fontSize={11} tickLine={false} axisLine={false} unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12121A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#F4F4F7',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="withoutRecall"
                  stroke="#F43F5E"
                  strokeWidth={2}
                  name="Without Recall AI (Stateless baseline)"
                />
                <Line
                  type="monotone"
                  dataKey="withRecall"
                  stroke="#10B981"
                  strokeWidth={2.5}
                  name="With Recall AI (Persistent Memory model)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Memory Retrieval Breakdown by Category */}
        <div className="p-5 sm:p-6 rounded-2xl bg-[#12121A] border border-white/[0.08] space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7]">
                Sample Retrieval Distribution by Category
              </h3>
              <p className="text-xs text-[#92929F]">
                Synthetic breakdown of customer context types conditioning responses
              </p>
            </div>
            <span className="text-[10px] font-mono text-[#9B8CFF]">Demonstration Bank</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MEMORY_RETRIEVAL_BY_CATEGORY} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" stroke="#626270" fontSize={11} tickLine={false} />
                <YAxis dataKey="category" type="category" stroke="#92929F" fontSize={11} tickLine={false} width={110} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12121A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#F4F4F7',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} name="Sample Query Count" fill="#9B8CFF" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Pipeline Latency Breakdown */}
        <div className="lg:col-span-2 p-5 sm:p-6 rounded-2xl bg-[#12121A] border border-white/[0.08] space-y-4 shadow-md">
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-[#F4F4F7]">
              Architectural Latency Budget (Target Specifications)
            </h3>
            <p className="text-xs text-[#92929F]">
              Budget allocation for Hindsight Cloud memory retrieval, identity cryptographic verification, and Groq reasoning
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-2">
            {LATENCY_BREAKDOWN_DATA.map((step, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-[#191923] border border-white/[0.05] space-y-1">
                <span className="text-[10px] font-mono text-[#626270] uppercase">Budget 0{idx + 1}</span>
                <div className="text-xs font-semibold text-[#F4F4F7] truncate">{step.stage}</div>
                <div className="text-lg font-bold text-[#9B8CFF] font-mono">{step.latencyMs}ms</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
