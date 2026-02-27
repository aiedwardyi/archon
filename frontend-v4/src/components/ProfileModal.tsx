import { X, User, Mail, Calendar, CreditCard } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface ProfileModalProps {
  open: boolean;
  onClose: () => void;
}

export const ProfileModal = ({ open, onClose }: ProfileModalProps) => {
  const { t } = useLanguage();
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-md shadow-lg w-full max-w-md z-10 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider">{t("profile")}</h2>
          <button onClick={onClose} className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-5 py-4 border-b border-border flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold flex-shrink-0">
            JD
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">Jane Doe</div>
            <div className="text-[11px] text-muted-foreground">archon@archon.dev</div>
          </div>
        </div>

        <div className="divide-y divide-border">
          {[
            { icon: User, label: t("fullName"), value: "Jane Doe" },
            { icon: Mail, label: t("email"), value: "archon@archon.dev" },
            { icon: CreditCard, label: t("plan"), value: t("free") },
            { icon: Calendar, label: t("memberSince"), value: "January 2025" },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
              <span className="text-xs font-medium text-foreground">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
