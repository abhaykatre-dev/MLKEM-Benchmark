import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { getApiBaseUrl, setApiBaseUrl, apiService } from '../services/api';
import { Settings, Server, Database, Save, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [fastApiUrl, setFastApiUrl] = useState(getApiBaseUrl());
  const [renodePath, setRenodePath] = useState('C:\\Program Files\\Renode\\renode.exe');
  const [datasetSource, setDatasetSource] = useState('benchmark.csv');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [pingStatus, setPingStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [pingMsg, setPingMsg] = useState('');

  // Load live settings from backend if available
  useEffect(() => {
    apiService
      .getSettings()
      .then((s) => {
        if (s.renodePath) setRenodePath(s.renodePath);
        if (s.datasetSource) setDatasetSource(s.datasetSource);
      })
      .catch(() => {
        // Backend offline or unreachable
      });
  }, []);

  const handleTestConnection = async () => {
    setPingStatus('testing');
    setPingMsg('');
    setApiBaseUrl(fastApiUrl);
    try {
      const health = await apiService.getHealth();
      setPingStatus('success');
      setPingMsg(`Backend API connected successfully (version ${health.version || '1.0.0'}).`);
    } catch (err: any) {
      setPingStatus('error');
      setPingMsg(err?.message || 'Unable to connect to specified backend API base URL.');
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiBaseUrl(fastApiUrl);
    try {
      await apiService.updateSettings({
        renodePath,
        datasetSource,
      });
    } catch {
      // Ignored if backend offline
    }
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Top Banner */}
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-slate-100 border border-slate-200 text-slate-800">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Framework & Data Settings</h1>
            <p className="text-xs text-slate-500">
              Configure backend REST API endpoint, simulator execution paths, and dataset source
            </p>
          </div>
        </div>
      </Card>

      {/* Settings Form */}
      <Card className="p-5">
        <form onSubmit={handleSave} className="space-y-5">
          {/* Data Source Display */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-slate-600" /> Benchmark Data Provider Source
            </label>
            <div className="p-3.5 rounded-md border border-slate-200 bg-stone-50 text-left">
              <div className="font-bold text-xs text-slate-900 mb-1">FastAPI Backend Server ({fastApiUrl})</div>
              <div className="text-[11px] text-slate-600 leading-snug">
                Backend serves empirical Renode simulation records from dataset/benchmark.csv and runs AI model inference.
              </div>
            </div>
          </div>

          {/* FastAPI Endpoint input */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Server className="w-4 h-4 text-slate-600" /> Backend REST API Base URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={fastApiUrl}
                onChange={(e) => setFastApiUrl(e.target.value)}
                className="flex-1 bg-white border border-slate-300 rounded-md px-3 py-2 text-xs text-slate-900 font-mono outline-none focus:border-slate-800"
              />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleTestConnection}
                isLoading={pingStatus === 'testing'}
                icon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Test Connection
              </Button>
            </div>

            {pingStatus === 'success' && (
              <p className="text-xs text-emerald-700 font-medium mt-1.5 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> {pingMsg}
              </p>
            )}
            {pingStatus === 'error' && (
              <p className="text-xs text-rose-700 font-medium mt-1.5 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" /> {pingMsg}
              </p>
            )}
          </div>

          {/* Renode Executable Path */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Renode CLI Executable Path
            </label>
            <input
              type="text"
              value={renodePath}
              onChange={(e) => setRenodePath(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-md px-3 py-2 text-xs text-slate-900 font-mono outline-none focus:border-slate-800"
            />
          </div>

          {/* Save Button */}
          <div className="flex items-center gap-3 pt-3 border-t border-slate-200">
            <Button type="submit" variant="primary" size="sm" icon={<Save className="w-4 h-4" />}>
              Save Settings
            </Button>

            {savedSuccess && (
              <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Settings updated!
              </span>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
};
