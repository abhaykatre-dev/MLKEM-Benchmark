import React, { useState } from 'react';
import { RecommendationFormInputs, RecommendationResult, SecurityLevel, OptimizationLevel } from '../types';
import { runAIRecommendation } from '../services/aiEngine';
import { apiService } from '../services/api';
import { Card } from '../components/ui/Card';
import { RecommendationCard } from '../components/ui/RecommendationCard';
import { Button } from '../components/ui/Button';
import { PROCESSOR_PROFILES } from '../data/mockData';
import { BrainCircuit, Cpu, Sliders, Shield, Sparkles, AlertCircle } from 'lucide-react';

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
  const [result, setResult] = useState<RecommendationResult>(() => runAIRecommendation(formInputs));

  // Handle MCU preset change
  const handleMcuChange = (mcuName: string) => {
    const selectedMcu = PROCESSOR_PROFILES.find((p) => p.mcu === mcuName);
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

    try {
      const output = await apiService.getRecommendation(formInputs);
      setResult(output);
    } catch (err) {
      const output = runAIRecommendation(formInputs);
      setResult(output);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100">
            <BrainCircuit className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
              AI-Based ML-KEM Recommendation Interface
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Interactive target parameter input form and recommendation confidence display (UI Preview)
            </p>
          </div>
        </div>
      </Card>

      {/* Interface Disclaimer Banner */}
      <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-md p-3.5 flex items-start gap-2.5 text-xs text-amber-800 dark:text-amber-300">
        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Frontend UI Demonstration:</span> This view renders the client-side decision matrix interface. Machine learning model training and server-side prediction endpoints are maintained by the backend engineering sub-team.
        </div>
      </div>

      {/* Main Grid: Form Inputs (Left) and AI Output Card (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Interactive Parameter Form */}
        <div className="lg:col-span-6">
          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-slate-700 dark:text-slate-300" /> Target Hardware Specifications
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Target MCU Select */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-slate-600 dark:text-slate-400" /> Target Processor Preset
                </label>
                <select
                  value={formInputs.mcu}
                  onChange={(e) => handleMcuChange(e.target.value)}
                  className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-2 text-xs text-slate-900 dark:text-white font-medium outline-none focus:border-slate-800 dark:focus:border-slate-500"
                >
                  {PROCESSOR_PROFILES.map((p) => (
                    <option key={p.mcu} value={p.mcu} className="dark:bg-slate-900 dark:text-white">
                      {p.mcu} ({p.core} @ {p.frequency} MHz, {p.ram} KB RAM)
                    </option>
                  ))}
                  <option value="Custom" className="dark:bg-slate-900 dark:text-white">Custom Target Profile</option>
                </select>
              </div>

              {/* Frequency, RAM, Flash Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Clock (MHz)</label>
                  <input
                    type="number"
                    value={formInputs.frequency}
                    onChange={(e) => setFormInputs({ ...formInputs, frequency: Number(e.target.value) })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-900 dark:text-white font-bold font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">SRAM (KB)</label>
                  <input
                    type="number"
                    value={formInputs.ram}
                    onChange={(e) => setFormInputs({ ...formInputs, ram: Number(e.target.value) })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-900 dark:text-white font-bold font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Flash (KB)</label>
                  <input
                    type="number"
                    value={formInputs.flash}
                    onChange={(e) => setFormInputs({ ...formInputs, flash: Number(e.target.value) })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-900 dark:text-white font-bold font-mono"
                  />
                </div>
              </div>

              {/* Security Level Radio Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-slate-600 dark:text-slate-400" /> Target Security Level
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
                            ? 'bg-slate-900 dark:bg-blue-600 text-white border-slate-900 dark:border-blue-600 shadow-xs'
                            : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
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
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Compiler Optimization (-O)</label>
                  <select
                    value={formInputs.optimization}
                    onChange={(e) => setFormInputs({ ...formInputs, optimization: e.target.value as OptimizationLevel })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-900 dark:text-white font-medium outline-none"
                  >
                    <option value="O0" className="dark:bg-slate-900 dark:text-white">-O0 (No Optimization)</option>
                    <option value="O1" className="dark:bg-slate-900 dark:text-white">-O1 (Minimal Size)</option>
                    <option value="O2" className="dark:bg-slate-900 dark:text-white">-O2 (Balanced Speed)</option>
                    <option value="O3" className="dark:bg-slate-900 dark:text-white">-O3 (Max Speed)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    System CPU Load: <span className="font-bold text-slate-900 dark:text-white font-mono">{formInputs.cpuLoad}%</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="75"
                    value={formInputs.cpuLoad}
                    onChange={(e) => setFormInputs({ ...formInputs, cpuLoad: Number(e.target.value) })}
                    className="w-full accent-slate-900 dark:accent-blue-500 mt-2"
                  />
                </div>
              </div>

              {/* Latency Budget Input */}
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Latency Budget Constraint (Microseconds µs)
                </label>
                <input
                  type="number"
                  step="500"
                  value={formInputs.latencyBudget}
                  onChange={(e) => setFormInputs({ ...formInputs, latencyBudget: Number(e.target.value) })}
                  className="w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-900 dark:text-white font-bold font-mono"
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
                Generate Recommendation Preview
              </Button>
            </form>
          </Card>
        </div>

        {/* AI Output Card (Right) */}
        <div className="lg:col-span-6">
          <RecommendationCard result={result} />
        </div>
      </div>
    </div>
  );
};
