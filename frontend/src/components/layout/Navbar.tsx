import React from 'react';
import { PageId } from './Sidebar';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Menu, BrainCircuit, Database, ShieldCheck, Sun, Moon } from 'lucide-react';

interface NavbarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  onOpenMobileSidebar: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activePage,
  onNavigate,
  onOpenMobileSidebar,
  isDarkMode,
  onToggleDarkMode,
}) => {
  const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Benchmark Overview Dashboard',
      subtitle: 'Post-Quantum ML-KEM Cryptographic Characterization on Microcontrollers',
    },
    recommendation: {
      title: 'AI Recommendation (UI Preview)',
      subtitle: 'Interactive hardware specification & latency parameter interface',
    },
    benchmarks: {
      title: 'Benchmark Explorer',
      subtitle: 'Empirical execution latency, cycle count, and RAM footprint records',
    },
    analytics: {
      title: 'Performance & Resource Analytics',
      subtitle: 'Cryptographic operation breakdown across processors and variants',
    },
    processors: {
      title: 'Microcontroller Target Profiles',
      subtitle: 'Hardware specifications for ARM Cortex-M, RISC-V, and Xtensa targets',
    },
    variants: {
      title: 'NIST FIPS 203 ML-KEM Specifications',
      subtitle: 'Security levels, key sizes, ciphertext overhead, and RAM bounds',
    },
    about: {
      title: 'Academic Research Documentation',
      subtitle: 'B.Tech final year project objectives, architecture, and references',
    },
    settings: {
      title: 'Framework Configuration',
      subtitle: 'Local dataset paths and visualization display preferences',
    },
  };

  const { title, subtitle } = pageTitles[activePage] || {
    title: 'Post-Quantum Benchmarking Framework',
    subtitle: 'NIST FIPS 203 Cryptography Research Suite',
  };

  return (
    <header className="sticky top-0 z-30 bg-white dark:bg-slate-900 border-b border-stone-200 dark:border-slate-800 px-4 lg:px-8 py-3 flex items-center justify-between gap-4 shadow-xs transition-colors duration-200">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-1.5 rounded-md bg-stone-100 dark:bg-slate-800 border border-stone-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h2 className="text-base lg:text-lg font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            {title}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block font-medium">{subtitle}</p>
        </div>
      </div>

      {/* Action Controls & Badges */}
      <div className="flex items-center gap-2.5">
        <Badge variant="info" size="sm" className="hidden md:inline-flex">
          <ShieldCheck className="w-3.5 h-3.5" /> NIST FIPS 203
        </Badge>

        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={onToggleDarkMode}
          title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          aria-label="Toggle Theme"
          className="p-2 rounded-lg bg-stone-100 dark:bg-slate-800 border border-stone-200 dark:border-slate-700 text-slate-700 dark:text-amber-400 hover:bg-stone-200 dark:hover:bg-slate-700 transition-all duration-200 flex items-center gap-1.5 text-xs font-semibold"
        >
          {isDarkMode ? (
            <>
              <Sun className="w-4 h-4 text-amber-400 animate-pulse" />
              <span className="hidden sm:inline text-amber-400">Light</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-slate-700" />
              <span className="hidden sm:inline text-slate-700">Dark</span>
            </>
          )}
        </button>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => onNavigate('benchmarks')}
          icon={<Database className="w-4 h-4 text-slate-600 dark:text-slate-300" />}
          className="hidden sm:inline-flex"
        >
          Explore Data
        </Button>

        <Button
          variant="primary"
          size="sm"
          onClick={() => onNavigate('recommendation')}
          icon={<BrainCircuit className="w-4 h-4 text-amber-400" />}
        >
          <span className="hidden sm:inline font-medium">AI</span> Recommendation UI
        </Button>
      </div>
    </header>
  );
};
