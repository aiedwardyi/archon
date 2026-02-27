import { AlertCircle, CheckCircle2, Circle, Loader2, Zap } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

type AgentStatus = "done" | "running" | "pending" | "failed";

interface AgentStep {
  name: string;
  description: string;
  status: AgentStatus;
}

interface PipelineStatusProps {
  agents: AgentStep[];
}

export const PipelineStatus = ({ agents }: PipelineStatusProps) => {
  const { t } = useLanguage();

  const statusConfig: Record<AgentStatus, { icon: typeof CheckCircle2; className: string; label: string; bgClass: string }> = {
    done: { icon: CheckCircle2, className: "text-success", label: t("done"), bgClass: "bg-green-500/10 border-green-500/25" },
    running: { icon: Loader2, className: "text-blue-500 animate-spin", label: t("building"), bgClass: "bg-blue-500/10 border-blue-500/30" },
    failed: { icon: AlertCircle, className: "text-destructive", label: t("failed"), bgClass: "bg-red-500/10 border-red-500/25" },
    pending: { icon: Circle, className: "text-muted-foreground", label: t("pending"), bgClass: "bg-muted/50 border-border" },
  };

  return (
    <div className="border border-border rounded-md bg-card">
      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
        <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase flex items-center gap-1.5">
          <Zap className="h-3.5 w-3.5 text-blue-500 fill-blue-500" /> {t("agentPipeline")}
        </h3>
        <span className="text-[10px] text-muted-foreground">{agents.filter(a => a.status === "done").length}/{agents.length} {t("complete")}</span>
      </div>
      <div className="p-3 space-y-2">
        {agents.map((agent, i) => {
          const config = statusConfig[agent.status];
          const Icon = config.icon;
          return (
            <div key={agent.name} className="flex items-start gap-3">
              <div className="flex flex-col items-center pt-0.5">
                <div className={`h-6 w-6 rounded-md border flex items-center justify-center ${config.bgClass}`}>
                  <Icon className={`h-3.5 w-3.5 ${config.className}`} />
                </div>
                {i < agents.length - 1 && (
                  <div className="w-px h-4 bg-border mt-1" />
                )}
              </div>
              <div className="min-w-0 pt-0.5">
                <div className="text-xs font-medium text-foreground leading-tight">{agent.name}</div>
                <div className="text-[11px] text-muted-foreground leading-tight mt-0.5 flex items-center gap-1.5">
                  {agent.description}
                  <span className={`font-medium ${
                    agent.status === "done" ? "text-success" :
                    agent.status === "running" ? "text-blue-500" :
                    agent.status === "failed" ? "text-destructive" : "text-muted-foreground"
                  }`}>
                    · {config.label}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
