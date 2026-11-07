import { useState, useEffect } from 'react';
import type React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  LayoutDashboard,
  Inbox,
  Users,
  Brain,
  Activity,
  BarChart3,
  BookOpen,
  Cpu,
  Settings,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import type { NavigationPage } from '../../types';
import { MOCK_CUSTOMERS } from '../../data/mock/customers';
import { MOCK_MEMORIES } from '../../data/mock/memories';

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (page: NavigationPage) => void;
  onSelectCustomer?: (customerId: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onSelectCustomer,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else setQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const navItems = [
    { id: 'overview' as NavigationPage, label: 'Overview', icon: LayoutDashboard },
    { id: 'inbox' as NavigationPage, label: 'Support Inbox', icon: Inbox },
    { id: 'customers' as NavigationPage, label: 'Customers Intelligence', icon: Users },
    { id: 'memory-explorer' as NavigationPage, label: 'Memory Explorer', icon: Brain },
    { id: 'activity' as NavigationPage, label: 'Agent Activity Stream', icon: Activity },
    { id: 'analytics' as NavigationPage, label: 'Analytics & Insights', icon: BarChart3 },
    { id: 'knowledge-base' as NavigationPage, label: 'Knowledge Base', icon: BookOpen },
    { id: 'integrations' as NavigationPage, label: 'Integrations & Architecture', icon: Cpu },
    { id: 'settings' as NavigationPage, label: 'Workspace Settings', icon: Settings },
  ];

  const filteredNav = navItems.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  const filteredCustomers = MOCK_CUSTOMERS.filter((c) =>
    c.name.toLowerCase().includes(query.toLowerCase()) ||
    c.email.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 3);

  const filteredMemories = MOCK_MEMORIES.filter((m) =>
    m.title.toLowerCase().includes(query.toLowerCase()) ||
    m.content.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 3);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-[#09090D]/80 backdrop-blur-md"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: -10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-xl bg-[#12121A] border border-white/[0.12] rounded-2xl shadow-[0_24px_64px_rgba(0,0,0,0.8)] overflow-hidden z-10"
        >
          {/* Search Header */}
          <div className="flex items-center px-4 py-3.5 border-b border-white/[0.08]">
            <Search className="w-5 h-5 text-[#9B8CFF] shrink-0 mr-3" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command, customer, memory or issue..."
              className="w-full bg-transparent text-[#F4F4F7] text-base placeholder-[#626270] focus:outline-none"
            />
            <kbd className="px-2 py-0.5 text-[10px] font-mono text-[#92929F] bg-white/[0.06] border border-white/[0.1] rounded">
              ESC
            </kbd>
          </div>

          {/* Results list */}
          <div className="max-h-96 overflow-y-auto p-2 space-y-4">
            {/* Quick Actions / Navigation */}
            {filteredNav.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-[#626270] uppercase tracking-wider px-3 py-1">
                  Pages
                </p>
                <div className="space-y-0.5">
                  {filteredNav.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          onNavigate(item.id);
                          onClose();
                        }}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-[#F4F4F7] hover:bg-[#9B8CFF]/15 hover:text-[#B6A9FF] group transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="w-4 h-4 text-[#92929F] group-hover:text-[#9B8CFF]" />
                          <span>{item.label}</span>
                        </div>
                        <ArrowRight className="w-3.5 h-3.5 text-[#626270] opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Customers */}
            {filteredCustomers.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-[#626270] uppercase tracking-wider px-3 py-1">
                  Customers
                </p>
                <div className="space-y-0.5">
                  {filteredCustomers.map((cust) => (
                    <button
                      key={cust.id}
                      onClick={() => {
                        onNavigate('customers');
                        if (onSelectCustomer) onSelectCustomer(cust.id);
                        onClose();
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-[#F4F4F7] hover:bg-white/[0.06] group transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <img src={cust.avatar} alt={cust.name} className="w-6 h-6 rounded-full object-cover" />
                        <div className="text-left">
                          <div className="text-xs font-medium text-[#F4F4F7]">{cust.name}</div>
                          <div className="text-[11px] text-[#92929F]">{cust.email}</div>
                        </div>
                      </div>
                      <span className="text-[11px] text-[#92929F]">{cust.conversationCount} convs</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Memories */}
            {filteredMemories.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-[#626270] uppercase tracking-wider px-3 py-1">
                  Memories & Failed Actions
                </p>
                <div className="space-y-0.5">
                  {filteredMemories.map((mem) => (
                    <button
                      key={mem.id}
                      onClick={() => {
                        onNavigate('memory-explorer');
                        onClose();
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-[#F4F4F7] hover:bg-white/[0.06] group transition-colors cursor-pointer text-left"
                    >
                      <div className="flex items-center gap-3 truncate">
                        {mem.isFailedAttempt ? (
                          <AlertTriangle className="w-4 h-4 text-[#F43F5E] shrink-0" />
                        ) : (
                          <Brain className="w-4 h-4 text-[#9B8CFF] shrink-0" />
                        )}
                        <div className="truncate">
                          <div className="text-xs font-medium text-[#F4F4F7] truncate">{mem.title}</div>
                          <div className="text-[11px] text-[#92929F] truncate">{mem.content}</div>
                        </div>
                      </div>
                      <span className="text-[10px] text-[#626270] shrink-0 ml-2">{mem.customerName}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer note */}
          <div className="flex items-center justify-between px-4 py-2 bg-[#0D0D13] border-t border-white/[0.06] text-[11px] text-[#626270]">
            <span>Navigate with arrows or click to select</span>
            <span>RECALL AI Enterprise Intelligence</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
