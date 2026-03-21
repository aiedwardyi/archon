import { useState, useEffect, useRef } from "react";
import { PanelLeftClose, PanelLeftOpen, Loader2 } from "lucide-react";
import { CheckCircle2, XCircle, Download, RotateCcw, FileText, Blocks, Code2, Monitor, Smartphone, RefreshCw } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchVersions } from "@/services/api";
import { DEMO_MODE } from "@/demo/demoMode";
import { getDemoFactsheetPdfUrl, getDemoPreviewUrl } from "@/demo/demoData";

interface PromptTurn {
  role: string;
  content: string;
}

interface Version {
  id: number;
  executionId: number;
  parentVersion?: number;
  label: string;
  status: "completed" | "failed";
  description: string;
  time: string;
  filesChanged: number;
  prompt?: string;
  promptHistory?: PromptTurn[];
  basePrompt?: string;
  latestRequest?: string;
  lineageSummary?: string;
  refinementCount?: number;
  buildSummary?: string;
  filesGenerated?: number;
  qualityTier?: string | null;
  readinessScore?: number | null;
}

const getUserTurns = (promptHistory?: PromptTurn[]): string[] =>
  (promptHistory || [])
    .filter((turn) => turn.role === "user")
    .map((turn) => turn.content.trim())
    .filter(Boolean);

const summarizeText = (value: string, maxLength = 56): string =>
  value.length > maxLength ? `${value.slice(0, maxLength - 1)}...` : value;

const buildLineageSummary = (turns: string[]): string => {
  if (turns.length <= 1) return summarizeText(turns[0] || "");
  const visibleTurns = turns.slice(-3).map((turn) => summarizeText(turn, 28));
  return visibleTurns.join(" -> ");
};

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
  const desktopPreviewHeight = "clamp(720px, 78vh, 1100px)";
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [collapsed, setCollapsed] = useState(false);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [isProjectBuilding, setIsProjectBuilding] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);
  const [restoring, setRestoring] = useState(false);
  const [restoreConfirmedExecutionId, setRestoreConfirmedExecutionId] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wasBuilding = useRef(false);
  const prevVersionCount = useRef(0);
  const restoreConfirmationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { t } = useLanguage();

  const handleRestore = async (executionId: number) => {
    if (DEMO_MODE) return;
    setRestoring(true);
    try {
      await fetch(`http://localhost:5000/api/executions/${executionId}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("archon_token")}` },
      });
      setRestoreConfirmedExecutionId(executionId);
      if (restoreConfirmationTimeoutRef.current) {
        clearTimeout(restoreConfirmationTimeoutRef.current);
      }
      restoreConfirmationTimeoutRef.current = setTimeout(() => {
        setRestoreConfirmedExecutionId(null);
      }, 2000);
      setIframeKey((k) => k + 1);
    } catch (e) {
      console.error("Restore failed:", e);
    } finally {
      setRestoring(false);
    }
  };

  const loadVersionData = async (projectId: number, cancelled: { value: boolean }) => {
    if (DEMO_MODE) {
      setIsProjectBuilding(false);
      const raw = await fetchVersions(projectId);
      if (cancelled.value) return;
      const parentVersionByExecutionId = new Map(raw.map((v) => [Number(v.id), v.version]));
      const mapped: Version[] = raw.map((v) => {
        const userTurns = getUserTurns(v.prompt_history);
        const basePrompt = userTurns[0] || "";
        const latestRequest = userTurns[userTurns.length - 1] || "";
        const lastUserMsg = latestRequest;
        const fileCount = v.files_generated ?? 0;
        const imageCount = v.images_generated ?? 0;
        const parts: string[] = [];
        if (fileCount > 0) parts.push(`${fileCount} code file${fileCount !== 1 ? "s" : ""}`);
        if (imageCount > 0) parts.push(`${imageCount} image${imageCount !== 1 ? "s" : ""}`);
        return {
          id: v.version,
          executionId: Number(v.id),
          parentVersion: v.parent_execution_id != null ? parentVersionByExecutionId.get(Number(v.parent_execution_id)) : undefined,
          label: "v" + v.version,
          status: "completed",
          description: lastUserMsg.length > 40 ? lastUserMsg.slice(0, 40) + "…" : lastUserMsg,
          time: v.created_at ? new Date(v.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }) : "",
          filesChanged: fileCount,
          prompt: lastUserMsg,
          promptHistory: v.prompt_history,
          basePrompt,
          latestRequest,
          lineageSummary: buildLineageSummary(userTurns),
          refinementCount: Math.max(userTurns.length - 1, 0),
          filesGenerated: fileCount,
          qualityTier: v.quality_tier ?? null,
          readinessScore: v.readiness_score ?? null,
          buildSummary: parts.length > 0 ? parts.join(" · ") + " generated" : "Pipeline completed successfully.",
        };
      });
      mapped.sort((a, b) => b.id - a.id);
      setVersions(mapped);
      if (mapped.length > 0 && (selectedVersion === null || !mapped.find((m) => m.id === selectedVersion))) {
        onVersionSelect(mapped[0].id);
      }
      prevVersionCount.current = mapped.length;
      setLoadingVersions(false);
      return;
    }
    try {
      const res = await fetch(`http://localhost:5000/api/execution-status?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('archon_token')}` }
      });
      const data = await res.json();
      if (cancelled.value) return;
      const building = data.status === 'RUNNING';
      setIsProjectBuilding(building);
      if (wasBuilding.current && !building) {
        setIframeKey(k => k + 1);
      }
      wasBuilding.current = building;
      if (!building && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {
      if (!cancelled.value) setIsProjectBuilding(false);
    }
    try {
      const raw = await fetchVersions(projectId);
      if (cancelled.value) return;
      const parentVersionByExecutionId = new Map(
        raw.map((v) => [Number(v.id), v.version])
      );
      const mapped: Version[] = raw.map((v) => {
        const userTurns = getUserTurns(v.prompt_history);
        const basePrompt = userTurns[0] || "";
        const latestRequest = userTurns[userTurns.length - 1] || "";
        const lastUserMsg = latestRequest;
        const normalizedStatus = String(v.status || "").toLowerCase();
        const isSuccess = normalizedStatus === "success" || normalizedStatus === "completed";
        const isRunning = normalizedStatus === "running" || normalizedStatus === "in_progress" || normalizedStatus === "pending";
        const fileCount = v.files_generated ?? 0;
        const imageCount = v.images_generated ?? 0;
        const parts: string[] = [];
        if (fileCount > 0) parts.push(`${fileCount} code file${fileCount !== 1 ? "s" : ""}`);
        if (imageCount > 0) parts.push(`${imageCount} image${imageCount !== 1 ? "s" : ""}`);
        return {
          id: v.version,
          executionId: Number(v.id),
          parentVersion: v.parent_execution_id != null ? parentVersionByExecutionId.get(Number(v.parent_execution_id)) : undefined,
          label: "v" + v.version,
          status: isSuccess || isRunning ? "completed" as const : "failed" as const,
          description: lastUserMsg.length > 40 ? lastUserMsg.slice(0, 40) + "…" : lastUserMsg,
          time: v.created_at ? new Date(v.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true }) : "",
          filesChanged: fileCount,
          prompt: lastUserMsg,
          promptHistory: v.prompt_history,
          basePrompt,
          latestRequest,
          lineageSummary: buildLineageSummary(userTurns),
          refinementCount: Math.max(userTurns.length - 1, 0),
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
      const hasNewBuild = mapped.length > prevVersionCount.current;
      if (mapped.length > 0 && (hasNewBuild || selectedVersion === null || !mapped.find(m => m.id === selectedVersion))) {
        onVersionSelect(mapped[0].id);
      }
      prevVersionCount.current = mapped.length;
      setLoadingVersions(false);
    } catch {}
  };

  useEffect(() => {
    if (!projectId) { setVersions([]); return; }
    const cancelled = { value: false };
    prevVersionCount.current = 0;
    setLoadingVersions(true);
    loadVersionData(projectId, cancelled);
    pollRef.current = setInterval(() => loadVersionData(projectId, cancelled), 3000);
    return () => {
      cancelled.value = true;
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      if (restoreConfirmationTimeoutRef.current) {
        clearTimeout(restoreConfirmationTimeoutRef.current);
        restoreConfirmationTimeoutRef.current = null;
      }
    };
  }, [projectId]);

  const version = versions.find((v) => v.id === selected);
  const latestVersionId = versions.length > 0 ? versions[0].id : null; // versions sorted descending
  const isBuildingSelected = isProjectBuilding && selected === latestVersionId;

  const handleDownloadReport = async () => {
    if (!projectId || !version) return;
    if (DEMO_MODE) {
      const url = getDemoFactsheetPdfUrl(projectId, "client");
      const a = document.createElement("a");
      a.href = url;
      a.download = `archon-v${version.id}-client.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      return;
    }
    try {
      const token = localStorage.getItem("archon_token");
      const res = await fetch(`http://localhost:5000/api/projects/${projectId}/versions/${version.id}/factsheet/pdf?type=client`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Failed to download report");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `archon-v${version.id}-client.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      alert("Report download failed");
    }
  };

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
            {versions.map((v, idx) => {
              const isActive = v.id === selected;
              const isLatestVersion = idx === 0; // versions sorted descending — idx 0 is newest
              const isBuildingThis = isProjectBuilding && isLatestVersion;
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
                    {isBuildingThis ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" /> : <StatusIcon status={v.status} />}
                    <span className="text-[10px] text-muted-foreground ml-auto">{v.time}</span>
                  </div>
                  <p className="text-xs text-foreground mt-1.5 truncate leading-tight">{v.description}</p>
                  {v.refinementCount ? (
                    <p className="text-[11px] text-muted-foreground mt-1 leading-tight line-clamp-2">
                      {v.lineageSummary}
                    </p>
                  ) : null}
                  <p className="text-[11px] text-muted-foreground mt-1">{v.filesChanged} {t("filesChanged")}</p>
                  {typeof v.refinementCount === "number" && v.refinementCount > 0 && (
                    <p className="text-[11px] text-muted-foreground mt-1">{t("refinementCount")}: {v.refinementCount}</p>
                  )}
                  {typeof v.parentVersion === "number" && v.parentVersion < v.id - 1 && (
                    <p className="text-[11px] text-muted-foreground mt-1">↩ branched from v{v.parentVersion}</p>
                  )}
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
              {isBuildingSelected ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" /> : <StatusIcon status={version.status} />}
              {isBuildingSelected ? <span className="text-xs font-medium text-blue-500">Building</span> : <span className="text-xs font-medium text-foreground capitalize">{version.status === "completed" ? t("completed") : t("failed")}</span>}
            </div>
            <span className="text-xs text-muted-foreground">{t("yesterday")} at {version.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadReport}
              className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> {t("downloadReport")}
            </button>
            <button
              onClick={() => setIframeKey((k) => k + 1)}
              className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" /> {t("refreshPreview")}
            </button>
            {!DEMO_MODE && version && latestVersionId !== null && version.id !== latestVersionId && (
              <button
                onClick={() => handleRestore(version.executionId)}
                disabled={restoring}
                title="Future builds will continue from this version"
                className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                {restoring ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="h-3.5 w-3.5" />} {restoreConfirmedExecutionId === version.executionId ? "Set ✓" : "Set as iteration base"}
              </button>
            )}
          </div>
        </div>

        <div className="p-5 space-y-5">
          {/* Prompt Lineage */}
          <div className="border-l-2 border-primary pl-4">
            <div className="text-[10px] font-bold text-primary uppercase tracking-wider mb-1">
              {t("promptLineage")} {version.time}
            </div>
            <div className="space-y-2">
              <div>
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">{t("basePrompt")}</div>
                <p className="text-sm text-foreground">{version.basePrompt || version.prompt}</p>
              </div>
              {version.refinementCount ? (
                <div>
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">{t("latestRequest")}</div>
                    <span className="text-[11px] text-muted-foreground">{t("refinementCount")}: {version.refinementCount}</span>
                  </div>
                  <p className="text-sm text-foreground">{version.latestRequest}</p>
                </div>
              ) : null}
              {version.refinementCount ? (
                <p className="text-xs text-muted-foreground">{version.lineageSummary}</p>
              ) : null}
            </div>
          </div>

          {/* What Was Built */}
          <div className="border-l-2 border-emerald-500 pl-4">
            <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">
              {t("whatWasBuilt")} {version.time}
            </div>
            <p className="text-sm text-foreground">{isBuildingSelected ? "Build in progress..." : version.buildSummary}</p>
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

            <div className="bg-secondary/20" style={{ height: desktopPreviewHeight }}>
              {previewDevice === "desktop" ? (
                <div className="w-full h-full bg-background border border-border rounded-lg overflow-hidden shadow-sm flex flex-col">
                  <div className="h-8 bg-secondary/60 border-b border-border flex items-center gap-1.5 px-3 flex-shrink-0">
                    <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
                    <div className="ml-3 h-4 w-48 bg-secondary rounded-sm" />
                  </div>
                  <iframe
                    src={DEMO_MODE ? getDemoPreviewUrl(projectId, selected) : `http://localhost:5000/api/preview/${projectId}/${selected}?k=${iframeKey}`}
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
                        src={DEMO_MODE ? getDemoPreviewUrl(projectId, selected) : `http://localhost:5000/api/preview/${projectId}/${selected}?k=${iframeKey}`}
                        className="w-full h-full border-0"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="px-4 py-2 border-t border-border bg-secondary/20 text-[11px] text-muted-foreground">
              {t("previewWarmupHint")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
