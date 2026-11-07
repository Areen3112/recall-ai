import type React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  LayoutDashboard,
  Inbox,
  Users,
  Brain,
  Activity,
  BarChart3,
  BookOpen,
  Cpu,
  Settings,
  Sparkles,
  FlaskConical
} from 'lucide-react';
import type { NavigationPage } from '../../types';

export interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
  currentPage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({
  isOpen,
  onClose,
  currentPage,
  onNavigate,
}) => {
  const navItems = [
    { id: 'overview' as NavigationPage, label: 'Overview', icon: LayoutDashboard },
    { id: 'inbox' as NavigationPage, label: 'Support Inbox', icon: Inbox },
    { id: 'customers' as NavigationPage, label: 'Customers', icon: Users },
    { id: 'memory-explorer' as NavigationPage, label: 'Memory Explorer', icon: Brain, badge: 'Core' },
    { id: 'activity' as NavigationPage, label: 'Agent Activity', icon: Activity },
    { id: 'analytics' as NavigationPage, label: 'Analytics', icon: BarChart3 },
    { id: 'knowledge-base' as NavigationPage, label: 'Knowledge Base', icon: BookOpen },
    { id: 'integrations' as NavigationPage, label: 'Integrations', icon: Cpu },
    { id: 'settings' as NavigationPage, label: 'Settings', icon: Settings },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#09090D]/80 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="relative w-72 max-w-[80vw] bg-[#0D0D13] border-r border-white/[0.08] h-full flex flex-col p-4 shadow-2xl z-10"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#9B8CFF]/15 border border-[#9B8CFF]/30 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-[#B6A9FF]" />
                </div>
                <div>
                  <span className="font-bold text-sm tracking-wider text-[#F4F4F7]">RECALL AI</span>
                  <div className="text-[10px] text-[#626270]">Customer Intelligence</div>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-md text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.06] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Nav list */}
            <div className="flex-1 overflow-y-auto py-4 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onNavigate(item.id);
                      onClose();
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#9B8CFF]/15 text-[#B6A9FF]'
                        : 'text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[#9B8CFF]' : 'text-[#626270]'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-[#10B981]/15 text-[#34D399]">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-white/[0.08] text-xs text-[#626270]">
              <div className="flex items-center gap-2 text-[#B6A9FF]">
                <FlaskConical className="w-3.5 h-3.5 text-[#9B8CFF]" />
                <span className="font-mono text-[10px]">DEMO ENVIRONMENT</span>
              </div>
              <p className="mt-1 text-[11px] text-[#92929F]">Persistent memory across sessions.</p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
