import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple' | 'cyan' | 'emerald';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}) => {
  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 border-slate-200 font-medium',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200 font-medium',
    warning: 'bg-amber-50 text-amber-800 border-amber-200 font-medium',
    error: 'bg-rose-50 text-rose-800 border-rose-200 font-medium',
    info: 'bg-blue-50 text-blue-800 border-blue-200 font-medium',
    purple: 'bg-indigo-50 text-indigo-800 border-indigo-200 font-medium',
    cyan: 'bg-sky-50 text-sky-800 border-sky-200 font-medium',
    emerald: 'bg-emerald-50 text-emerald-800 border-emerald-200 font-medium',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
