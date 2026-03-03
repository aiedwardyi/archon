import { useState, useEffect } from "react";
import { PanelLeftClose, PanelLeftOpen, Loader2 } from "lucide-react";
import { CheckCircle2, XCircle, Download, RotateCcw, FileText, Blocks, Code2, Monitor, Smartphone } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchVersions } from "@/services/api";

interface Version {
  id: number;
  label: string;
  status: "completed" | "failed";
  description: string;
  time: string;
  filesChanged: number;
  prompt?: string;
  buildSummary?: string;
  filesGenerated?: number;
  qualityTier?: string | null;
  readinessScore?: number | null;
}

const StatusIcon = ({ status }: { status: "completed" | "failed" }) =>
  status === "completed" ? (
    <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
  ) : (
    <XCircle className="h-4 w-4 text-destructive flex-shrink-0" />
  );

interface VersionsViewProps {
  projectId: number | null;
  selectedVersion: number | null;
  onVersionSelect: (v: number) => void;
  onArtifactNavigate?: (tab: "brief" | "plan" | "code") => void;
}

export const VersionsView = ({ projectId, selectedVersion, onVersionSelect, onArtifactNavigate }: VersionsViewProps) => {
  const selected = selectedVersion;
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [collapsed, setCollapsed] = useState(false);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [isProjectBuilding, setIsProjectBuilding] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    if (!projectId) { setVersions([]); return; }
    let cancelled = false;
    setLoadingVersions(true);
    (async () => {
      try {
        const res = await fetch(`http://localhost:5000/api/execution-status?project_id=${projectId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('archon_token')}` }
        });
        const data = await res.json();
        if (!cancelled) setIsProjectBuilding(data.status === 'RUNNING');
      } catch {
        if (!cancelled) setIsProjectBuilding(false);
      }
      try {
        const raw = await fetchVersions(projectId);
        if (cancelled) return;
        const mapped: Version[] = raw.map((v) => {
          const lastUserMsg = v.prompt_history?.filter(m => m.role === "user").pop()?.content || "";
          const isSuccess = v.status === "success" || v.status === "completed";
          const fileCount = v.files_generated ?? 0;
          const imageCount = v.images_generated ?? 0;
          const parts: string[] = [];
          if (fileCount > 0) parts.push(`${fileCount} code file${fileCount !== 1 ? "s" : ""}`);
          if (imageCount > 0) parts.push(`${imageCount} image${imageCount !== 1 ? "s" : ""}`);
          return {
            id: v.version,
            label: "v" + v.version,
            status: isSuccess ? "completed" as const : "failed" as const,
            description: lastUserMsg.length > 40 ? lastUserMsg.slice(0, 40) + "…" : lastUserMsg,
            time: v.created_at ? new Date(v.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }) : "",
            filesChanged: fileCount,
            prompt: lastUserMsg,
            filesGenerated: fileCount,
            qualityTier: v.quality_tier ?? null,
            readinessScore: v.readiness_score ?? null,
            buildSummary: isSuccess
              ? parts.length > 0
                ? parts.join(" · ") + " generated"
                : "Pipeline completed successfully."
              : t("pipelineFailed"),
          };
        });
        mapped.sort((a, b) => b.id - a.id);
        setVersions(mapped);
        if (mapped.length > 0 && (selectedVersion === null || !mapped.find(m => m.id === selectedVersion))) {
          onVersionSelect(mapped[0].id);
        }
        setLoadingVersions(false);
      } catch {}
    })();
    return () => { cancelled = true; };
  }, [projectId]);

  const version = versions.find((v) => v.id === selected);

  if (!projectId) {
    return (
      <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
        <span className="text-sm text-muted-foreground">Select a project to view versions</span>
      </div>
    );
  }

  if (loadingVersions) {
    return (
      <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading versions...</span>
      </div>
    );
  }

  if (!version) {
    return (
      <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
        <span className="text-sm text-muted-foreground">No versions found</span>
      </div>
    );
  }

  return (
    <div
      className="border border-border rounded-md overflow-hidden bg-card flex"
      style={{ height: "calc(100vh - 80px)" }}
    >
      {/* Left: Version History Sidebar */}
      {!collapsed && (
      <div className="w-[360px] flex-shrink-0 border-r border-border overflow-y-auto">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider flex items-center gap-1.5 whitespace-nowrap">
            ⏱ {t("versionHistory")}
          </h2>
          <button
            onClick={() => setCollapsed(true)}
            className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-3 py-3">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-1.5 mb-1">{t("yesterday")}</div>
          <div className="space-y-1">
            {versions.map((v) => {
              const isActive = v.id === selected;
              return (
                <button
                  key={v.id}
                  onClick={() => onVersionSelect(v.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-md transition-colors ${
                    isActive ? "bg-primary/10 border border-primary/20" : "hover:bg-secondary/60"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-muted-foreground"
                    }`}>
                      {v.label}
                    </span>
                    {isProjectBuilding ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" /> : <StatusIcon status={v.status} />}
                    <span className="text-[10px] text-muted-foreground ml-auto">{v.time}</span>
                  </div>
                  <p className="text-xs text-foreground mt-1.5 truncate leading-tight">{v.description}</p>
                  <p className="text-[11px] text-muted-foreground mt-1">{v.filesChanged} {t("filesChanged")}</p>
                  {v.qualityTier === "high" && (
                    <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-400/40 shadow-[0_0_6px_rgba(59,130,246,0.4)]">High Quality</span>
                  )}
                  {v.qualityTier === "good" && (
                    <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-400/40">Good Quality</span>
                  )}
                  {v.qualityTier === "low" && (
                    <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-500 border border-red-400/40">Low Quality</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
      )}

      {/* Right: Version Detail */}
      <div className="flex-1 overflow-y-auto">
        {/* Header Bar */}
        <div className="px-5 py-3 border-b border-border bg-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            {collapsed && (
              <button
                onClick={() => setCollapsed(false)}
                className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5"
              >
                <PanelLeftOpen className="h-3.5 w-3.5" /> {t("showVersions")}
              </button>
            )}
            <span className="text-xs font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded">
              V{version.id}
            </span>
            <div className="flex items-center gap-1.5">
              {isProjectBuilding ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" /> : <StatusIcon status={version.status} />}
              {isProjectBuilding ? <span className="text-xs font-medium text-blue-500">Building</span> : <span className="text-xs font-medium text-foreground capitalize">{version.status === "completed" ? t("completed") : t("failed")}</span>}
            </div>
            <span className="text-xs text-muted-foreground">{t("yesterday")} at {version.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5">
              <Download className="h-3.5 w-3.5" /> {t("downloadReport")}
            </button>
            <button className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5">
              <RotateCcw className="h-3.5 w-3.5" /> {t("restoreToThisVersion")}
            </button>
          </div>
        </div>

        <div className="p-5 space-y-5">
          {/* Prompt Section */}
          <div className="border-l-2 border-primary pl-4">
            <div className="text-[10px] font-bold text-primary uppercase tracking-wider mb-1">
              {t("prompt")} {version.time}
            </div>
            <p className="text-sm text-foreground">{version.prompt}</p>
          </div>

          {/* What Was Built */}
          <div className="border-l-2 border-emerald-500 pl-4">
            <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">
              {t("whatWasBuilt")} {version.time}
            </div>
            <p className="text-sm text-foreground">{isProjectBuilding ? "Build in progress..." : version.buildSummary}</p>
          </div>

          {/* Artifacts Row */}
          <div className="grid grid-cols-3 gap-0 border border-border rounded-md overflow-hidden bg-card">
            {([
              { icon: FileText, title: t("brief"), subtitle: t("requirementsDoc"), tab: "brief" as const },
              { icon: Blocks, title: t("buildPlan"), subtitle: t("architecturePlan"), tab: "plan" as const },
              { icon: Code2, title: t("code"), subtitle: `${version.filesGenerated ?? 0} ${t("files")}`, tab: "code" as const },
            ]).map(({ icon: Icon, title, subtitle, tab }, i) => (
              <button
                key={title}
                onClick={() => onArtifactNavigate?.(tab)}
                className={`flex items-center gap-3 px-4 py-3.5 text-left hover:bg-secondary/40 transition-colors ${
                  i < 2 ? "border-r border-border" : ""
                }`}
              >
                <div className="h-9 w-9 rounded-md bg-secondary flex items-center justify-center flex-shrink-0">
                  <Icon className="h-4.5 w-4.5 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-foreground">{title}</div>
                  <div className="text-[11px] text-muted-foreground">{subtitle}</div>
                </div>
              </button>
            ))}
          </div>

          {/* Live Preview */}
          <div className="border border-border rounded-md bg-card overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">{t("livePreview")}</h3>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPreviewDevice("desktop")}
                  className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
                    previewDevice === "desktop" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Monitor className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setPreviewDevice("mobile")}
                  className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
                    previewDevice === "mobile" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Smartphone className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="bg-secondary/20" style={{ height: 500 }}>
              {previewDevice === "desktop" ? (
                <div className="w-full h-full bg-background border border-border rounded-lg overflow-hidden shadow-sm flex flex-col">
                  <div className="h-8 bg-secondary/60 border-b border-border flex items-center gap-1.5 px-3 flex-shrink-0">
                    <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
                    <div className="ml-3 h-4 w-48 bg-secondary rounded-sm" />
                  </div>
                  <iframe
                    src={`http://localhost:5000/api/preview/${projectId}/${selected}`}
                    className="w-full flex-1 border-0"
                  />
                </div>
              ) : (
                <div className="flex items-start justify-center h-full pt-4">
                  <div className="w-[280px] bg-background border-2 border-foreground/20 rounded-[2rem] overflow-hidden shadow-lg flex flex-col" style={{ height: 480 }}>
                    <div className="flex justify-center py-2 flex-shrink-0">
                      <div className="h-4 w-20 bg-foreground/10 rounded-full" />
                    </div>
                    <div className="mx-2 mb-2 rounded-xl overflow-hidden border border-border flex-1">
                      <iframe
                        src={`http://localhost:5000/api/preview/${projectId}/${selected}`}
                        className="w-full h-full border-0"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
