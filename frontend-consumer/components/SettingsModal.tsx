import React, { useState } from 'react';
import { Globe, Moon, Sun, X } from 'lucide-react';
import { t } from '../i18n';
import { SystemSettings } from '../types';

interface SettingsModalProps {
  settings: SystemSettings;
  onUpdate: (updates: Partial<SystemSettings>) => void;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ settings, onUpdate, onClose }) => {
  const [localSettings, setLocalSettings] = useState<SystemSettings>({ ...settings });

  const handleBackdropMouseDown = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const handleApply = () => {
    onUpdate(localSettings);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm"
      onMouseDown={handleBackdropMouseDown}
    >
      <div
        className="w-full max-w-sm rounded-[2rem] border border-white/60 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.16)] dark:border-white/10 dark:bg-[#111827]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-slate-950 dark:text-white">
              {t(localSettings.language, 'settings')}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">
              {t(localSettings.language, 'settingsSubtitle')}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/5 dark:hover:text-white"
            aria-label="Close settings"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-950 dark:text-white">
              {localSettings.theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              {t(localSettings.language, 'theme')}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {(['light', 'dark'] as const).map((themeOption) => (
                <button
                  key={themeOption}
                  type="button"
                  onClick={() => setLocalSettings((current) => ({ ...current, theme: themeOption }))}
                  className={`rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    localSettings.theme === themeOption
                      ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                      : 'bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-950/40 dark:text-slate-300 dark:hover:bg-slate-950'
                  }`}
                >
                  {t(localSettings.language, themeOption)}
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-950 dark:text-white">
              <Globe size={16} />
              {t(localSettings.language, 'language')}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {([
                { value: 'en', label: t(localSettings.language, 'english') },
                { value: 'ko', label: t(localSettings.language, 'korean') },
              ] as const).map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setLocalSettings((current) => ({ ...current, language: option.value }))}
                  className={`rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    localSettings.language === option.value
                      ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                      : 'bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-950/40 dark:text-slate-300 dark:hover:bg-slate-950'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        </div>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
          >
            {t(localSettings.language, 'cancel')}
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="flex-1 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
          >
            {t(localSettings.language, 'save')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
