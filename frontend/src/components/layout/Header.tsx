import { useState } from 'react';
import type React from 'react';
import {
  Search,
  Bell,
  Menu,
  CheckCircle2,
  AlertTriangle,
  Brain,
  Sparkles,
  Command,
  FlaskConical
} from 'lucide-react';
import type { NavigationPage } from '../../types';

export interface HeaderProps {
  currentPage: NavigationPage;
  onOpenMobileNav: () => void;
  onOpenCommandPalette: () => void;
  onNavigate: (page: NavigationPage) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onOpenMobileNav,
  onOpenCommandPalette,
  onNavigate,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);

  const pageMeta: Record<NavigationPage, { title: string; subtitle: string; breadcrumb: string }> = {
    overview: {
      title: 'Platform Overview',
      subtitle: 'Demonstration dashboard for customer intelligence and persistent memory',
      breadcrumb: 'Workspace / Overview',
    },
    inbox: {
      title: 'Support Inbox',
      subtitle: 'Simulated memory-conditioned workspace featuring the Sarah Mitchell scenario',
      breadcrumb: 'Workspace / Inbox',
    },
    customers: {
      title: 'Customer Directory',
      subtitle: 'Persistent memory profiles, interaction history and hardware preferences (Demo dataset)',
      breadcrumb: 'Workspace / Customers',
    },
    'memory-explorer': {
      title: 'Memory Explorer',
      subtitle: 'Core intelligence console: explore verified facts, preferences & failed attempts',
      breadcrumb: 'Intelligence / Memory Explorer',
    },
    activity: {
      title: 'Agent Activity Stream',
      subtitle: 'Simulated telemetry of memory recall, reasoning & retention events',
      breadcrumb: 'Intelligence / Agent Activity',
    },
    analytics: {
      title: 'Analytics & Insights',
      subtitle: 'Demonstration metrics illustrating cross-session repeat-issue reduction',
      breadcrumb: 'Intelligence / Analytics',
    },
    'knowledge-base': {
      title: 'Knowledge Base',
      subtitle: 'Technical troubleshooting documentation indexed into persistent memory (Demo)',
      breadcrumb: 'Configuration / Knowledge Base',
    },
    integrations: {
      title: 'Integrations & Architecture',
      subtitle: 'System architecture: Supabase, Hindsight Cloud, Groq & Webhook connectors',
      breadcrumb: 'Configuration / Integrations',
    },
    settings: {
      title: 'Settings',
      subtitle: 'Workspace preferences, identity token rules & memory retention thresholds',
      breadcrumb: 'Configuration / Settings',
    },
  };

  const currentMeta = pageMeta[currentPage];

  const recentNotifications = [
    {
      id: 'notif-1',
      title: 'Failed Troubleshooting Step Stored',
      desc: 'Sarah Mitchell reported Bluetooth forget & pair did not work. Added to avoidance filter.',
      time: '12m ago',
      type: 'warning',
      actionPage: 'memory-explorer' as NavigationPage,
    },
    {
      id: 'notif-2',
      title: 'Tier-2 Escalation Triggered',
      desc: 'Marcus Vance reached repeated failure threshold on Windows 11 multipoint.',
      time: '45m ago',
      type: 'alert',
      actionPage: 'inbox' as NavigationPage,
    },
    {
      id: 'notif-3',
      title: 'Memory Mesh Synced (Simulated)',
      desc: 'Hindsight Cloud successfully indexed demonstration knowledge base articles.',
      time: '2h ago',
      type: 'success',
      actionPage: 'knowledge-base' as NavigationPage,
    },
  ];

  return (
    <header className="h-16 bg-[#09090D] border-b border-white/[0.07] px-4 sm:px-6 flex items-center justify-between z-10 sticky top-0">
      {/* Left: Mobile trigger & Page Title / Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileNav}
          className="lg:hidden p-1.5 rounded-lg text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.06] transition-colors cursor-pointer"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm sm:text-base font-semibold text-[#F4F4F7] tracking-tight">
              {currentMeta.title}
            </h1>
            <span className="hidden md:inline-block text-[11px] font-mono text-[#626270]">
              / {currentMeta.breadcrumb}
            </span>
          </div>
          <p className="hidden sm:block text-xs text-[#92929F] truncate max-w-md">
            {currentMeta.subtitle}
          </p>
        </div>
      </div>

      {/* Right: Quick Search, Status, Notifications, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Quick Search Button */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#12121A] border border-white/[0.08] text-xs text-[#92929F] hover:text-[#F4F4F7] hover:border-white/[0.14] transition-all cursor-pointer group"
        >
          <Search className="w-3.5 h-3.5 text-[#626270] group-hover:text-[#9B8CFF] transition-colors" />
          <span className="hidden sm:inline">Search memory, customers...</span>
          <span className="sm:hidden">Search</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.2 text-[10px] font-mono text-[#626270] bg-white/[0.04] border border-white/[0.08] rounded">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </button>

        {/* Persistent Truthful DEMO ENVIRONMENT Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#9B8CFF]/10 border border-[#9B8CFF]/25 text-[11px] text-[#B6A9FF] font-medium">
          <FlaskConical className="w-3 h-3 text-[#9B8CFF]" />
          <span className="font-mono tracking-tight text-[10px]">DEMO ENVIRONMENT</span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.06] transition-colors cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#9B8CFF]" />
          </button>

          {showNotifications && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setShowNotifications(false)}
              />
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-[#12121A] border border-white/[0.1] shadow-2xl p-3 z-40 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#9B8CFF]" />
                    <span className="text-xs font-semibold text-[#F4F4F7]">Demonstration Alerts</span>
                  </div>
                  <span className="text-[10px] text-[#626270] font-mono">Simulated</span>
                </div>

                <div className="space-y-1.5">
                  {recentNotifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => {
                        onNavigate(n.actionPage);
                        setShowNotifications(false);
                      }}
                      className="p-2 rounded-lg bg-[#191923] hover:bg-[#21212E] border border-white/[0.04] transition-colors cursor-pointer text-left"
                    >
                      <div className="flex items-start gap-2.5">
                        {n.type === 'warning' && (
                          <AlertTriangle className="w-4 h-4 text-[#F43F5E] shrink-0 mt-0.5" />
                        )}
                        {n.type === 'alert' && (
                          <Brain className="w-4 h-4 text-[#F59E0B] shrink-0 mt-0.5" />
                        )}
                        {n.type === 'success' && (
                          <CheckCircle2 className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
                        )}
                        <div>
                          <div className="text-xs font-medium text-[#F4F4F7]">{n.title}</div>
                          <div className="text-[11px] text-[#92929F] leading-snug mt-0.5">{n.desc}</div>
                          <span className="text-[10px] text-[#626270] mt-1 block">{n.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-1 text-center">
                  <button
                    onClick={() => {
                      onNavigate('activity');
                      setShowNotifications(false);
                    }}
                    className="text-[11px] text-[#B6A9FF] hover:underline cursor-pointer"
                  >
                    View simulated event stream →
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-1 border-l border-white/[0.08]">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#9B8CFF] to-[#7B68EE] p-[1px]">
            <div className="w-full h-full rounded-full bg-[#12121A] flex items-center justify-center text-xs font-semibold text-[#F4F4F7]">
              AR
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
