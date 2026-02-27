import { useState, useEffect } from "react";
import { Cpu, Code2, GitBranch, Clock } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { usePlatformStats } from "@/services/api";

interface WelcomeBannerProps {
  stats?: { total: number; running: number; completed: number; failed: number };
}

function formatLines(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function formatDuration(secs: number): string {
  if (!secs) return "—";
  const m = Math.floor(secs / 60);
  const s = Math.round(secs % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export const WelcomeBanner = ({ stats }: WelcomeBannerProps) => {
  const { t } = useLanguage();
  const platform = usePlatformStats();
  const [backendUp, setBackendUp] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      try {
        const res = await fetch("http://localhost:5000/api/health", { signal: controller.signal });
        setBackendUp(res.ok);
      } catch {
        setBackendUp(false);
      } finally {
        clearTimeout(timeout);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? t("goodMorning") : hour < 18 ? t("goodAfternoon") : t("goodEvening");

  const metrics = [
    { icon: Cpu, label: t("pipelinesToday"), value: platform ? String(platform.pipelines_today) : (stats ? String(stats.total) : "—") },
    { icon: Code2, label: t("linesGenerated"), value: platform ? formatLines(platform.lines_generated) : "—" },
    { icon: GitBranch, label: t("versionsShipped"), value: platform ? String(platform.versions_shipped) : "—" },
    { icon: Clock, label: t("avgBuildTime"), value: platform ? formatDuration(platform.avg_build_time_seconds) : "—" },
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
          <span className={`inline-block h-2 w-2 rounded-full ${backendUp ? "bg-emerald-500 animate-pulse" : "bg-red-500 animate-pulse"}`} />
          <span className={`text-[11px] font-medium ${backendUp ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
            {backendUp ? t("allSystemsOperational") : t("backendOffline")}
          </span>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-px bg-border border-t border-border">
        {metrics.map(({ icon: Icon, label, value }) => (
          <div key={label} className="bg-card px-4 py-3 flex items-center gap-3">
            <div className="h-9 w-9 rounded-md bg-secondary flex items-center justify-center flex-shrink-0">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</div>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="text-lg font-bold text-foreground leading-none">{value}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
