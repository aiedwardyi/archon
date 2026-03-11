import React, { useState } from 'react';
import { Globe, X } from 'lucide-react';
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
        className="w-full max-w-sm rounded-[2rem] border border-white/10 bg-[#09101f] p-6 shadow-[0_30px_80px_rgba(2,6,23,0.55)]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-white">
              {t(localSettings.language, 'settings')}
            </h2>
            <p className="mt-1 text-sm text-white/50">
              {t(localSettings.language, 'settingsSubtitle')}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-white/40 transition hover:bg-white/[0.06] hover:text-white"
            aria-label="Close settings"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
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
                      ? 'bg-[linear-gradient(135deg,#4f46e5,#7c3aed)] text-white'
                      : 'border border-white/10 bg-white/[0.05] text-white/60 hover:bg-white/[0.08] hover:text-white'
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
            className="flex-1 rounded-2xl border border-white/10 px-4 py-3 text-sm font-medium text-white/60 transition hover:bg-white/[0.05]"
          >
            {t(localSettings.language, 'cancel')}
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="flex-1 rounded-2xl bg-[linear-gradient(135deg,#4f46e5,#7c3aed)] px-4 py-3 text-sm font-medium text-white transition hover:brightness-110"
          >
            {t(localSettings.language, 'save')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
