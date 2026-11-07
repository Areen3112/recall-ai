import type React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  icon,
  iconPosition = 'left',
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses = {
    sm: 'px-2.5 py-1 text-xs font-medium rounded-md gap-1.5',
    md: 'px-3.5 py-1.5 text-sm font-medium rounded-lg gap-2',
    lg: 'px-4 py-2 text-base font-medium rounded-lg gap-2.5',
  }[size];

  const variantClasses = {
    primary:
      'bg-[#9B8CFF] text-[#09090D] hover:bg-[#B6A9FF] active:bg-[#8574FF] font-semibold transition-all shadow-sm hover:shadow-[0_0_16px_rgba(155,140,255,0.35)]',
    secondary:
      'bg-[#191923] text-[#F4F4F7] border border-white/[0.08] hover:bg-[#21212E] hover:border-white/[0.14] active:bg-[#12121A] transition-all',
    ghost:
      'bg-transparent text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.05] active:bg-white/[0.08] transition-all',
    danger:
      'bg-[#F43F5E]/15 text-[#FB7185] border border-[#F43F5E]/30 hover:bg-[#F43F5E]/25 transition-all',
    outline:
      'bg-transparent text-[#F4F4F7] border border-white/[0.12] hover:bg-white/[0.06] hover:border-white/[0.2] transition-all',
  }[variant];

  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center cursor-pointer select-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {isLoading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        <>
          {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
          {children}
          {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
        </>
      )}
    </button>
  );
};
