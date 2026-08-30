import React, { useState, useEffect } from 'react';
import { PageId } from './Sidebar';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Menu, BrainCircuit, Database, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { apiService } from '../../services/api';

interface NavbarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  onOpenMobileSidebar: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activePage,
  onNavigate,
  onOpenMobileSidebar,
}) => {
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  const checkHealth = async () => {
    setApiStatus('checking');
    try {
      await apiService.getHealth();
      setApiStatus('online');
    } catch {
      setApiStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Benchmark Overview Dashboard',
      subtitle: 'Post-Quantum ML-KEM Cryptographic Characterization on Microcontrollers',
    },
    recommendation: {
      title: 'AI Recommendation Interface',
      subtitle: 'Target hardware parameters & real-time prediction engine interface',
    },
    benchmarks: {
      title: 'Benchmark Data Explorer',
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
      subtitle: 'Backend REST API endpoint configuration & simulator settings',
    },
  };

  const { title, subtitle } = pageTitles[activePage] || {
    title: 'Post-Quantum Benchmarking Framework',
    subtitle: 'NIST FIPS 203 Cryptography Research Suite',
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-stone-200/90 px-4 lg:px-8 py-3 flex items-center justify-between gap-4 shadow-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-1.5 rounded-md bg-stone-100 border border-stone-200 text-slate-700 hover:text-slate-900 cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h2 className="text-base lg:text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            {title}
          </h2>
          <p className="text-xs text-slate-500 hidden sm:block font-medium">{subtitle}</p>
        </div>
      </div>

      {/* Action Controls & Badges */}
      <div className="flex items-center gap-2.5">
        {/* Backend API Health Status Indicator */}
        <button
          onClick={checkHealth}
          title="Click to re-check API connection"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border font-mono transition-colors cursor-pointer"
        >
          {apiStatus === 'checking' && (
            <span className="flex items-center gap-1 text-slate-600 bg-stone-50 border-stone-200">
              <RefreshCw className="w-3 h-3 animate-spin text-slate-500" />
              <span className="hidden md:inline">Connecting API...</span>
            </span>
          )}
          {apiStatus === 'online' && (
            <span className="flex items-center gap-1 text-emerald-800 bg-emerald-50 border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
              <span>API Online</span>
            </span>
          )}
          {apiStatus === 'offline' && (
            <span className="flex items-center gap-1 text-rose-800 bg-rose-50 border-rose-200">
              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>API Offline</span>
            </span>
          )}
        </button>

        <Badge variant="info" size="sm" className="hidden md:inline-flex">
          <ShieldCheck className="w-3.5 h-3.5" /> NIST FIPS 203
        </Badge>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => onNavigate('benchmarks')}
          icon={<Database className="w-4 h-4 text-slate-600" />}
          className="hidden sm:inline-flex"
        >
          Explorer
        </Button>

        <Button
          variant="primary"
          size="sm"
          onClick={() => onNavigate('recommendation')}
          icon={<BrainCircuit className="w-4 h-4 text-amber-400" />}
        >
          <span className="hidden sm:inline font-medium">AI</span> Recommendation
        </Button>
      </div>
    </header>
  );
};
