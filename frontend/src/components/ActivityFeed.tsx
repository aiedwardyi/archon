import { useState } from "react";
import { CheckCircle2, XCircle, Play, GitBranch, Clock, ChevronDown, ChevronUp } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { useActivity } from "@/services/api";

const COLLAPSED_COUNT = 4;

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function statusIcon(status: string) {
  const s = status.toUpperCase();
  if (s === "SUCCESS" || s === "COMPLETED") return { icon: CheckCircle2, iconClass: "text-emerald-500" };
  if (s === "FAILED" || s === "ERROR") return { icon: XCircle, iconClass: "text-destructive" };
  if (s === "RUNNING" || s === "IN_PROGRESS") return { icon: Play, iconClass: "text-blue-500" };
  return { icon: GitBranch, iconClass: "text-muted-foreground" };
}

function statusText(item: { project_name: string; project_id: number; status: string; version: number }): string {
  const s = item.status.toUpperCase();
  if (s === "SUCCESS" || s === "COMPLETED") return `${item.project_name} v${item.version} completed`;
  if (s === "FAILED" || s === "ERROR") return `${item.project_name} v${item.version} build failed`;
  if (s === "RUNNING" || s === "IN_PROGRESS") return `Pipeline started for ${item.project_name}`;
  return `Version v${item.version} created for ${item.project_name}`;
}

export const ActivityFeed = () => {
  const { t } = useLanguage();
  const items = useActivity();
  const [expanded, setExpanded] = useState(false);

  const canExpand = items.length > COLLAPSED_COUNT;
  const visible = expanded ? items : items.slice(0, COLLAPSED_COUNT);

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
        {items.length === 0 && (
          <div className="px-3 py-4 text-xs text-muted-foreground text-center">No recent activity</div>
        )}
        {visible.map((a, i) => {
          const { icon: Icon, iconClass } = statusIcon(a.status);
          return (
            <div key={i} className="px-3 py-2.5 flex items-start gap-2.5 hover:bg-secondary/40 transition-colors">
              <Icon className={`h-3.5 w-3.5 mt-0.5 flex-shrink-0 ${iconClass}`} />
              <div className="min-w-0 flex-1">
                <div className="text-xs text-foreground leading-snug">{statusText(a)}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{a.created_at ? relativeTime(a.created_at) : "—"}</div>
              </div>
            </div>
          );
        })}
      </div>
      {canExpand && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-3 py-2 border-t border-border text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/40 transition-colors flex items-center justify-center gap-1"
        >
          {expanded ? (
            <><ChevronUp className="h-3 w-3" /> Show less</>
          ) : (
            <><ChevronDown className="h-3 w-3" /> Show more ({items.length - COLLAPSED_COUNT})</>
          )}
        </button>
      )}
    </div>
  );
};
