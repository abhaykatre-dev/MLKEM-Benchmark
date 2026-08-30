import React, { useState, useEffect } from 'react';
import { RecommendationFormInputs, RecommendationResult, SecurityLevel, OptimizationLevel, ProcessorProfile } from '../types';
import { apiService } from '../services/api';
import { Card } from '../components/ui/Card';
import { RecommendationCard } from '../components/ui/RecommendationCard';
import { Button } from '../components/ui/Button';
import { ApiErrorState } from '../components/ui/ApiErrorState';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { PROCESSOR_PROFILES } from '../data/mockData';
import { BrainCircuit, Cpu, Sliders, Shield, Sparkles } from 'lucide-react';

export const AIRecommendationPage: React.FC = () => {
  const [formInputs, setFormInputs] = useState<RecommendationFormInputs>({
    mcu: 'STM32F407VGT6',
    frequency: 168,
    ram: 192,
    flash: 1024,
    securityLevel: 'Level 3',
    optimization: 'O3',
    cpuLoad: 25,
    latencyBudget: 8000,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [processors, setProcessors] = useState<ProcessorProfile[]>(PROCESSOR_PROFILES);

  // Load target profiles and initial recommendation on mount
  const loadInitialRecommendation = async () => {
    setInitialLoading(true);
    setApiError(null);
    try {
      const [output, procList] = await Promise.all([
        apiService.getRecommendation(formInputs),
        apiService.getProcessors().catch(() => PROCESSOR_PROFILES),
      ]);
      setResult(output);
      if (procList && procList.length > 0) {
        setProcessors(procList);
      }
    } catch (err: any) {
      setApiError(err?.message || 'Failed to reach backend API recommendation endpoint.');
    } finally {
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    loadInitialRecommendation();
  }, []);

  // Handle MCU preset change
  const handleMcuChange = (mcuName: string) => {
    const selectedMcu = processors.find((p) => p.mcu === mcuName);
    if (selectedMcu) {
      setFormInputs((prev) => ({
        ...prev,
        mcu: selectedMcu.mcu,
        frequency: selectedMcu.frequency,
        ram: selectedMcu.ram,
        flash: selectedMcu.flash,
      }));
    } else {
      setFormInputs((prev) => ({ ...prev, mcu: mcuName }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setApiError(null);

    try {
      const output = await apiService.getRecommendation(formInputs);
      setResult(output);
    } catch (err: any) {
      setApiError(err?.message || 'Backend API server unavailable for recommendation calculation.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-slate-100 border border-slate-200 text-slate-800">
            <BrainCircuit className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              AI-Based ML-KEM Recommendation Interface
            </h1>
            <p className="text-xs text-slate-500">
              Interactive target parameter input form evaluated against backend AI recommendation model
            </p>
          </div>
        </div>
      </Card>

      {/* Main Grid: Form Inputs (Left) and AI Output Card (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Interactive Parameter Form */}
        <div className="lg:col-span-6">
          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2 border-b border-slate-200 pb-3">
              <Sliders className="w-4 h-4 text-slate-700" /> Target Hardware Specifications
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Target MCU Select */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-slate-600" /> Target Processor Profile
                </label>
                <select
                  value={formInputs.mcu}
                  onChange={(e) => handleMcuChange(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-md px-3 py-2 text-xs text-slate-900 font-medium outline-none focus:border-slate-800"
                >
                  {processors.map((p) => (
                    <option key={p.mcu} value={p.mcu}>
                      {p.mcu} ({p.core} @ {p.frequency} MHz, {p.ram} KB RAM)
                    </option>
                  ))}
                  <option value="Custom">Custom Target Profile</option>
                </select>
              </div>

              {/* Frequency, RAM, Flash Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Clock (MHz)</label>
                  <input
                    type="number"
                    value={formInputs.frequency}
                    onChange={(e) => setFormInputs({ ...formInputs, frequency: Number(e.target.value) })}
                    className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-bold font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">SRAM (KB)</label>
                  <input
                    type="number"
                    value={formInputs.ram}
                    onChange={(e) => setFormInputs({ ...formInputs, ram: Number(e.target.value) })}
                    className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-bold font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Flash (KB)</label>
                  <input
                    type="number"
                    value={formInputs.flash}
                    onChange={(e) => setFormInputs({ ...formInputs, flash: Number(e.target.value) })}
                    className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-bold font-mono"
                  />
                </div>
              </div>

              {/* Security Level Radio Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-slate-600" /> Target Security Level
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['Level 1', 'Level 3', 'Level 5'] as SecurityLevel[]).map((lvl) => {
                    const isSelected = formInputs.securityLevel === lvl;
                    return (
                      <button
                        type="button"
                        key={lvl}
                        onClick={() => setFormInputs({ ...formInputs, securityLevel: lvl })}
                        className={`py-2 px-3 rounded-md text-xs font-bold border transition-all cursor-pointer text-center ${
                          isSelected
                            ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
                            : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        {lvl}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* GCC Optimization & CPU Load Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Compiler Optimization (-O)</label>
                  <select
                    value={formInputs.optimization}
                    onChange={(e) => setFormInputs({ ...formInputs, optimization: e.target.value as OptimizationLevel })}
                    className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-medium outline-none"
                  >
                    <option value="-O0">-O0 (No Optimization)</option>
                    <option value="-O1">-O1 (Minimal Size)</option>
                    <option value="-O2">-O2 (Balanced Speed)</option>
                    <option value="-O3">-O3 (Max Speed)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    System CPU Load: <span className="font-bold text-slate-900 font-mono">{formInputs.cpuLoad}%</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="75"
                    value={formInputs.cpuLoad}
                    onChange={(e) => setFormInputs({ ...formInputs, cpuLoad: Number(e.target.value) })}
                    className="w-full accent-slate-900 mt-2"
                  />
                </div>
              </div>

              {/* Latency Budget Input */}
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Latency Budget Constraint (Microseconds µs)
                </label>
                <input
                  type="number"
                  step="500"
                  value={formInputs.latencyBudget}
                  onChange={(e) => setFormInputs({ ...formInputs, latencyBudget: Number(e.target.value) })}
                  className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-bold font-mono"
                />
              </div>

              {/* Submit Action Button */}
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                icon={<Sparkles className="w-4 h-4 text-amber-400" />}
                className="w-full mt-2"
              >
                Run AI Recommendation Inference
              </Button>
            </form>
          </Card>
        </div>

        {/* AI Output Card (Right) */}
        <div className="lg:col-span-6">
          {initialLoading || isLoading ? (
            <Card className="p-8">
              <LoadingSpinner label="Running recommendation inference on backend model..." />
            </Card>
          ) : apiError ? (
            <ApiErrorState
              title="Recommendation API Error"
              message={apiError}
              onRetry={loadInitialRecommendation}
            />
          ) : result ? (
            <RecommendationCard result={result} />
          ) : null}
        </div>
      </div>
    </div>
  );
};
