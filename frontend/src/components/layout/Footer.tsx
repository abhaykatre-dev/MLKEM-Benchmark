import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-12 py-5 px-4 lg:px-8 border-t border-stone-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-500 dark:text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-3 transition-colors duration-200">
      <div>
        <span className="font-semibold text-slate-700 dark:text-slate-200">
          Post-Quantum ML-KEM Benchmarking Framework
        </span>
        <span className="mx-2 text-slate-300 dark:text-slate-700">|</span>
        <span className="text-slate-500 dark:text-slate-400">Final Year B.Tech Computer Science Project</span>
      </div>

      <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 text-[11px]">
        <span>NIST FIPS 203 Standard</span>
        <span>•</span>
        <span>Renode Simulator</span>
        <span>•</span>
        <span>IoT Embedded Targets</span>
      </div>
    </footer>
  );
};
