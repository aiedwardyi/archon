import { useState } from "react";
import { X, Eye, EyeOff, Key, ShieldCheck } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

const apiKeys = [
  { label: "OpenAI API Key", placeholder: "sk-proj-············", provider: "OpenAI" },
  { label: "Gemini API Key", placeholder: "AIza·········", provider: "Google" },
  { label: "Anthropic API Key", placeholder: "sk-ant-···········", provider: "Anthropic" },
];

export const SettingsModal = ({ open, onClose }: SettingsModalProps) => {
  const [visibility, setVisibility] = useState<Record<number, boolean>>({});
  const { t } = useLanguage();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-md shadow-lg w-full max-w-md z-10 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider">{t("settings")}</h2>
          <button onClick={onClose} className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-5 py-3 border-b border-border bg-secondary/30 flex items-center gap-2">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
          <span className="text-[11px] text-muted-foreground">{t("apiKeysSecurityNotice")}</span>
        </div>

        <div className="divide-y divide-border">
          {apiKeys.map((key, i) => (
            <div key={key.label} className="px-5 py-3.5">
              <div className="flex items-center gap-2 mb-2">
                <Key className="h-3 w-3 text-muted-foreground" />
                <label className="text-xs font-medium text-foreground">{key.label}</label>
                <span className="text-[10px] text-muted-foreground bg-secondary px-1.5 py-0.5 rounded ml-auto">{key.provider}</span>
              </div>
              <div className="relative">
                <input
                  type={visibility[i] ? "text" : "password"}
                  placeholder={key.placeholder}
                  className="w-full h-8 px-3 pr-8 text-xs border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring font-mono"
                />
                <button
                  onClick={() => setVisibility(v => ({ ...v, [i]: !v[i] }))}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {visibility[i] ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="px-5 py-3.5 border-t border-border bg-secondary/20">
          <button className="w-full h-8 bg-primary text-primary-foreground text-xs font-semibold rounded-md hover:opacity-90 transition-opacity">
            {t("saveApiKeys")}
          </button>
        </div>
      </div>
    </div>
  );
};
