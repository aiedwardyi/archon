import { X, Check, Zap } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface PricingModalProps {
  open: boolean;
  onClose: () => void;
}

export const PricingModal = ({ open, onClose }: PricingModalProps) => {
  const { t } = useLanguage();

  if (!open) return null;

  const plans = [
    {
      name: t("free"),
      price: "$0",
      period: t("forever"),
      features: ["5 projects", "10 pipeline runs / month", "Basic artifact export", "Community support"],
      cta: t("currentPlan"),
      current: true,
    },
    {
      name: t("pro"),
      price: "$29",
      period: t("perMonth"),
      features: ["Unlimited projects", "Unlimited pipeline runs", "PDF export & shareable links", "White-label client views", "Priority support"],
      cta: t("upgradeToPro"),
      current: false,
    },
  ];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-md shadow-lg w-full max-w-lg z-10 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider">{t("pricing")}</h2>
          <button onClick={onClose} className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-5 py-2.5 border-b border-border bg-secondary/20">
          <p className="text-[11px] text-muted-foreground">{t("chooseThePlan")}</p>
        </div>

        <div className="p-5 grid grid-cols-2 gap-4">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`border rounded-md overflow-hidden flex flex-col ${
                plan.current ? "border-border" : "border-primary"
              }`}
            >
              <div className={`px-4 py-3 border-b ${plan.current ? "border-border bg-secondary/30" : "border-primary/30 bg-primary/5"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">{plan.name}</span>
                  {!plan.current && <Zap className="h-3.5 w-3.5 text-primary" />}
                </div>
                <div className="mt-1">
                  <span className="text-xl font-bold text-foreground">{plan.price}</span>
                  <span className="text-[11px] text-muted-foreground ml-1">{plan.period}</span>
                </div>
              </div>

              <div className="px-4 py-3 space-y-2 flex-1">
                {plan.features.map((f) => (
                  <div key={f} className="flex items-start gap-2 text-xs text-foreground">
                    <Check className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    {f}
                  </div>
                ))}
              </div>

              <div className="px-4 py-3 border-t border-border">
                <button
                  className={`w-full h-8 text-xs font-semibold rounded-md transition-opacity ${
                    plan.current
                      ? "border border-border text-muted-foreground cursor-default"
                      : "bg-primary text-primary-foreground hover:opacity-90"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
