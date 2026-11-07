import type React from 'react';

export interface TabItem<T extends string = string> {
  id: T;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface TabsProps<T extends string = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (tabId: T) => void;
  className?: string;
  size?: 'sm' | 'md';
}

export function Tabs<T extends string = string>({
  tabs,
  activeTab,
  onChange,
  className = '',
  size = 'md',
}: TabsProps<T>) {
  const paddingClass = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-1.5 text-xs sm:text-sm';

  return (
    <div className={`flex items-center gap-1 border-b border-white/[0.07] overflow-x-auto no-scrollbar ${className}`}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`relative flex items-center gap-2 font-medium transition-colors shrink-0 cursor-pointer ${paddingClass} ${
              isActive
                ? 'text-[#F4F4F7]'
                : 'text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.03] rounded-t-lg'
            }`}
          >
            {tab.icon && <span className="w-3.5 h-3.5">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`text-[11px] px-1.5 py-0.2 rounded-full font-mono ${
                  isActive
                    ? 'bg-[#9B8CFF]/20 text-[#B6A9FF]'
                    : 'bg-white/[0.06] text-[#92929F]'
                }`}
              >
                {tab.count}
              </span>
            )}
            {isActive && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#9B8CFF] shadow-[0_0_8px_rgba(155,140,255,0.6)] rounded-full" />
            )}
          </button>
        );
      })}
    </div>
  );
}
