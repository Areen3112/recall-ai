import type React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'subtle' | 'interactive' | 'failed-border';
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantClasses = {
    default: 'bg-[#12121A] border border-white/[0.07] rounded-xl shadow-sm',
    elevated: 'bg-[#191923] border border-white/[0.09] rounded-xl shadow-md',
    subtle: 'bg-[#0D0D13]/60 border border-white/[0.05] rounded-xl',
    interactive:
      'bg-[#12121A] border border-white/[0.07] hover:border-[#9B8CFF]/40 hover:bg-[#151522] rounded-xl cursor-pointer transition-all duration-200 hover:shadow-[0_4px_20px_rgba(0,0,0,0.4)]',
    'failed-border':
      'bg-[#15121B] border border-[#F43F5E]/30 hover:border-[#F43F5E]/60 rounded-xl transition-all duration-200 glow-rose-sm',
  }[variant];

  return (
    <div className={`${variantClasses} ${className}`} {...props}>
      {children}
    </div>
  );
};
