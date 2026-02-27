import { CheckCircle2, XCircle, Play, GitBranch, Clock } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

const activities = [
  { icon: CheckCircle2, iconClass: "text-emerald-500", text: "Project #55 completed successfully", time: "2m ago" },
  { icon: Play, iconClass: "text-blue-500", text: "Pipeline started for Project #58", time: "5m ago" },
  { icon: GitBranch, iconClass: "text-muted-foreground", text: "Version v2 created for Project #58", time: "8m ago" },
  { icon: XCircle, iconClass: "text-destructive", text: "Project #54 build failed — timeout", time: "12m ago" },
  { icon: CheckCircle2, iconClass: "text-emerald-500", text: "Project #56 deployed to production", time: "1h ago" },
  { icon: Play, iconClass: "text-blue-500", text: "Pipeline started for Project #52", time: "2h ago" },
];

export const ActivityFeed = () => {
  const { t } = useLanguage();

  return (
    <div className="border border-border rounded-md bg-card">
      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
        <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          {t("recentActivity")}
        </h3>
        <span className="text-[10px] text-muted-foreground">{t("live")}</span>
      </div>
      <div className="divide-y divide-border">
        {activities.map((a, i) => {
          const Icon = a.icon;
          return (
            <div key={i} className="px-3 py-2.5 flex items-start gap-2.5 hover:bg-secondary/40 transition-colors">
              <Icon className={`h-3.5 w-3.5 mt-0.5 flex-shrink-0 ${a.iconClass}`} />
              <div className="min-w-0 flex-1">
                <div className="text-xs text-foreground leading-snug">{a.text}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{a.time}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
