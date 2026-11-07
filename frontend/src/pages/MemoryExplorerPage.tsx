import { useState } from 'react';
import type React from 'react';
import {
  Brain,
  AlertTriangle,
  Tag,
  Sliders,
  FileText,
  CheckCircle,
  Eye,
  Clock,
  Ban,
  Layers,
  ArrowRight,
  User,
  FlaskConical,
  Info
} from 'lucide-react';
import { MOCK_MEMORIES } from '../data/mock/memories';
import { MOCK_CUSTOMERS } from '../data/mock/customers';
import { Badge } from '../components/ui/Badge';
import { SearchInput } from '../components/ui/SearchInput';
import { MemoryCard } from '../components/memory/MemoryCard';

export interface MemoryExplorerPageProps {
  initialCustomerId?: string;
  onOpenConversation?: (convId: string) => void;
}

export const MemoryExplorerPage: React.FC<MemoryExplorerPageProps> = ({
  initialCustomerId,
}) => {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>(
    initialCustomerId || 'all'
  );
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMemoryId, setSelectedMemoryId] = useState<string>('mem-sm-failed-01');

  // Categories definition
  const categories: { id: string; label: string; icon: React.ComponentType<{ className?: string }>; count?: number }[] = [
    { id: 'all', label: 'All Memories', icon: Layers },
    { id: 'failed_attempts', label: 'Failed Attempts', icon: Ban },
    { id: 'customer_facts', label: 'Customer Facts', icon: Tag },
    { id: 'preferences', label: 'Preferences', icon: Sliders },
    { id: 'customer_reported_issues', label: 'Reported Issues', icon: FileText },
    { id: 'successful_resolutions', label: 'Resolutions', icon: CheckCircle },
    { id: 'agent_observations', label: 'Agent Observations', icon: Eye },
    { id: 'historical_context', label: 'Historical Context', icon: Clock },
  ];

  // Filtering
  const filteredMemories = MOCK_MEMORIES.filter((m) => {
    const matchesCustomer =
      selectedCustomerId === 'all' || m.customerId === selectedCustomerId;
    const matchesCategory =
      selectedCategory === 'all' || m.category === selectedCategory;
    const matchesSearch =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.relatedIssue.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCustomer && matchesCategory && matchesSearch;
  });

  const selectedMemory =
    MOCK_MEMORIES.find((m) => m.id === selectedMemoryId) || filteredMemories[0] || MOCK_MEMORIES[0];

  const failedCount = MOCK_MEMORIES.filter((m) => m.isFailedAttempt).length;

  return (
    <div className="h-full flex flex-col overflow-hidden bg-[#09090D]">
      {/* Top Intelligence Console Header Bar */}
      <div className="bg-[#12121A] border-b border-white/[0.08] px-4 sm:px-6 py-3.5 shrink-0 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#9B8CFF]/15 border border-[#9B8CFF]/30 flex items-center justify-center glow-accent-sm shrink-0">
            <Brain className="w-5 h-5 text-[#B6A9FF]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#F4F4F7] tracking-tight">
                Customer Memory Intelligence Console
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#9B8CFF]/20 text-[#B6A9FF] border border-[#9B8CFF]/35">
                Retain • Recall • Reflect
              </span>
            </div>
            <p className="text-xs text-[#92929F]">
              Direct inspection of persistent customer memory bank. Demonstrating failed-attempt recognition and cross-session knowledge retention.
            </p>
          </div>
        </div>

        {/* Demo environment note */}
        <div className="flex items-center gap-2.5 bg-[#0D0D13] px-3 py-1.5 rounded-xl border border-white/[0.06] text-xs">
          <FlaskConical className="w-3.5 h-3.5 text-[#9B8CFF]" />
          <span className="text-[#92929F]">Status:</span>
          <span className="text-[#F4F4F7] font-semibold">Demonstration Memory Console</span>
        </div>
      </div>

      {/* Control Filters Bar */}
      <div className="p-3.5 sm:p-4 bg-[#0D0D13] border-b border-white/[0.07] flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Customer selector */}
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-[#626270]" />
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="bg-[#12121A] text-xs text-[#F4F4F7] border border-white/[0.08] rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-[#9B8CFF]/50 cursor-pointer"
            >
              <option value="all">All Customers ({MOCK_CUSTOMERS.length})</option>
              {MOCK_CUSTOMERS.map((cust) => (
                <option key={cust.id} value={cust.id}>
                  {cust.name} ({cust.memoryCount} memories)
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="flex-1 max-w-sm">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search memories, facts, avoid rules..."
            />
          </div>
        </div>

        {/* Failed Attempts Filter Pill */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedCategory('failed_attempts')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              selectedCategory === 'failed_attempts'
                ? 'bg-[#F43F5E]/20 text-[#FF6B8B] border border-[#F43F5E]/50 glow-rose-sm'
                : 'bg-[#19121E] text-[#FB7185] border border-[#F43F5E]/25 hover:border-[#F43F5E]/50'
            }`}
          >
            <Ban className="w-3.5 h-3.5" />
            <span>Failed Attempts ({failedCount})</span>
          </button>
        </div>
      </div>

      {/* Main 3-Column Layout: Categories / Memory Stream / Deep Inspection */}
      <div className="flex-1 flex overflow-hidden">
        {/* Category List Sidebar (Left) */}
        <div className="hidden md:block w-52 lg:w-56 shrink-0 bg-[#0D0D13] border-r border-white/[0.07] p-3 overflow-y-auto">
          <div className="text-[10px] font-semibold text-[#626270] uppercase tracking-wider px-3 py-1.5 mb-1">
            Memory Categories
          </div>
          <div className="space-y-1">
            {categories.map((cat) => {
              const Icon = cat.icon;
              const isActive = selectedCategory === cat.id;
              const isFailed = cat.id === 'failed_attempts';
              const count =
                cat.id === 'all'
                  ? MOCK_MEMORIES.length
                  : MOCK_MEMORIES.filter((m) => m.category === cat.id).length;

              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? isFailed
                        ? 'bg-[#F43F5E]/15 text-[#FF6B8B] border border-[#F43F5E]/30 font-semibold'
                        : 'bg-[#9B8CFF]/15 text-[#B6A9FF] border border-[#9B8CFF]/25 font-semibold'
                      : 'text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Icon
                      className={`w-3.5 h-3.5 shrink-0 ${
                        isActive
                          ? isFailed
                            ? 'text-[#F43F5E]'
                            : 'text-[#9B8CFF]'
                          : 'text-[#626270]'
                      }`}
                    />
                    <span className="truncate">{cat.label}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                      isActive ? 'bg-white/[0.1] text-white' : 'text-[#626270]'
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Sarah Mitchell Demo Focus Box */}
          <div className="mt-6 p-3 rounded-xl bg-[#141018] border border-[#F43F5E]/25 space-y-2">
            <div className="flex items-center gap-1.5 text-[#FB7185] text-xs font-semibold">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>Demo Scenario Focus</span>
            </div>
            <p className="text-[11px] text-[#92929F] leading-snug">
              Inspect Sarah Mitchell's failed troubleshooting memory to verify how RECALL AI avoids repetitive suggestions across sessions.
            </p>
            <button
              onClick={() => {
                setSelectedCustomerId('cust-sarah-mitchell-01');
                setSelectedCategory('failed_attempts');
                setSelectedMemoryId('mem-sm-failed-01');
              }}
              className="w-full text-left py-1 text-[11px] text-[#B6A9FF] font-medium hover:underline flex items-center justify-between cursor-pointer"
            >
              <span>View Sarah's Memory</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Memory Stream Timeline (Center) */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3 bg-[#09090D] border-r border-white/[0.07]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-[#92929F] uppercase tracking-wider">
              Memory Bank Records ({filteredMemories.length})
            </span>
            <span className="text-[11px] text-[#626270] font-mono">
              Chronological order
            </span>
          </div>

          {filteredMemories.length === 0 ? (
            <div className="p-12 text-center text-[#626270] text-xs">
              No memories match the current filters.
            </div>
          ) : (
            filteredMemories.map((mem) => (
              <MemoryCard
                key={mem.id}
                memory={mem}
                isSelected={mem.id === selectedMemory.id}
                onClick={() => setSelectedMemoryId(mem.id)}
                showCustomerName={selectedCustomerId === 'all'}
              />
            ))
          )}
        </div>

        {/* Memory Deep Detail Panel (Right) */}
        <div className="hidden lg:block w-80 xl:w-96 shrink-0 bg-[#0D0D13] p-5 overflow-y-auto space-y-5">
          {selectedMemory ? (
            <div className="space-y-5">
              {/* Top Category and Verification Status */}
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.07]">
                <Badge
                  variant={selectedMemory.isFailedAttempt ? 'failed' : 'violet'}
                  size="md"
                  dot={selectedMemory.isFailedAttempt}
                >
                  {selectedMemory.category.toUpperCase().replace('_', ' ')}
                </Badge>
                <span className="text-xs font-mono text-[#92929F]">
                  ID: {selectedMemory.id}
                </span>
              </div>

              {/* Title & Content */}
              <div>
                <h3 className="text-sm sm:text-base font-bold text-[#F4F4F7] tracking-tight mb-2">
                  {selectedMemory.title}
                </h3>
                <div className="p-3.5 rounded-xl bg-[#12121A] border border-white/[0.08] text-xs sm:text-sm text-[#F4F4F7] leading-relaxed">
                  {selectedMemory.content}
                </div>
              </div>

              {/* FAILED ATTEMPT RULE DETAILS (Highlighted if applicable) */}
              {selectedMemory.isFailedAttempt && (
                <div className="p-4 rounded-xl bg-[#191018] border border-[#F43F5E]/40 space-y-2.5 glow-rose-sm text-left">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#FB7185] uppercase tracking-wider">
                    <Ban className="w-4 h-4 text-[#F43F5E]" />
                    <span>Active Avoidance Rule</span>
                  </div>
                  <div className="text-xs text-[#F4F4F7] font-medium leading-relaxed">
                    {selectedMemory.avoidAction}
                  </div>
                  <div className="text-[11px] text-[#92929F] pt-2 border-t border-[#F43F5E]/20">
                    <strong>Action Key: </strong>
                    <code className="text-[#FF6B8B] font-mono">{selectedMemory.failedActionId}</code>
                  </div>
                  <div className="text-[10px] text-[#FBBF24] bg-[#F59E0B]/10 p-2.5 rounded-lg border border-[#F59E0B]/20 leading-relaxed flex items-start gap-1.5">
                    <Info className="w-3.5 h-3.5 text-[#F59E0B] shrink-0 mt-0.5" />
                    <span>
                      Customer-reported outcome: Logged to avoid customer repetition. Not verified by diagnostic telemetry.
                    </span>
                  </div>
                </div>
              )}

              {/* Provenance & Metadata Grid */}
              <div className="space-y-2.5">
                <h4 className="text-xs font-semibold text-[#626270] uppercase tracking-wider">
                  Memory Provenance & Audit
                </h4>

                <div className="p-3 rounded-xl bg-[#12121A] border border-white/[0.06] space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Customer:</span>
                    <span className="text-[#F4F4F7] font-semibold">{selectedMemory.customerName}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Source:</span>
                    <span className="text-[#9B8CFF] font-medium">{selectedMemory.source}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Verification:</span>
                    <span className={selectedMemory.isFailedAttempt ? 'text-[#FBBF24]' : 'text-[#34D399]'}>
                      {selectedMemory.verification}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Related Issue:</span>
                    <span className="text-[#F4F4F7] truncate max-w-[170px]">{selectedMemory.relatedIssue}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Session ID:</span>
                    <code className="font-mono text-[11px] text-[#B6A9FF]">
                      {selectedMemory.sessionId.slice(0, 16)}...
                    </code>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Confidence Score:</span>
                    <span className="font-mono text-[#34D399]">
                      {(selectedMemory.confidenceScore * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#626270]">Recalled in Prompts:</span>
                    <span className="font-mono text-[#F4F4F7]">{selectedMemory.recalledCount} times</span>
                  </div>
                </div>
              </div>

              {/* Additional Context Footnote */}
              {selectedMemory.context && (
                <div className="p-3 rounded-xl bg-[#12121A] border border-white/[0.06] text-xs space-y-1">
                  <span className="text-[10px] font-semibold uppercase text-[#626270]">Agent Context Notes</span>
                  <p className="text-[#92929F] leading-relaxed">{selectedMemory.context}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-[#626270] text-xs pt-10">
              Select a memory to inspect provenance and avoidance details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
