import { useState } from 'react';
import type React from 'react';
import { MOCK_CUSTOMERS } from '../data/mock/customers';
import { MOCK_MEMORIES } from '../data/mock/memories';
import { MOCK_CONVERSATIONS } from '../data/mock/conversations';
import { CustomerDetailView } from '../components/customer/CustomerDetailView';
import { SearchInput } from '../components/ui/SearchInput';
import { Badge } from '../components/ui/Badge';
import { Users, AlertTriangle, ArrowLeft, Laptop } from 'lucide-react';

export interface CustomersPageProps {
  initialCustomerId?: string;
  onOpenConversation?: (convId: string) => void;
  onNavigateToMemoryExplorer?: (customerId: string) => void;
}

export const CustomersPage: React.FC<CustomersPageProps> = ({
  initialCustomerId = 'cust-sarah-mitchell-01',
  onOpenConversation,
  onNavigateToMemoryExplorer,
}) => {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>(initialCustomerId);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'vip' | 'active' | 'churn_risk'>('all');
  const [mobileShowDetail, setMobileShowDetail] = useState(false);

  const selectedCustomer =
    MOCK_CUSTOMERS.find((c) => c.id === selectedCustomerId) || MOCK_CUSTOMERS[0];

  const customerMemories = MOCK_MEMORIES.filter(
    (m) => m.customerId === selectedCustomer.id
  );

  const customerConversations = MOCK_CONVERSATIONS.filter(
    (c) => c.customerId === selectedCustomer.id
  );

  const filteredCustomers = MOCK_CUSTOMERS.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.deviceInfo?.model || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="h-full flex flex-col md:flex-row overflow-hidden bg-[#09090D]">
      {/* Customer Directory List Column */}
      <div
        className={`w-full md:w-80 lg:w-96 shrink-0 h-full flex flex-col bg-[#0D0D13] border-r border-white/[0.07] ${
          mobileShowDetail ? 'hidden md:flex' : 'flex'
        }`}
      >
        {/* Header Controls */}
        <div className="p-4 border-b border-white/[0.07] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-[#9B8CFF]" />
              <h2 className="text-sm font-semibold text-[#F4F4F7]">Customer Intelligence</h2>
            </div>
            <span className="text-[11px] font-mono text-[#626270] bg-white/[0.05] px-2 py-0.5 rounded">
              {filteredCustomers.length} total
            </span>
          </div>

          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search customers, hardware..."
          />

          {/* Filter tabs */}
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#12121A] border border-white/[0.05] text-xs">
            {(['all', 'vip', 'active', 'churn_risk'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className={`flex-1 py-1 text-center font-medium capitalize rounded-md transition-colors cursor-pointer text-xs ${
                  statusFilter === filter
                    ? 'bg-[#191923] text-[#F4F4F7] shadow-sm'
                    : 'text-[#92929F] hover:text-[#F4F4F7]'
                }`}
              >
                {filter === 'churn_risk' ? 'At Risk' : filter}
              </button>
            ))}
          </div>
        </div>

        {/* Customer Cards List */}
        <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
          {filteredCustomers.map((cust) => {
            const isSelected = cust.id === selectedCustomer.id;
            const hasFailedAttempt = cust.failedAttemptsCount > 0;

            return (
              <div
                key={cust.id}
                onClick={() => {
                  setSelectedCustomerId(cust.id);
                  setMobileShowDetail(true);
                }}
                className={`p-4 text-left cursor-pointer transition-all relative ${
                  isSelected
                    ? 'bg-[#161622] border-l-2 border-l-[#9B8CFF]'
                    : 'hover:bg-white/[0.02]'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2.5">
                    <img
                      src={cust.avatar}
                      alt={cust.name}
                      className="w-9 h-9 rounded-full object-cover border border-white/[0.1] shrink-0"
                    />
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-[#F4F4F7] truncate">
                        {cust.name}
                      </div>
                      <div className="text-[11px] text-[#92929F] truncate max-w-[140px]">
                        {cust.email}
                      </div>
                    </div>
                  </div>
                  <Badge
                    variant={
                      cust.status === 'vip'
                        ? 'emerald'
                        : cust.status === 'churn_risk'
                        ? 'rose'
                        : 'neutral'
                    }
                    size="sm"
                  >
                    {cust.status === 'churn_risk' ? 'Risk' : cust.status}
                  </Badge>
                </div>

                {cust.deviceInfo && (
                  <div className="text-[11px] text-[#626270] flex items-center gap-1.5 truncate my-1">
                    <Laptop className="w-3 h-3 text-[#9B8CFF] shrink-0" />
                    <span className="truncate">{cust.deviceInfo.model}</span>
                  </div>
                )}

                <div className="mt-2 flex items-center justify-between text-[10px] text-[#626270]">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[#9B8CFF]">{cust.memoryCount} memories</span>
                    <span>•</span>
                    <span>{cust.conversationCount} convs</span>
                  </div>

                  {hasFailedAttempt && (
                    <span className="text-[#FB7185] bg-[#F43F5E]/10 border border-[#F43F5E]/20 px-1.5 py-0.2 rounded font-medium flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {cust.failedAttemptsCount} failed step
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Customer Detail View Area */}
      <div
        className={`flex-1 h-full min-w-0 overflow-y-auto ${
          mobileShowDetail ? 'block' : 'hidden md:block'
        }`}
      >
        {/* Mobile back button */}
        <div className="md:hidden p-3 bg-[#0D0D13] border-b border-white/[0.07] flex items-center gap-2">
          <button
            onClick={() => setMobileShowDetail(false)}
            className="text-xs text-[#92929F] hover:text-[#F4F4F7] flex items-center gap-1 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Customers list</span>
          </button>
        </div>

        <CustomerDetailView
          customer={selectedCustomer}
          memories={customerMemories}
          conversations={customerConversations}
          onOpenConversation={onOpenConversation}
          onNavigateToMemoryExplorer={onNavigateToMemoryExplorer}
        />
      </div>
    </div>
  );
};
