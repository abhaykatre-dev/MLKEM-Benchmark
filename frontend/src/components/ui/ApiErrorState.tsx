import React from 'react';
import { AlertTriangle, RefreshCw, Server } from 'lucide-react';
import { Button } from './Button';

interface ApiErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ApiErrorState: React.FC<ApiErrorStateProps> = ({
  title = 'Backend Service Unavailable',
  message = 'Unable to connect to the backend REST API server (http://127.0.0.1:8000).',
  onRetry,
}) => {
  return (
    <div className="p-6 bg-white border border-stone-200 rounded-lg text-center space-y-4 max-w-2xl mx-auto shadow-xs my-6">
      <div className="w-12 h-12 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto text-rose-600">
        <Server className="w-6 h-6" />
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          {title}
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed max-w-lg mx-auto">
          {message}
        </p>
      </div>

      <div className="p-3 bg-stone-50 border border-stone-200 rounded text-[11px] text-slate-600 text-left font-mono space-y-1">
        <span className="font-bold text-slate-700 block text-[10px] uppercase tracking-wider">Troubleshooting steps:</span>
        <p>• Ensure the FastAPI server is running: <code className="bg-stone-200 px-1 py-0.5 rounded text-slate-900 font-bold">python backend/main.py</code> or <code className="bg-stone-200 px-1 py-0.5 rounded text-slate-900 font-bold">uvicorn backend.main:app --reload</code></p>
        <p>• Confirm the API base URL in <span className="font-semibold text-slate-800">Framework Settings</span> points to <code className="bg-stone-200 px-1 py-0.5 rounded text-slate-900">http://127.0.0.1:8000</code></p>
      </div>

      {onRetry && (
        <div className="pt-2">
          <Button
            onClick={onRetry}
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="w-4 h-4 text-slate-700" />}
          >
            Retry Connection
          </Button>
        </div>
      )}
    </div>
  );
};
