import React, { useState } from 'react';
import { RefreshCw, ServerOff, X } from 'lucide-react';
import { getLang, t } from '../i18n';
import { backend } from '../services/orchestrator';

interface BackendConnectionOverlayProps {
  onClose: () => void;
}

const BackendConnectionOverlay: React.FC<BackendConnectionOverlayProps> = ({ onClose }) => {
  const [isRetrying, setIsRetrying] = useState(false);
  const lang = getLang();

  const handleRetry = async () => {
    setIsRetrying(true);
    await backend.retryConnection();
    setTimeout(() => setIsRetrying(false), 500);
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-[2rem] border border-white/60 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.2)] dark:border-white/10 dark:bg-[#111827]">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/5 dark:hover:text-white"
          aria-label="Close connection warning"
        >
          <X size={16} />
        </button>

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300">
          <ServerOff size={26} />
        </div>

        <h2 className="mt-5 text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {t(lang, 'backendRequired')}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-300/70">
          {t(lang, 'backendHelp')}
        </p>
        <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 dark:bg-white/5 dark:text-slate-100">
          http://localhost:5000
        </p>

        <button
          type="button"
          onClick={handleRetry}
          disabled={isRetrying}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
        >
          <RefreshCw size={16} className={isRetrying ? 'animate-spin' : ''} />
          {isRetrying ? t(lang, 'retry') : t(lang, 'retryConnection')}
        </button>
      </div>
    </div>
  );
};

export default BackendConnectionOverlay;
