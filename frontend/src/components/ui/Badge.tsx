import type React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'violet' | 'emerald' | 'amber' | 'rose' | 'neutral' | 'outline' | 'failed';
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  className = '',
}) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  const variantClasses = {
    violet: 'bg-[#9B8CFF]/12 text-[#B6A9FF] border border-[#9B8CFF]/25',
    emerald: 'bg-[#10B981]/12 text-[#34D399] border border-[#10B981]/25',
    amber: 'bg-[#F59E0B]/12 text-[#FBBF24] border border-[#F59E0B]/25',
    rose: 'bg-[#F43F5E]/12 text-[#FB7185] border border-[#F43F5E]/25',
    neutral: 'bg-white/[0.06] text-[#92929F] border border-white/[0.08]',
    outline: 'bg-transparent text-[#92929F] border border-white/[0.12]',
    failed: 'bg-[#F43F5E]/15 text-[#FF6B8B] border border-[#F43F5E]/40 font-medium glow-rose-sm',
  }[variant];

  const dotColorClasses = {
    violet: 'bg-[#9B8CFF]',
    emerald: 'bg-[#10B981]',
    amber: 'bg-[#F59E0B]',
    rose: 'bg-[#F43F5E]',
    neutral: 'bg-[#92929F]',
    outline: 'bg-[#92929F]',
    failed: 'bg-[#F43F5E] animate-pulse',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium tracking-tight ${sizeClasses} ${variantClasses} ${className}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotColorClasses}`} />}
      {children}
    </span>
  );
};
