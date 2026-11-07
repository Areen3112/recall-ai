import type React from 'react';
import { Search, X } from 'lucide-react';

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  shortcut?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = 'Search...',
  className = '',
  shortcut,
}) => {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3 w-4 h-4 text-[#626270] pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-[#12121A] text-[#F4F4F7] text-sm placeholder-[#626270] border border-white/[0.08] rounded-lg pl-9 pr-12 py-1.5 focus:outline-none focus:border-[#9B8CFF]/50 focus:ring-1 focus:ring-[#9B8CFF]/30 transition-all"
      />
      {value ? (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 text-[#626270] hover:text-[#92929F] p-0.5 rounded cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      ) : (
        shortcut && (
          <kbd className="absolute right-2.5 px-1.5 py-0.5 text-[10px] font-mono text-[#626270] bg-white/[0.05] border border-white/[0.08] rounded">
            {shortcut}
          </kbd>
        )
      )}
    </div>
  );
};
