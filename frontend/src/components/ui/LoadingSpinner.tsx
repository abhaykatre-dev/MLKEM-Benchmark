import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Fetching benchmark data from backend...',
  size = 'md',
}) => {
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-600">
      <Loader2 className={`${iconSizes[size]} animate-spin text-slate-800`} />
      {label && <p className="text-xs font-medium text-slate-600 animate-pulse">{label}</p>}
    </div>
  );
};
