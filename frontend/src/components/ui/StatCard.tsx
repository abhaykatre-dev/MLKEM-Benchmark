import React from 'react';
import { Card } from './Card';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  glowColor?: 'blue' | 'cyan' | 'emerald' | 'purple';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
}) => {
  return (
    <Card className="flex flex-col justify-between">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 dark:text-slate-400 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight font-mono">{value}</h3>
        </div>
        <div className="p-2.5 rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200">
          {icon}
        </div>
      </div>
      {(subtitle || trend) && (
        <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
          {subtitle && <span className="text-slate-500 dark:text-slate-400 font-medium">{subtitle}</span>}
          {trend && (
            <span
              className={`font-semibold px-2 py-0.5 rounded border ${
                trend.isPositive
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                  : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800'
              }`}
            >
              {trend.isPositive ? '↑' : '↓'} {trend.value}
            </span>
          )}
        </div>
      )}
    </Card>
  );
};
