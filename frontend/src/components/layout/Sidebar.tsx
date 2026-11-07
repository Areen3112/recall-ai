import type React from 'react';
import {
  LayoutDashboard,
  Inbox,
  Users,
  Brain,
  Activity,
  BarChart3,
  BookOpen,
  Cpu,
  Settings,
  ChevronDown,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  FlaskConical
} from 'lucide-react';
import type { NavigationPage } from '../../types';

export interface SidebarProps {
  currentPage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  unreadInboxCount?: number;
}

interface NavItem {
  id: NavigationPage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  isCollapsed,
  onToggleCollapse,
  unreadInboxCount = 2,
}) => {
  const navSections: NavSection[] = [
    {
      title: 'WORKSPACE',
      items: [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'inbox', label: 'Support Inbox', icon: Inbox, count: unreadInboxCount },
        { id: 'customers', label: 'Customers', icon: Users },
      ],
    },
    {
      title: 'INTELLIGENCE',
      items: [
        {
          id: 'memory-explorer',
          label: 'Memory Explorer',
          icon: Brain,
          badge: 'Core'
        },
        { id: 'activity', label: 'Agent Activity', icon: Activity },
        { id: 'analytics', label: 'Analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'CONFIGURATION',
      items: [
        { id: 'knowledge-base', label: 'Knowledge Base', icon: BookOpen },
        { id: 'integrations', label: 'Integrations', icon: Cpu },
        { id: 'settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside
      className={`relative flex flex-col bg-[#0D0D13] border-r border-white/[0.07] transition-all duration-300 ease-in-out shrink-0 select-none z-20 ${
        isCollapsed ? 'w-18' : 'w-64'
      } h-screen`}
    >
      {/* Top Header / Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-white/[0.07]">
        {!isCollapsed ? (
          <div className="flex items-center gap-3">
            {/* Logo Mark */}
            <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-[#9B8CFF]/20 to-[#9B8CFF]/5 border border-[#9B8CFF]/40 flex items-center justify-center glow-accent-sm">
              <Sparkles className="w-4 h-4 text-[#B6A9FF]" />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#9B8CFF]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-wider text-[#F4F4F7]">RECALL</span>
                <span className="text-[10px] px-1 py-0.2 rounded font-mono font-semibold bg-[#9B8CFF]/20 text-[#B6A9FF] border border-[#9B8CFF]/30">
                  AI
                </span>
              </div>
              <p className="text-[10px] text-[#626270] tracking-tight">Persistent Memory Engine</p>
            </div>
          </div>
        ) : (
          <div className="mx-auto">
            <div className="relative w-9 h-9 rounded-lg bg-[#9B8CFF]/15 border border-[#9B8CFF]/35 flex items-center justify-center glow-accent-sm">
              <Sparkles className="w-5 h-5 text-[#B6A9FF]" />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#9B8CFF]" />
            </div>
          </div>
        )}

        {/* Collapse toggle button */}
        <button
          onClick={onToggleCollapse}
          className={`p-1 rounded-md text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.06] transition-colors cursor-pointer ${
            isCollapsed ? 'hidden' : 'block'
          }`}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Workspace Selector */}
      {!isCollapsed ? (
        <div className="px-3 pt-3 pb-1">
          <div className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-[#12121A] border border-white/[0.06] text-xs text-[#92929F] hover:border-white/[0.12] transition-colors cursor-pointer group">
            <div className="flex items-center gap-2 truncate">
              <span className="w-2 h-2 rounded-full bg-[#9B8CFF]" />
              <div className="truncate">
                <div className="text-[#F4F4F7] font-medium text-xs truncate">Recall AI Demo</div>
                <div className="text-[10px] text-[#626270]">workspace-v2-dev</div>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#626270] group-hover:text-[#F4F4F7] transition-colors shrink-0" />
          </div>
        </div>
      ) : (
        <div className="py-2 flex justify-center">
          <button
            onClick={onToggleCollapse}
            className="w-8 h-8 rounded-lg bg-[#12121A] border border-white/[0.06] flex items-center justify-center text-[#92929F] hover:text-[#F4F4F7] transition-colors cursor-pointer"
            title="Expand"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-6">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            {!isCollapsed && (
              <h4 className="px-3 text-[10px] font-semibold tracking-wider text-[#626270] uppercase">
                {section.title}
              </h4>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    title={isCollapsed ? item.label : undefined}
                    className={`w-full flex items-center rounded-lg text-xs font-medium transition-all group relative cursor-pointer ${
                      isCollapsed ? 'justify-center p-2.5' : 'px-3 py-2 justify-between'
                    } ${
                      isActive
                        ? 'bg-[#9B8CFF]/15 text-[#F4F4F7]'
                        : 'text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.04]'
                    }`}
                  >
                    {/* Active violet indicator bar */}
                    {isActive && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-[#9B8CFF] rounded-r shadow-[0_0_8px_rgba(155,140,255,0.7)]" />
                    )}

                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive
                            ? 'text-[#9B8CFF]'
                            : 'text-[#626270] group-hover:text-[#92929F]'
                        }`}
                      />
                      {!isCollapsed && (
                        <span className={isActive ? 'font-semibold text-[#F4F4F7]' : ''}>
                          {item.label}
                        </span>
                      )}
                    </div>

                    {!isCollapsed && (
                      <div className="flex items-center gap-1.5">
                        {item.count !== undefined && item.count > 0 && (
                          <span className="px-1.5 py-0.2 text-[10px] font-mono rounded-full bg-[#9B8CFF]/20 text-[#B6A9FF] border border-[#9B8CFF]/30">
                            {item.count}
                          </span>
                        )}
                        {item.badge && (
                          <span className="px-1.5 py-0.2 text-[10px] font-medium rounded-full bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/30">
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* System Status and User Profile Footer */}
      <div className="p-3 border-t border-white/[0.07] space-y-2">
        {/* Truthful Demo Environment Status */}
        {!isCollapsed && (
          <div className="px-2.5 py-1.5 rounded-lg bg-[#12121A] border border-white/[0.05] flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-3.5 h-3.5 text-[#9B8CFF]" />
              <span className="text-[#92929F] font-mono text-[10px]">DEMO ENVIRONMENT</span>
            </div>
            <span className="text-[10px] text-[#626270] font-mono">Simulated</span>
          </div>
        )}

        {/* User Profile */}
        <div className={`flex items-center rounded-lg p-1.5 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div className="flex items-center gap-2.5 truncate">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#9B8CFF] to-[#7B68EE] p-[1px] shrink-0">
              <div className="w-full h-full rounded-full bg-[#0D0D13] flex items-center justify-center text-[11px] font-bold text-[#F4F4F7]">
                AR
              </div>
            </div>
            {!isCollapsed && (
              <div className="truncate text-left">
                <div className="text-xs font-medium text-[#F4F4F7] truncate">Alex Rivera</div>
                <div className="text-[10px] text-[#626270] truncate">Lead Support Architect</div>
              </div>
            )}
          </div>
          {!isCollapsed && (
            <span title="Workspace Admin">
              <ShieldCheck className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};
