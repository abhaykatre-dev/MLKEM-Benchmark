import React from 'react';
import { MLKEMVariantSpec } from '../../types';
import { Card } from './Card';
import { Badge } from './Badge';
import { ShieldCheck, Key, Lock, Cpu, CheckCircle2 } from 'lucide-react';

interface VariantCardProps {
  spec: MLKEMVariantSpec;
}

export const VariantCard: React.FC<VariantCardProps> = ({ spec }) => {
  const {
    variant,
    claimedNistLevel,
    securityBits,
    publicKeySize,
    secretKeySize,
    ciphertextSize,
    minRamRequirement,
    performanceRating,
    memoryUsageRating,
    recommendedUseCases,
  } = spec;

  const levelColor = claimedNistLevel === 'Level 1' ? 'info' : claimedNistLevel === 'Level 3' ? 'purple' : 'emerald';

  return (
    <Card className="flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-slate-700 pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <Badge variant={levelColor} size="sm" className="mb-1">
                {claimedNistLevel} ({securityBits}-bit Security)
              </Badge>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight font-mono">{variant}</h3>
            </div>
          </div>
        </div>

        {/* Cryptographic Parameters Grid */}
        <div className="grid grid-cols-3 gap-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-md border border-slate-200 dark:border-slate-700 mb-5">
          <div className="text-center">
            <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
              <Key className="w-3 h-3 text-slate-600 dark:text-slate-400" /> Public Key
            </span>
            <span className="text-xs font-bold text-slate-900 dark:text-white font-mono">{publicKeySize} B</span>
          </div>

          <div className="text-center border-x border-slate-200 dark:border-slate-700">
            <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
              <Lock className="w-3 h-3 text-slate-600 dark:text-slate-400" /> Secret Key
            </span>
            <span className="text-xs font-bold text-slate-900 dark:text-white font-mono">{secretKeySize} B</span>
          </div>

          <div className="text-center">
            <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
              <ShieldCheck className="w-3 h-3 text-slate-600 dark:text-slate-400" /> Ciphertext
            </span>
            <span className="text-xs font-bold text-slate-900 dark:text-white font-mono">{ciphertextSize} B</span>
          </div>
        </div>

        {/* Memory & Rating Specs */}
        <div className="space-y-2 mb-5 text-xs">
          <div className="flex justify-between items-center bg-stone-50 dark:bg-slate-800/60 px-3 py-2 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" /> Min SRAM Boundary:
            </span>
            <span className="font-bold text-slate-900 dark:text-white font-mono">&ge; {minRamRequirement} KB SRAM</span>
          </div>

          <div className="flex justify-between items-center bg-stone-50 dark:bg-slate-800/60 px-3 py-2 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-600 dark:text-slate-400 font-medium">Execution Throughput:</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">{performanceRating}</span>
          </div>

          <div className="flex justify-between items-center bg-stone-50 dark:bg-slate-800/60 px-3 py-2 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-600 dark:text-slate-400 font-medium">Stack Footprint:</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">{memoryUsageRating}</span>
          </div>
        </div>

        {/* Recommended Use Cases */}
        <div>
          <span className="text-xs uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400 mb-2.5 block">
            Recommended Deployments
          </span>
          <ul className="space-y-1.5">
            {recommendedUseCases.map((useCase, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{useCase}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
};
