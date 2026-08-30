import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`
        bg-white rounded-lg border border-stone-200/90 shadow-xs p-5
        transition-all duration-200 text-slate-800
        ${hoverEffect ? 'hover:border-slate-400 hover:shadow-sm' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
