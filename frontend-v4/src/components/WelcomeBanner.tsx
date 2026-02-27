import { Cpu, Code2, GitBranch, Clock } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface WelcomeBannerProps {
  stats?: { total: number; running: number; completed: number; failed: number };
}

export const WelcomeBanner = ({ stats }: WelcomeBannerProps) => {
  const { t } = useLanguage();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? t("goodMorning") : hour < 18 ? t("goodAfternoon") : t("goodEvening");

  const metrics = [
    { icon: Cpu, label: t("pipelinesToday"), value: stats ? String(stats.total) : "—", change: null, up: true },
    { icon: Code2, label: t("linesGenerated"), value: "48.2k", change: "+6.1k", up: true },
    { icon: GitBranch, label: t("versionsShipped"), value: "37", change: "+5", up: true },
    { icon: Clock, label: t("avgBuildTime"), value: "2m 14s", change: "-12s", up: true },
  ];

  return (
    <div className="border border-border rounded-md bg-card overflow-hidden">
      <div className="px-5 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground tracking-tight">
            {greeting}, Jane
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("platformOverview")} · <span className="font-medium text-foreground">{t("enterpriseWorkspace")}</span>
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">{t("allSystemsOperational")}</span>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-px bg-border border-t border-border">
        {metrics.map(({ icon: Icon, label, value, change, up }) => (
          <div key={label} className="bg-card px-4 py-3 flex items-center gap-3">
            <div className="h-9 w-9 rounded-md bg-secondary flex items-center justify-center flex-shrink-0">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</div>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="text-lg font-bold text-foreground leading-none">{value}</span>
                {change && (
                  <span className={`text-[10px] font-semibold ${up ? "text-emerald-600 dark:text-emerald-400" : "text-destructive"}`}>
                    {change}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
