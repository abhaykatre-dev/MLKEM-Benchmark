import React from 'react';
import {
  LayoutDashboard,
  BrainCircuit,
  Database,
  BarChart3,
  Cpu,
  Layers,
  Info,
  Settings,
  Shield,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'recommendation'
  | 'benchmarks'
  | 'analytics'
  | 'processors'
  | 'variants'
  | 'about'
  | 'settings';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  isOpen,
  onCloseMobile,
}) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'benchmarks' as PageId, label: 'Benchmark Explorer', icon: <Database className="w-4 h-4" /> },
    { id: 'analytics' as PageId, label: 'Analytics & Graphs', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'recommendation' as PageId, label: 'AI Recommendation (UI)', icon: <BrainCircuit className="w-4 h-4 text-amber-400" /> },
    { id: 'processors' as PageId, label: 'Processors', icon: <Cpu className="w-4 h-4" /> },
    { id: 'variants' as PageId, label: 'ML-KEM Variants', icon: <Layers className="w-4 h-4" /> },
    { id: 'about' as PageId, label: 'About Project', icon: <Info className="w-4 h-4" /> },
    { id: 'settings' as PageId, label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/60 backdrop-blur-xs z-40 lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`
          fixed lg:static top-0 left-0 bottom-0 z-50
          w-64 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-r border-slate-200/80 dark:border-slate-800
          flex flex-col justify-between transition-colors duration-200 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Brand Header */}
        <div>
          <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center gap-3">
            <div className="p-2 rounded bg-blue-50 dark:bg-slate-800 border border-blue-200/80 dark:border-slate-700 text-blue-600 dark:text-white">
              <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight font-mono">
                ML-KEM BENCHMARK
              </h1>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Post-Quantum IoT Lab</p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="p-3 space-y-1">
            <div className="px-3 py-1.5 text-[10px] uppercase font-bold text-slate-400 dark:text-slate-400 tracking-wider">
              Research Console
            </div>
            {navItems.map((item) => {
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onNavigate(item.id);
                    onCloseMobile();
                  }}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium
                    transition-all duration-150 cursor-pointer
                    ${
                      isActive
                        ? 'bg-blue-50/80 text-blue-700 font-semibold border-l-2 border-blue-600 shadow-2xs dark:bg-slate-800 dark:text-white dark:border-blue-500'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/80 dark:hover:bg-slate-800/60'
                    }
                  `}
                >
                  <span className={isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-400'}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer Academic Tag */}
        <div className="p-3 m-3 rounded bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 text-xs">
          <div className="flex items-center gap-2 mb-1 text-slate-700 dark:text-slate-300 font-medium text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400" />
            Renode Simulation Pipeline
          </div>
          <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-snug">
            NIST FIPS 203 Cryptographic Benchmarking Suite
          </p>
        </div>
      </aside>
    </>
  );
};
